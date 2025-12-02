"""
ParseValidator: 문서 파싱 단계 검증

검증 항목:
1. Section 추출 완전성
2. 시작/끝 경계 정확성
3. 콘텐츠 무결성

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


class ParseValidator(BaseValidator):
    """문서 파싱 결과 검증기"""

    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        파싱 결과 검증 (LLM 기반)

        Args:
            data: 파싱된 section_text
            context: {"docx_path": ..., "full_document": ...}

        Returns:
            ValidationResult
        """
        section_text = data if isinstance(data, str) else str(data)
        context = context or {}

        # 기본 검증: 텍스트가 있는지
        if not section_text or len(section_text) < 100:
            return ValidationResult(
                status=ValidationStatus.FAIL,
                accuracy=0.0,
                errors=[
                    ValidationError(
                        error_type="empty_section",
                        description="Section text is empty or too short",
                        suggested_fix="Check document path and section extraction",
                    )
                ],
            )

        # LLM 검증: 섹션 완전성 확인
        validation_prompt = f"""You are a document parsing validator. Analyze this extracted "Incoming Liaison Statements" section.

**Extracted Section (first 2000 chars):**
{section_text[:2000]}

**Extracted Section (last 500 chars):**
{section_text[-500:] if len(section_text) > 500 else section_text}

**Total Length:** {len(section_text)} characters

**Validation Checklist:**
1. Does the section start with a proper heading (e.g., "5 Incoming liaison statements" or similar)?
2. Does it contain LS item patterns (e.g., "R1-XXXXXXX", "LS from/to", "Reply LS")?
3. Does the section appear complete (not truncated mid-sentence)?
4. Is there a clear boundary at the end (transition to next section or end of content)?
5. Are there obvious signs of corruption or encoding issues?

**Output (JSON):**
{{
  "completeness_score": 0.0-1.0,
  "has_proper_start": true/false,
  "has_proper_end": true/false,
  "contains_ls_patterns": true/false,
  "encoding_issues": true/false,
  "issues_found": ["issue 1", "issue 2"],
  "suggestions": ["fix 1", "fix 2"]
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

            # 점수 계산
            completeness = result.get("completeness_score", 0.0)
            has_start = result.get("has_proper_start", False)
            has_end = result.get("has_proper_end", False)
            has_ls = result.get("contains_ls_patterns", False)
            has_encoding = result.get("encoding_issues", False)

            # 가중 점수
            score = (
                completeness * 0.4
                + (1.0 if has_start else 0.0) * 0.2
                + (1.0 if has_end else 0.0) * 0.2
                + (1.0 if has_ls else 0.0) * 0.15
                + (0.0 if has_encoding else 1.0) * 0.05
            )

            # 오류 변환
            errors = []
            for issue in result.get("issues_found", []):
                suggestions = result.get("suggestions", [])
                errors.append(
                    ValidationError(
                        error_type="parse_issue",
                        description=issue,
                        suggested_fix=suggestions[0] if suggestions else None,
                    )
                )

            return ValidationResult(
                status=ValidationStatus.PASS if score >= 1.0 else ValidationStatus.FAIL,
                accuracy=score,
                errors=errors,
                warnings=result.get("suggestions", []),
            )

        except Exception as e:
            logger.error(f"[ParseValidator] Validation failed: {e}")
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
        파싱 오류 상세 식별

        Args:
            data: section_text
            validation_result: 초기 검증 결과

        Returns:
            상세 오류 목록
        """
        section_text = data if isinstance(data, str) else str(data)

        prompt = f"""Analyze this section extraction for specific errors.

**Current Issues Found:**
{[e.description for e in validation_result.errors]}

**Section Text (sample):**
{section_text[:1500]}

**Identify specific problems:**
1. Where exactly does the extraction fail?
2. What content might be missing?
3. Are there boundary detection errors?

**Output (JSON):**
{{
  "errors": [
    {{
      "type": "boundary_error|content_missing|truncation|encoding",
      "description": "specific description",
      "location": "start|middle|end|unknown",
      "fix": "how to fix this"
    }}
  ]
}}

Generate error analysis:"""

        try:
            result = self._call_llm_for_validation(prompt)
            errors = []

            for err in result.get("errors", []):
                errors.append(
                    ValidationError(
                        error_type=err.get("type", "unknown"),
                        description=err.get("description", ""),
                        location=err.get("location"),
                        suggested_fix=err.get("fix"),
                    )
                )

            return errors

        except Exception as e:
            logger.error(f"[ParseValidator] Error identification failed: {e}")
            return validation_result.errors

    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        파싱 결과 자동 수정

        Note: 파싱 단계는 원본 문서 재처리가 필요하므로
        자동 수정이 제한적입니다.

        Args:
            data: section_text
            errors: 수정할 오류 목록

        Returns:
            (수정된 텍스트, 성공 여부)
        """
        section_text = data if isinstance(data, str) else str(data)

        # 간단한 수정만 시도 (인코딩, 공백 정리 등)
        correction_prompt = f"""You need to fix this extracted section text.

**Original Text:**
{section_text[:3000]}

**Errors to Fix:**
{[{"type": e.error_type, "desc": e.description, "fix": e.suggested_fix} for e in errors]}

**Instructions:**
1. Fix encoding issues (if any)
2. Clean up obvious formatting problems
3. DO NOT add or remove content
4. Return the cleaned text as-is

If no fixes are possible, return "NO_FIX_POSSIBLE".

**Output:** (just the corrected text, no explanation)"""

        try:
            response = self.llm.generate(correction_prompt, temperature=0.0, max_tokens=4000)

            if "NO_FIX_POSSIBLE" in response:
                return data, False

            # 최소한의 변화가 있어야 성공으로 간주
            if response.strip() != section_text.strip():
                return response.strip(), True

            return data, False

        except Exception as e:
            logger.error(f"[ParseValidator] Auto-correction failed: {e}")
            return data, False
