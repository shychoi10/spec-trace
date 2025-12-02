"""
ClassificationValidator: Issue Type 분류 검증

검증 항목:
1. Issue Type 분류 정확성 (Actionable vs Non-action)
2. 분류 근거 일관성
3. Decision과 Issue Type 일치 여부

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


class ClassificationValidator(BaseValidator):
    """Issue Type 분류 검증기"""

    # 유효한 Issue Types
    VALID_ISSUE_TYPES = [
        "Actionable Issue",
        "Non-action Issue",
    ]

    # Decision 키워드 (LLM 프롬프트에서 참조용)
    ACTIONABLE_KEYWORDS = [
        "LS reply",
        "revision",
        "CR",
        "way forward",
        "update",
        "respond",
        "draft",
    ]

    NON_ACTION_KEYWORDS = [
        "noted",
        "no action",
        "for information",
        "FYI",
        "already handled",
    ]

    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        Issue Type 분류 검증 (LLM 기반)

        Args:
            data: Issue dict 또는 Issues 리스트
            context: 추가 컨텍스트

        Returns:
            ValidationResult
        """
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

        # 분류 정보 수집
        classifications = []
        for idx, issue in enumerate(issues):
            if not isinstance(issue, dict):
                continue

            classifications.append({
                "index": idx + 1,
                "ls_id": issue.get("ls_id", ""),
                "issue_type": issue.get("issue_type", ""),
                "decision": issue.get("decision_text", "")[:200],
                "has_tdocs": bool(issue.get("related_tdocs")),
            })

        validation_prompt = f"""Validate Issue Type classifications for these LS items.

**Classifications to Validate:**
{classifications}

**Classification Rules:**
1. "Actionable Issue": RAN1 needs to take action (LS reply, CR, revision, way forward)
   - Decision mentions: {self.ACTIONABLE_KEYWORDS}
   - Should have related Tdocs

2. "Non-action Issue": RAN1 just notes/acknowledges
   - Decision mentions: {self.NON_ACTION_KEYWORDS}
   - Should NOT have Tdocs (or Tdocs = "없음")

**Validation Tasks:**
1. Check if issue_type matches the decision text
2. Check if Tdocs presence matches the issue_type
3. Identify any misclassifications

**Output (JSON):**
{{
  "correct_classifications": [1, 2, 5],
  "incorrect_classifications": [
    {{
      "index": 3,
      "current_type": "Actionable Issue",
      "correct_type": "Non-action Issue",
      "reason": "Decision says 'noted' with no further action"
    }}
  ],
  "accuracy_score": 0.0-1.0
}}

Generate validation:"""

        try:
            result = self._call_llm_for_validation(validation_prompt)

            errors = []
            for wrong in result.get("incorrect_classifications", []):
                errors.append(
                    ValidationError(
                        error_type="wrong_classification",
                        description=f"Issue {wrong.get('index')}: {wrong.get('current_type')} should be {wrong.get('correct_type')} - {wrong.get('reason')}",
                        location=f"Issue {wrong.get('index')}",
                        suggested_fix=f"Change issue_type to '{wrong.get('correct_type')}'",
                    )
                )

            accuracy = result.get("accuracy_score", 0.0)
            correct_count = len(result.get("correct_classifications", []))

            return ValidationResult(
                status=ValidationStatus.PASS if accuracy >= 1.0 else ValidationStatus.FAIL,
                accuracy=accuracy,
                errors=errors,
                notes=[f"Correct: {correct_count}/{len(issues)} classifications"],
            )

        except Exception as e:
            logger.error(f"[ClassificationValidator] Validation failed: {e}")
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
        분류 오류 상세 식별

        Args:
            data: issues 리스트
            validation_result: 초기 검증 결과

        Returns:
            상세 오류 목록
        """
        return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        분류 자동 수정

        Args:
            data: issues 리스트
            errors: 수정할 오류 목록

        Returns:
            (수정된 리스트, 성공 여부)
        """
        issues = data if isinstance(data, list) else [data]

        # 분류 오류만 필터
        classification_errors = [
            e for e in errors if e.error_type == "wrong_classification"
        ]

        if not classification_errors:
            return data, False

        corrected_issues = list(issues)
        made_changes = False

        for error in classification_errors:
            # location에서 Issue index 추출
            location = error.location or ""
            if "Issue" in location:
                try:
                    idx = int(location.split("Issue")[1].strip()) - 1
                    if 0 <= idx < len(corrected_issues):
                        # suggested_fix에서 새 타입 추출
                        fix = error.suggested_fix or ""
                        if "Actionable Issue" in fix:
                            corrected_issues[idx]["issue_type"] = "Actionable Issue"
                            made_changes = True
                        elif "Non-action Issue" in fix:
                            corrected_issues[idx]["issue_type"] = "Non-action Issue"
                            made_changes = True
                except (ValueError, IndexError):
                    continue

        return corrected_issues, made_changes
