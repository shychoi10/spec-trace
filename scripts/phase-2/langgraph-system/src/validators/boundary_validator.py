"""
BoundaryValidator: Issue 경계 감지 검증

검증 항목:
1. Issue 수 정확성
2. 누락된 LS 항목 체크
3. 경계 정확성 (Issue 시작/끝)

True Agentic AI: 모든 검증은 LLM이 수행
"""

from typing import Any, Optional
import logging

from .base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationError,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class BoundaryValidator(BaseValidator):
    """Issue 경계 감지 결과 검증기"""

    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        Issue 분할 결과 검증 (LLM 기반)

        Args:
            data: 분할된 Issues 리스트 (list[dict])
            context: {"section_text": ..., "expected_count": ...}

        Returns:
            ValidationResult
        """
        issues = data if isinstance(data, list) else []
        context = context or {}
        section_text = context.get("section_text", "")

        if not issues:
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="no_issues",
                        description="No issues were extracted",
                        suggested_fix="Re-run issue splitting with more context",
                    )
                ],
            )

        # Issue 요약 생성
        issue_summaries = []
        for i, issue in enumerate(issues):
            ls_id = issue.get("ls_id", "unknown")
            title = issue.get("title", "")[:50]
            is_primary = issue.get("is_primary", True)
            issue_summaries.append(f"{i+1}. [{ls_id}] {title}... (primary={is_primary})")

        validation_prompt = f"""You are an Issue boundary validator. Compare extracted issues against the source text.

**Source Section (first 3000 chars):**
{section_text[:3000]}

**Extracted Issues ({len(issues)} total):**
{chr(10).join(issue_summaries)}

**Validation Tasks:**
1. Count how many distinct LS items exist in the source text
2. Compare with extracted count ({len(issues)})
3. Check if any LS items are missing
4. Verify each issue has correct boundary (not merged with another)
5. Check for duplicate extractions

**Output (JSON):**
{{
  "source_count": number (your count from source text),
  "extracted_count": {len(issues)},
  "missing_ls_ids": ["R1-XXXXXXX", ...],
  "duplicate_ls_ids": ["R1-XXXXXXX", ...],
  "merged_issues": ["Issue N appears to contain multiple LS items"],
  "boundary_errors": ["Issue N has unclear boundary at end"],
  "accuracy_score": 0.0-1.0
}}

Generate validation result:"""

        try:
            result = self._call_llm_for_validation(validation_prompt)

            if not result:
                return ValidationResult(
                    status=ValidationStatus.FAIL,
                    accuracy=0.5,
                    warnings=["LLM validation returned empty result"],
                )

            # 결과 분석
            source_count = result.get("source_count", 0)
            extracted_count = result.get("extracted_count", len(issues))
            missing = result.get("missing_ls_ids", [])
            duplicates = result.get("duplicate_ls_ids", [])
            merged = result.get("merged_issues", [])
            boundary_errors = result.get("boundary_errors", [])

            # 오류 수집
            errors = []

            for ls_id in missing:
                errors.append(
                    ValidationError(
                        error_type="missing_issue",
                        description=f"Missing LS item: {ls_id}",
                        suggested_fix="Re-extract with focus on this LS ID",
                    )
                )

            for ls_id in duplicates:
                errors.append(
                    ValidationError(
                        error_type="duplicate_issue",
                        description=f"Duplicate extraction: {ls_id}",
                        suggested_fix="Remove duplicate entry",
                    )
                )

            for msg in merged:
                errors.append(
                    ValidationError(
                        error_type="merged_issues",
                        description=msg,
                        suggested_fix="Split merged issues",
                    )
                )

            for msg in boundary_errors:
                errors.append(
                    ValidationError(
                        error_type="boundary_error",
                        description=msg,
                        severity="warning",
                    )
                )

            # 정확도 계산
            accuracy = result.get("accuracy_score", 0.0)
            if source_count > 0:
                # 추출률 기반 정확도
                coverage = min(1.0, extracted_count / source_count)
                # 오류 페널티
                error_penalty = len(errors) * 0.05
                accuracy = max(0.0, coverage - error_penalty)

            return ValidationResult(
                status=ValidationStatus.PASS if accuracy >= 1.0 else ValidationStatus.FAIL,
                accuracy=accuracy,
                errors=errors,
                notes=[
                    f"Source count: {source_count}",
                    f"Extracted count: {extracted_count}",
                ],
            )

        except Exception as e:
            logger.error(f"[BoundaryValidator] Validation failed: {e}")
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="validation_error",
                        description=str(e),
                    )
                ],
            )

    def identify_errors(
        self, data: Any, validation_result: ValidationResult
    ) -> list[ValidationError]:
        """
        경계 오류 상세 식별

        Args:
            data: issues 리스트
            validation_result: 초기 검증 결과

        Returns:
            상세 오류 목록
        """
        issues = data if isinstance(data, list) else []

        # 기존 오류에서 missing_issue만 추출
        missing_errors = [
            e for e in validation_result.errors if e.error_type == "missing_issue"
        ]

        if not missing_errors:
            return validation_result.errors

        prompt = f"""Analyze why these LS items might be missing from the extraction.

**Extracted Issues:** {len(issues)}
**Missing LS IDs:** {[e.description for e in missing_errors]}

**Possible reasons:**
1. Issue was merged with another
2. Issue was in CC-only section but marked as primary
3. Issue boundary was incorrectly detected
4. Issue ID was not in standard format

**For each missing item, identify:**
{{
  "errors": [
    {{
      "ls_id": "R1-XXXXXXX",
      "reason": "why it was missed",
      "location_hint": "where it might be in the source",
      "fix": "how to recover it"
    }}
  ]
}}

Generate analysis:"""

        try:
            result = self._call_llm_for_validation(prompt)
            errors = []

            for err in result.get("errors", []):
                errors.append(
                    ValidationError(
                        error_type="missing_issue",
                        description=f"{err.get('ls_id')}: {err.get('reason')}",
                        location=err.get("location_hint"),
                        suggested_fix=err.get("fix"),
                    )
                )

            return errors if errors else validation_result.errors

        except Exception as e:
            logger.error(f"[BoundaryValidator] Error identification failed: {e}")
            return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        Issue 리스트 자동 수정

        Args:
            data: issues 리스트
            errors: 수정할 오류 목록

        Returns:
            (수정된 리스트, 성공 여부)
        """
        issues = data if isinstance(data, list) else []

        # 오류 유형별 분류
        missing = [e for e in errors if e.error_type == "missing_issue"]
        duplicates = [e for e in errors if e.error_type == "duplicate_issue"]

        corrected = list(issues)
        made_changes = False

        # 중복 제거
        if duplicates:
            seen_ls_ids = set()
            new_issues = []
            for issue in corrected:
                ls_id = issue.get("ls_id", "")
                if ls_id not in seen_ls_ids:
                    seen_ls_ids.add(ls_id)
                    new_issues.append(issue)
                else:
                    made_changes = True
            corrected = new_issues

        # Missing issues는 자동 수정 불가 (원본 텍스트 재처리 필요)
        if missing:
            logger.warning(
                f"[BoundaryValidator] {len(missing)} missing issues require re-extraction"
            )

        return corrected, made_changes
