"""
SummaryValidator: 요약 품질 검증

검증 항목:
1. 요약 품질 (정보 완전성)
2. 핵심 정보 포함 여부
3. 한국어 번역 품질

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


class SummaryValidator(BaseValidator):
    """요약 품질 검증기"""

    # 요약에 포함되어야 할 핵심 요소
    REQUIRED_ELEMENTS = [
        "main_topic",           # 주제
        "source_context",       # 출처/배경
        "key_points",           # 핵심 내용
        "ran1_relevance",       # RAN1 관련성
    ]

    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        요약 품질 검증 (LLM 기반)

        Args:
            data: Issue dict with "summary_korean" 또는 요약 문자열
            context: {"original_text": ..., "issue_type": ...}

        Returns:
            ValidationResult
        """
        context = context or {}
        original_text = context.get("original_text", "")

        # 요약 추출
        if isinstance(data, dict):
            summary = data.get("summary_korean", "")
        elif isinstance(data, str):
            summary = data
        else:
            summary = ""

        if not summary or len(summary) < 20:
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="empty_summary",
                        description="Summary is empty or too short",
                        suggested_fix="Generate summary from original text",
                    )
                ],
            )

        validation_prompt = f"""Validate this Korean summary for quality and completeness.

**Summary to Validate:**
{summary}

**Original Text (first 1500 chars):**
{original_text[:1500] if original_text else "Not provided"}

**Quality Criteria:**
1. **Accuracy**: Does summary correctly represent the original?
2. **Completeness**: Does it capture the main topic and key points?
3. **Conciseness**: Is it appropriately brief but informative?
4. **Korean Quality**: Is the Korean natural and readable?
5. **RAN1 Relevance**: Does it explain why this matters to RAN1?

**Required Elements:**
- main_topic: What is this about?
- source_context: Who sent this and why?
- key_points: What are the key technical points?
- ran1_relevance: What does RAN1 need to know/do?

**Output (JSON):**
{{
  "accuracy_score": 0.0-1.0,
  "completeness_score": 0.0-1.0,
  "conciseness_score": 0.0-1.0,
  "korean_quality_score": 0.0-1.0,
  "missing_elements": ["main_topic", ...],
  "factual_errors": ["error description", ...],
  "improvement_suggestions": ["suggestion 1", ...]
}}

Generate validation:"""

        try:
            result = self._call_llm_for_validation(validation_prompt)

            if not result:
                return ValidationResult(
                    status=ValidationStatus.FAIL,
                    accuracy=0.5,
                    warnings=["LLM validation returned empty result"],
                )

            # 점수 계산
            accuracy = result.get("accuracy_score", 0.0)
            completeness = result.get("completeness_score", 0.0)
            conciseness = result.get("conciseness_score", 0.0)
            korean_quality = result.get("korean_quality_score", 0.0)

            # 가중 평균
            overall_score = (
                accuracy * 0.35
                + completeness * 0.30
                + conciseness * 0.15
                + korean_quality * 0.20
            )

            # 오류 수집
            errors = []

            for element in result.get("missing_elements", []):
                errors.append(
                    ValidationError(
                        error_type="missing_element",
                        description=f"Summary missing: {element}",
                        suggested_fix=f"Add {element} to summary",
                    )
                )

            for error in result.get("factual_errors", []):
                errors.append(
                    ValidationError(
                        error_type="factual_error",
                        description=error,
                        suggested_fix="Correct the factual information",
                    )
                )

            return ValidationResult(
                status=ValidationStatus.PASS if overall_score >= 1.0 else ValidationStatus.FAIL,
                accuracy=overall_score,
                errors=errors,
                warnings=result.get("improvement_suggestions", []),
                notes=[
                    f"Accuracy: {accuracy:.0%}",
                    f"Completeness: {completeness:.0%}",
                    f"Korean: {korean_quality:.0%}",
                ],
            )

        except Exception as e:
            logger.error(f"[SummaryValidator] Validation failed: {e}")
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
        요약 오류 상세 식별

        Args:
            data: 요약 데이터
            validation_result: 초기 검증 결과

        Returns:
            상세 오류 목록
        """
        return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        요약 자동 수정 (재생성)

        Args:
            data: Issue dict 또는 요약 문자열
            errors: 수정할 오류 목록

        Returns:
            (수정된 데이터, 성공 여부)
        """
        # 요약 추출
        is_dict = isinstance(data, dict)
        if is_dict:
            summary = data.get("summary_korean", "")
            original = data.get("original_text", data.get("text", ""))
        else:
            summary = str(data)
            original = ""

        if not errors:
            return data, False

        # 개선 필요 사항 정리
        issues_to_fix = [e.description for e in errors]
        suggestions = [e.suggested_fix for e in errors if e.suggested_fix]

        correction_prompt = f"""Improve this Korean summary based on the feedback.

**Current Summary:**
{summary}

**Issues to Fix:**
{issues_to_fix}

**Suggestions:**
{suggestions}

**Original Context (if available):**
{original[:1000] if original else "Not available"}

**Instructions:**
1. Address all the issues listed above
2. Keep the summary concise (2-3 sentences)
3. Ensure natural Korean expression
4. Include: main topic, source context, key points, RAN1 relevance

**Output:** (Just the improved summary in Korean, no explanation)"""

        try:
            improved_summary = self.llm.generate(
                correction_prompt, temperature=0.3, max_tokens=500
            )

            if improved_summary and len(improved_summary) > 50:
                if is_dict:
                    data["summary_korean"] = improved_summary.strip()
                    return data, True
                else:
                    return improved_summary.strip(), True

            return data, False

        except Exception as e:
            logger.error(f"[SummaryValidator] Auto-correction failed: {e}")
            return data, False
