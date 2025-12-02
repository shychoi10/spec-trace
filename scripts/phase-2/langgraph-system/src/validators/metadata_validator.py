"""
MetadataValidator: Issue 메타데이터 완전성 검증

검증 항목:
1. 필수 필드 완전성 (LS ID, Source WG, Title)
2. 필드 형식 유효성
3. 메타데이터 일관성

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


class MetadataValidator(BaseValidator):
    """Issue 메타데이터 검증기"""

    # 필수 필드 정의
    REQUIRED_FIELDS = [
        "ls_id",
        "title",
        "source_wg",
        "decision_text",
        "issue_type",
    ]

    OPTIONAL_FIELDS = [
        "agenda_item",
        "summary_korean",
        "related_tdocs",
    ]

    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        메타데이터 완전성 검증 (LLM 기반)

        Args:
            data: Issue dict 또는 Issues 리스트
            context: 추가 컨텍스트

        Returns:
            ValidationResult
        """
        # 단일 Issue 또는 리스트 처리
        issues = data if isinstance(data, list) else [data]
        context = context or {}

        if not issues:
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="no_data",
                        description="No issues to validate",
                    )
                ],
            )

        all_errors = []
        field_scores = []

        for idx, issue in enumerate(issues):
            if not isinstance(issue, dict):
                all_errors.append(
                    ValidationError(
                        error_type="invalid_format",
                        description=f"Issue {idx+1} is not a dictionary",
                    )
                )
                continue

            # 필수 필드 체크
            for field in self.REQUIRED_FIELDS:
                value = issue.get(field)
                if not value or (isinstance(value, str) and not value.strip()):
                    all_errors.append(
                        ValidationError(
                            error_type="missing_field",
                            description=f"Issue {idx+1} missing required field: {field}",
                            location=f"Issue {idx+1}",
                            suggested_fix=f"Extract {field} from source text",
                        )
                    )
                else:
                    field_scores.append(1.0)

        # LLM 검증: 필드 값 품질
        if issues and isinstance(issues[0], dict):
            quality_result = self._validate_field_quality(issues)
            all_errors.extend(quality_result.get("errors", []))
            field_scores.append(quality_result.get("quality_score", 0.5))

        # 정확도 계산
        if field_scores:
            accuracy = sum(field_scores) / (len(field_scores) + len(all_errors))
        else:
            accuracy = 0.0

        return ValidationResult(
            status=ValidationStatus.PASS if accuracy >= 1.0 else ValidationStatus.FAIL,
            accuracy=accuracy,
            errors=all_errors,
            notes=[f"Validated {len(issues)} issues"],
        )

    def _validate_field_quality(self, issues: list[dict]) -> dict:
        """
        LLM으로 필드 값 품질 검증

        Args:
            issues: Issue 리스트

        Returns:
            {"quality_score": float, "errors": list}
        """
        # 샘플 Issue 준비 (최대 5개)
        sample_issues = issues[:5]
        sample_data = []

        for idx, issue in enumerate(sample_issues):
            sample_data.append({
                "index": idx + 1,
                "ls_id": issue.get("ls_id", ""),
                "title": issue.get("title", "")[:100],
                "source_wg": issue.get("source_wg", ""),
                "issue_type": issue.get("issue_type", ""),
                "decision": issue.get("decision_text", "")[:100],
            })

        prompt = f"""Validate the quality of these Issue metadata fields.

**Sample Issues (first {len(sample_issues)} of {len(issues)}):**
{sample_data}

**Validation Rules:**
1. ls_id: Should match R1-XXXXXXX pattern (7 digits after R1-)
2. title: Should be descriptive, not just "LS on" or empty
3. source_wg: Should be valid 3GPP WG (e.g., RAN2, SA2, CT1)
4. issue_type: Should be "Actionable Issue" or "Non-action Issue"
5. decision: Should describe RAN1's action/response

**Output (JSON):**
{{
  "quality_score": 0.0-1.0,
  "field_issues": [
    {{
      "issue_index": 1,
      "field": "ls_id",
      "problem": "Invalid format",
      "current_value": "...",
      "suggested_fix": "..."
    }}
  ]
}}

Generate quality assessment:"""

        try:
            result = self._call_llm_for_validation(prompt)

            errors = []
            for issue in result.get("field_issues", []):
                errors.append(
                    ValidationError(
                        error_type="field_quality",
                        description=f"Issue {issue.get('issue_index')}: {issue.get('field')} - {issue.get('problem')}",
                        location=f"Issue {issue.get('issue_index')}, field: {issue.get('field')}",
                        suggested_fix=issue.get("suggested_fix"),
                    )
                )

            return {
                "quality_score": result.get("quality_score", 0.5),
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"[MetadataValidator] Quality validation failed: {e}")
            return {"quality_score": 0.5, "errors": []}

    def identify_errors(
        self, data: Any, validation_result: ValidationResult
    ) -> list[ValidationError]:
        """
        메타데이터 오류 상세 식별

        Args:
            data: issues 리스트
            validation_result: 초기 검증 결과

        Returns:
            상세 오류 목록
        """
        # 이미 충분히 상세한 오류가 있음
        return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        메타데이터 자동 수정

        Args:
            data: issues 리스트
            errors: 수정할 오류 목록

        Returns:
            (수정된 리스트, 성공 여부)
        """
        issues = data if isinstance(data, list) else [data]

        # 수정 가능한 오류 분류
        fixable_errors = [
            e for e in errors
            if e.error_type in ("field_quality", "missing_field")
            and e.location
        ]

        if not fixable_errors:
            return data, False

        # LLM으로 수정 시도
        correction_prompt = f"""Fix these metadata issues in the Issue list.

**Current Issues (summary):**
{[{"idx": i+1, "ls_id": iss.get("ls_id", ""), "fields": list(iss.keys())} for i, iss in enumerate(issues[:10])]}

**Errors to Fix:**
{[{"location": e.location, "description": e.description, "fix": e.suggested_fix} for e in fixable_errors]}

**Instructions:**
For each error, provide the corrected value.
If you cannot determine the correct value, use "UNKNOWN".

**Output (JSON):**
{{
  "corrections": [
    {{
      "issue_index": 1,
      "field": "source_wg",
      "corrected_value": "RAN2"
    }}
  ],
  "unfixable": ["description of what couldn't be fixed"]
}}

Generate corrections:"""

        try:
            result = self._call_llm_for_validation(correction_prompt)
            corrections = result.get("corrections", [])

            if not corrections:
                return data, False

            # 수정 적용
            corrected_issues = list(issues)
            made_changes = False

            for corr in corrections:
                idx = corr.get("issue_index", 0) - 1
                field = corr.get("field", "")
                value = corr.get("corrected_value", "")

                if 0 <= idx < len(corrected_issues) and field and value != "UNKNOWN":
                    corrected_issues[idx][field] = value
                    made_changes = True
                    logger.info(f"[MetadataValidator] Fixed Issue {idx+1}.{field} = {value}")

            return corrected_issues, made_changes

        except Exception as e:
            logger.error(f"[MetadataValidator] Auto-correction failed: {e}")
            return data, False
