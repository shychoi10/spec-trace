"""
TdocValidator: Tdoc 추출 및 연결 검증

검증 항목:
1. Tdoc ID 형식 유효성 (R1-XXXXXXX)
2. Tdoc 태그 적절성 (discussion, ls_reply_draft 등)
3. Tdoc 누락 여부

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


class TdocValidator(BaseValidator):
    """Tdoc 추출 결과 검증기"""

    # 유효한 Tdoc 태그
    VALID_TAGS = [
        "discussion",
        "ls_reply_draft",
        "presentation",
        "cr",
        "way_forward",
        "summary",
        "other",
    ]

    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        Tdoc 추출 결과 검증 (LLM 기반)

        Args:
            data: Issue dict with "related_tdocs" 또는 Tdocs 리스트
            context: {"issue_text": ..., "issue_type": ...}

        Returns:
            ValidationResult
        """
        context = context or {}
        issue_type = context.get("issue_type", "")
        issue_text = context.get("issue_text", "")

        # Tdocs 추출
        if isinstance(data, dict):
            tdocs = data.get("related_tdocs", [])
        elif isinstance(data, list):
            tdocs = data
        else:
            tdocs = []

        # Non-action Issue는 Tdoc이 없어야 함
        if "Non-action" in issue_type:
            if tdocs and tdocs != ["없음"] and tdocs != []:
                return ValidationResult(
                    status=ValidationStatus.FAIL,
                    accuracy=0.8,
                    errors=[
                        ValidationError(
                            error_type="unexpected_tdocs",
                            description="Non-action Issue should not have Tdocs",
                            suggested_fix="Set related_tdocs to '없음'",
                        )
                    ],
                )
            return ValidationResult(
                status=ValidationStatus.PASS,
                accuracy=1.0,
                notes=["Non-action Issue correctly has no Tdocs"],
            )

        # Actionable Issue는 Tdoc이 있어야 함
        if not tdocs or tdocs == ["없음"] or tdocs == []:
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="missing_tdocs",
                        description="Actionable Issue should have related Tdocs",
                        suggested_fix="Extract Tdocs from issue text",
                    )
                ],
            )

        # LLM 검증: Tdoc 형식 및 태그
        validation_prompt = f"""Validate these Tdoc entries for an Actionable Issue.

**Tdocs to validate:**
{tdocs}

**Issue Context (first 500 chars):**
{issue_text[:500] if issue_text else "Not provided"}

**Validation Rules:**
1. Tdoc ID format: R1-XXXXXXX (7 digits)
2. Each Tdoc should have a tag: {self.VALID_TAGS}
3. Tags should match the Tdoc's purpose
4. Tdocs should be relevant to the issue

**Output (JSON):**
{{
  "valid_tdocs": ["R1-2401234 (discussion)", ...],
  "invalid_format": ["R1-123 - too short", ...],
  "missing_tags": ["R1-2401234 - no tag", ...],
  "wrong_tags": ["R1-2401234 - should be discussion not cr", ...],
  "accuracy_score": 0.0-1.0
}}

Generate validation:"""

        try:
            result = self._call_llm_for_validation(validation_prompt)

            errors = []

            for item in result.get("invalid_format", []):
                errors.append(
                    ValidationError(
                        error_type="invalid_tdoc_format",
                        description=item,
                        suggested_fix="Correct the Tdoc ID format",
                    )
                )

            for item in result.get("missing_tags", []):
                errors.append(
                    ValidationError(
                        error_type="missing_tag",
                        description=item,
                        suggested_fix="Add appropriate tag",
                        severity="warning",
                    )
                )

            for item in result.get("wrong_tags", []):
                errors.append(
                    ValidationError(
                        error_type="wrong_tag",
                        description=item,
                        suggested_fix="Update tag to match Tdoc purpose",
                    )
                )

            accuracy = result.get("accuracy_score", 0.5)
            valid_count = len(result.get("valid_tdocs", []))
            total_count = len(tdocs) if tdocs else 1

            # 유효한 Tdoc 비율 반영
            coverage = valid_count / total_count if total_count > 0 else 0

            return ValidationResult(
                status=ValidationStatus.PASS if accuracy >= 1.0 else ValidationStatus.FAIL,
                accuracy=min(accuracy, coverage),
                errors=errors,
                notes=[f"Valid: {valid_count}/{total_count} Tdocs"],
            )

        except Exception as e:
            logger.error(f"[TdocValidator] Validation failed: {e}")
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
        Tdoc 오류 상세 식별

        Args:
            data: Tdocs 데이터
            validation_result: 초기 검증 결과

        Returns:
            상세 오류 목록
        """
        return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        Tdoc 데이터 자동 수정

        Args:
            data: Issue dict 또는 Tdocs 리스트
            errors: 수정할 오류 목록

        Returns:
            (수정된 데이터, 성공 여부)
        """
        # Tdocs 추출
        is_dict = isinstance(data, dict)
        if is_dict:
            tdocs = data.get("related_tdocs", [])
        else:
            tdocs = data if isinstance(data, list) else []

        if not tdocs or not errors:
            return data, False

        # 수정 가능한 오류만 처리
        fixable = [
            e for e in errors
            if e.error_type in ("missing_tag", "wrong_tag", "invalid_tdoc_format")
        ]

        if not fixable:
            return data, False

        correction_prompt = f"""Fix these Tdoc entries.

**Current Tdocs:**
{tdocs}

**Errors to Fix:**
{[{"type": e.error_type, "desc": e.description, "fix": e.suggested_fix} for e in fixable]}

**Instructions:**
1. Fix Tdoc ID formats (should be R1-XXXXXXX with 7 digits)
2. Add/correct tags (valid: {self.VALID_TAGS})
3. Format: "R1-XXXXXXX (tag)"

**Output (JSON):**
{{
  "corrected_tdocs": ["R1-2401234 (discussion)", ...]
}}

Generate corrections:"""

        try:
            result = self._call_llm_for_validation(correction_prompt)
            corrected = result.get("corrected_tdocs", [])

            if not corrected:
                return data, False

            if is_dict:
                data["related_tdocs"] = corrected
                return data, True
            else:
                return corrected, True

        except Exception as e:
            logger.error(f"[TdocValidator] Auto-correction failed: {e}")
            return data, False
