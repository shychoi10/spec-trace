"""
FinalValidator: 최종 검증 (Layer 2)

100% 정확도를 목표로 하는 최종 검증기
원본 DOCX와 생성된 출력을 비교하여 완전성 검증

검증 항목:
1. Issue 수 일치
2. 모든 LS ID 포함 여부
3. 메타데이터 완전성
4. 콘텐츠 품질

True Agentic AI: 모든 검증은 LLM이 수행
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path
import logging

from .base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationError,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class FinalValidationReport:
    """최종 검증 리포트"""

    meeting_id: str
    overall_accuracy: float
    issue_count_match: bool
    original_count: int
    generated_count: int
    missing_items: list[str] = field(default_factory=list)
    extra_items: list[str] = field(default_factory=list)
    field_completeness: float = 0.0
    content_quality: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    status: ValidationStatus = ValidationStatus.FAIL

    def to_markdown(self) -> str:
        """Markdown 리포트 생성"""
        status_emoji = {
            ValidationStatus.PASS: "✅",
            ValidationStatus.FAIL: "❌",
            ValidationStatus.CORRECTED: "🔧",
            ValidationStatus.MANUAL_REVIEW: "⚠️",
        }

        lines = [
            f"# Validation Report: {self.meeting_id}",
            "",
            "## Summary",
            f"- **Overall Accuracy**: {self.overall_accuracy:.1%}",
            f"- **Status**: {status_emoji.get(self.status, '?')} {self.status.value.upper()}",
            "",
            "## Issue Count Comparison",
            f"- **Original DOCX**: {self.original_count} LS items",
            f"- **Generated Output**: {self.generated_count} issues",
            f"- **Match**: {'✅ Yes' if self.issue_count_match else '❌ No'}",
            "",
        ]

        if self.missing_items:
            lines.append("## Missing Items")
            for item in self.missing_items:
                lines.append(f"- {item}")
            lines.append("")

        if self.extra_items:
            lines.append("## Extra Items (possibly duplicates)")
            for item in self.extra_items:
                lines.append(f"- {item}")
            lines.append("")

        lines.extend([
            "## Quality Scores",
            f"- **Field Completeness**: {self.field_completeness:.0%}",
            f"- **Content Quality**: {self.content_quality:.0%}",
            "",
        ])

        if self.recommendations:
            lines.append("## Recommendations")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)


class FinalValidator(BaseValidator):
    """
    최종 검증기 (Layer 2)

    원본 DOCX와 생성된 출력을 비교하여 100% 정확도 달성 여부 확인
    """

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.meeting_id = ""

    def validate(
        self,
        data: Any,
        context: Optional[dict] = None
    ) -> ValidationResult:
        """
        최종 검증 수행

        Args:
            data: 생성된 출력 (dict with issues, cc_only_items, markdown_output)
            context: {
                "section_text": 원본 섹션 텍스트,
                "meeting_id": 미팅 ID,
                "docx_path": 원본 DOCX 경로
            }

        Returns:
            ValidationResult
        """
        context = context or {}
        section_text = context.get("section_text", "")
        self.meeting_id = context.get("meeting_id", "unknown")

        if not isinstance(data, dict):
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="invalid_data",
                        description="Expected dict with issues and cc_only_items",
                    )
                ],
            )

        issues = data.get("issues", [])
        cc_only = data.get("cc_only_items", [])

        # Step 1: 원본에서 LS 항목 수 추출 (LLM)
        original_count, original_ls_ids = self._count_original_items(section_text)

        # Step 2: 생성된 출력에서 LS 항목 추출
        generated_count = len(issues) + len(cc_only)
        generated_ls_ids = self._extract_generated_ls_ids(issues, cc_only)

        # Step 3: 비교
        missing = set(original_ls_ids) - set(generated_ls_ids)
        extra = set(generated_ls_ids) - set(original_ls_ids)

        # Step 4: 필드 완전성 검사
        field_completeness = self._check_field_completeness(issues)

        # Step 5: 콘텐츠 품질 검사
        content_quality = self._check_content_quality(issues)

        # 정확도 계산
        count_match = original_count == generated_count
        id_match_rate = 1.0 - (len(missing) / max(len(original_ls_ids), 1))

        overall_accuracy = (
            (1.0 if count_match else 0.7) * 0.3
            + id_match_rate * 0.3
            + field_completeness * 0.2
            + content_quality * 0.2
        )

        # 100% 달성 여부
        is_perfect = (
            count_match
            and len(missing) == 0
            and len(extra) == 0
            and field_completeness >= 1.0
            and content_quality >= 0.95
        )

        # 오류 생성
        errors = []
        if not count_match:
            errors.append(
                ValidationError(
                    error_type="count_mismatch",
                    description=f"Count mismatch: original={original_count}, generated={generated_count}",
                    suggested_fix="Re-extract missing items",
                )
            )

        for ls_id in missing:
            errors.append(
                ValidationError(
                    error_type="missing_item",
                    description=f"Missing LS item: {ls_id}",
                    suggested_fix="Extract this item from source",
                )
            )

        for ls_id in extra:
            errors.append(
                ValidationError(
                    error_type="extra_item",
                    description=f"Extra item (possibly duplicate): {ls_id}",
                    suggested_fix="Verify if duplicate and remove",
                    severity="warning",
                )
            )

        # 리포트 생성
        report = FinalValidationReport(
            meeting_id=self.meeting_id,
            overall_accuracy=overall_accuracy,
            issue_count_match=count_match,
            original_count=original_count,
            generated_count=generated_count,
            missing_items=list(missing),
            extra_items=list(extra),
            field_completeness=field_completeness,
            content_quality=content_quality,
            status=ValidationStatus.PASS if is_perfect else ValidationStatus.FAIL,
        )

        # 권장사항 생성
        if not is_perfect:
            report.recommendations = self._generate_recommendations(
                count_match, missing, extra, field_completeness, content_quality
            )

        return ValidationResult(
            status=ValidationStatus.PASS if is_perfect else ValidationStatus.FAIL,
            accuracy=overall_accuracy,
            errors=errors,
            notes=[report.to_markdown()],
            validator_name=self.validator_name,
        )

    def _count_original_items(self, section_text: str) -> tuple[int, list[str]]:
        """
        원본 섹션에서 LS 항목 수 추출 (LLM)

        Args:
            section_text: 원본 섹션 텍스트

        Returns:
            (총 항목 수, LS ID 리스트)
        """
        if not section_text:
            return 0, []

        prompt = f"""Count all Liaison Statement items in this section.

**Section Text:**
{section_text[:6000]}

**Instructions:**
1. Count every distinct LS item (both primary and CC-only)
2. Extract all LS IDs (format: R1-XXXXXXX)
3. Include both addressed-to-RAN1 and cc-to-RAN1 items

**Output (JSON):**
{{
  "total_count": number,
  "ls_ids": ["R1-2401234", "R1-2401235", ...],
  "primary_count": number,
  "cc_only_count": number
}}

Generate count:"""

        try:
            result = self._call_llm_for_validation(prompt)
            total = result.get("total_count", 0)
            ls_ids = result.get("ls_ids", [])
            return total, ls_ids

        except Exception as e:
            logger.error(f"[FinalValidator] Failed to count original items: {e}")
            return 0, []

    def _extract_generated_ls_ids(
        self, issues: list, cc_only: list
    ) -> list[str]:
        """
        생성된 출력에서 LS ID 추출

        Args:
            issues: Primary issues 리스트
            cc_only: CC-only items 리스트

        Returns:
            LS ID 리스트
        """
        ls_ids = []

        for issue in issues:
            if isinstance(issue, dict):
                ls_id = issue.get("ls_id", "")
            elif hasattr(issue, "ls_id"):
                ls_id = issue.ls_id
            else:
                continue

            if ls_id:
                ls_ids.append(ls_id)

        for item in cc_only:
            if isinstance(item, dict):
                ls_id = item.get("ls_id", "")
            elif hasattr(item, "ls_id"):
                ls_id = item.ls_id
            else:
                continue

            if ls_id:
                ls_ids.append(ls_id)

        return ls_ids

    def _check_field_completeness(self, issues: list) -> float:
        """
        필드 완전성 검사

        Args:
            issues: Issue 리스트

        Returns:
            완전성 점수 (0.0-1.0)
        """
        if not issues:
            return 0.0

        required_fields = ["ls_id", "title", "source_wg", "decision_text", "issue_type"]
        total_fields = len(issues) * len(required_fields)
        present_fields = 0

        for issue in issues:
            if isinstance(issue, dict):
                for field in required_fields:
                    if issue.get(field):
                        present_fields += 1
            elif hasattr(issue, "__dict__"):
                for field in required_fields:
                    if getattr(issue, field, None):
                        present_fields += 1

        return present_fields / total_fields if total_fields > 0 else 0.0

    def _check_content_quality(self, issues: list) -> float:
        """
        콘텐츠 품질 검사 (샘플 기반 LLM 검증)

        Args:
            issues: Issue 리스트

        Returns:
            품질 점수 (0.0-1.0)
        """
        if not issues:
            return 0.0

        # 샘플 추출 (최대 3개)
        sample_issues = issues[:3]

        sample_data = []
        for issue in sample_issues:
            if isinstance(issue, dict):
                sample_data.append({
                    "ls_id": issue.get("ls_id", ""),
                    "title": issue.get("title", "")[:100],
                    "summary": issue.get("summary_korean", "")[:200],
                    "decision": issue.get("decision_text", "")[:150],
                    "issue_type": issue.get("issue_type", ""),
                })

        prompt = f"""Evaluate the content quality of these processed Issues.

**Sample Issues:**
{sample_data}

**Quality Criteria:**
1. Coherence: Do fields make sense together?
2. Accuracy: Does the content appear factually accurate?
3. Completeness: Is essential information captured?
4. Professional: Is the language professional and clear?

**Output (JSON):**
{{
  "quality_score": 0.0-1.0,
  "issues_found": ["issue 1", ...]
}}

Generate evaluation:"""

        try:
            result = self._call_llm_for_validation(prompt)
            return result.get("quality_score", 0.5)

        except Exception as e:
            logger.error(f"[FinalValidator] Content quality check failed: {e}")
            return 0.5

    def _generate_recommendations(
        self,
        count_match: bool,
        missing: set,
        extra: set,
        field_completeness: float,
        content_quality: float,
    ) -> list[str]:
        """
        개선 권장사항 생성

        Args:
            count_match: 수 일치 여부
            missing: 누락된 LS IDs
            extra: 추가된 LS IDs
            field_completeness: 필드 완전성
            content_quality: 콘텐츠 품질

        Returns:
            권장사항 리스트
        """
        recommendations = []

        if not count_match:
            recommendations.append(
                "Re-run boundary detection to ensure all LS items are captured"
            )

        if missing:
            recommendations.append(
                f"Focus on extracting these missing items: {', '.join(list(missing)[:5])}"
            )

        if extra:
            recommendations.append(
                "Review for duplicate extractions and merge if necessary"
            )

        if field_completeness < 1.0:
            recommendations.append(
                "Improve metadata extraction for missing required fields"
            )

        if content_quality < 0.95:
            recommendations.append(
                "Enhance summary generation for better content quality"
            )

        return recommendations

    def identify_errors(
        self, data: Any, validation_result: ValidationResult
    ) -> list[ValidationError]:
        """
        오류 상세 식별 (이미 validate에서 수행)

        Args:
            data: 생성된 출력
            validation_result: 초기 검증 결과

        Returns:
            오류 목록
        """
        return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        자동 수정 (제한적)

        Note: FinalValidator는 전체 파이프라인 재실행이 필요할 수 있어
        자동 수정이 제한적입니다.

        Args:
            data: 생성된 출력
            errors: 수정할 오류 목록

        Returns:
            (수정된 데이터, 성공 여부)
        """
        if not isinstance(data, dict):
            return data, False

        issues = data.get("issues", [])
        cc_only = data.get("cc_only_items", [])

        # 중복 제거만 시도
        extra_errors = [e for e in errors if e.error_type == "extra_item"]

        if not extra_errors:
            return data, False

        # LS ID 중복 제거
        seen_ids = set()
        deduplicated_issues = []

        for issue in issues:
            ls_id = issue.get("ls_id") if isinstance(issue, dict) else getattr(issue, "ls_id", "")
            if ls_id not in seen_ids:
                seen_ids.add(ls_id)
                deduplicated_issues.append(issue)

        deduplicated_cc = []
        for item in cc_only:
            ls_id = item.get("ls_id") if isinstance(item, dict) else getattr(item, "ls_id", "")
            if ls_id not in seen_ids:
                seen_ids.add(ls_id)
                deduplicated_cc.append(item)

        made_changes = len(deduplicated_issues) != len(issues) or len(deduplicated_cc) != len(cc_only)

        if made_changes:
            data["issues"] = deduplicated_issues
            data["cc_only_items"] = deduplicated_cc
            return data, True

        return data, False

    def generate_final_report(
        self, result: ValidationResult, output_dir: Optional[Path] = None
    ) -> str:
        """
        최종 검증 리포트 생성 및 저장

        Args:
            result: ValidationResult
            output_dir: 저장 디렉토리

        Returns:
            리포트 경로 또는 Markdown 문자열
        """
        # notes에 리포트가 포함되어 있음
        if result.notes:
            report_md = result.notes[0]
        else:
            report_md = self.generate_report(result)

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            report_path = output_dir / f"{self.meeting_id}_validation_report.md"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_md)

            logger.info(f"[FinalValidator] Report saved: {report_path}")
            return str(report_path)

        return report_md
