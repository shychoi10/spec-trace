"""
BaseValidator: 모든 Validator의 추상 기반 클래스

True Agentic AI 원칙 준수:
- 모든 검증 로직은 LLM이 수행
- Regex, 하드코딩된 규칙 사용 금지
- 100% 정확도 목표, 자동 수정 루프 포함

검증 플로우:
Validate → [100% 미만] → Identify Errors → Auto-Correct → Re-validate
                ↓
         [최대 3회 반복]
                ↓
         [여전히 실패] → Manual Review Flag + 상세 오류 리포트
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """검증 상태"""
    PASS = "pass"           # 100% 통과
    FAIL = "fail"           # 검증 실패 (오류 발견)
    CORRECTED = "corrected" # 자동 수정됨
    MANUAL_REVIEW = "manual_review"  # 수동 검토 필요


@dataclass
class ValidationError:
    """개별 검증 오류"""
    error_type: str
    description: str
    location: Optional[str] = None
    suggested_fix: Optional[str] = None
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """검증 결과"""
    status: ValidationStatus
    accuracy: float  # 0.0 - 1.0
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    corrected_output: Optional[Any] = None
    validation_time_ms: float = 0.0
    retry_count: int = 0
    validator_name: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def is_perfect(self) -> bool:
        """100% 정확도인지 확인"""
        return self.accuracy >= 1.0 and len(self.errors) == 0

    def to_dict(self) -> dict:
        """JSON 직렬화를 위한 dict 변환"""
        return {
            "status": self.status.value,
            "accuracy": self.accuracy,
            "errors": [
                {
                    "error_type": e.error_type,
                    "description": e.description,
                    "location": e.location,
                    "suggested_fix": e.suggested_fix,
                    "severity": e.severity,
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "validation_time_ms": self.validation_time_ms,
            "retry_count": self.retry_count,
            "validator_name": self.validator_name,
            "notes": self.notes,
        }


class BaseValidator(ABC):
    """
    모든 Validator의 기반 추상 클래스

    100% 정확도 목표의 검증 루프:
    1. validate(): 초기 검증
    2. identify_errors(): 오류 식별 (LLM)
    3. auto_correct(): 자동 수정 시도 (LLM)
    4. re-validate: 수정 후 재검증
    5. 최대 3회 반복, 실패 시 manual_review 플래그
    """

    # 설정
    MAX_CORRECTION_ATTEMPTS = 3
    TARGET_ACCURACY = 1.0  # 100%

    def __init__(self, llm_manager, config: Optional[dict] = None):
        """
        Args:
            llm_manager: LLM 호출 매니저
            config: 검증기 설정
        """
        self.llm = llm_manager
        self.validator_name = self.__class__.__name__
        self.config = config or {}
        self.validation_history: list[ValidationResult] = []

    @abstractmethod
    def validate(self, data: Any, context: Optional[dict] = None) -> ValidationResult:
        """
        핵심 검증 로직 (LLM 사용)

        Args:
            data: 검증할 데이터
            context: 추가 컨텍스트 (원본 문서 등)

        Returns:
            ValidationResult
        """
        pass

    @abstractmethod
    def identify_errors(
        self, data: Any, validation_result: ValidationResult
    ) -> list[ValidationError]:
        """
        오류 상세 식별 (LLM 사용)

        Args:
            data: 검증 대상 데이터
            validation_result: 초기 검증 결과

        Returns:
            식별된 오류 목록
        """
        pass

    @abstractmethod
    def auto_correct(
        self, data: Any, errors: list[ValidationError]
    ) -> tuple[Any, bool]:
        """
        자동 수정 시도 (LLM 사용)

        Args:
            data: 원본 데이터
            errors: 수정할 오류 목록

        Returns:
            (수정된 데이터, 수정 성공 여부)
        """
        pass

    def validate_with_correction_loop(
        self, data: Any, context: Optional[dict] = None
    ) -> ValidationResult:
        """
        100% 정확도 달성을 위한 자동 수정 루프

        플로우:
        1. 초기 검증
        2. 100% 미달 시 오류 식별
        3. 자동 수정 시도
        4. 재검증
        5. 최대 3회 반복
        6. 실패 시 manual_review 플래그

        Args:
            data: 검증할 데이터
            context: 추가 컨텍스트

        Returns:
            최종 ValidationResult
        """
        start_time = datetime.now()
        current_data = data
        attempt = 0

        while attempt < self.MAX_CORRECTION_ATTEMPTS:
            # 1. 검증 실행
            result = self.validate(current_data, context)
            result.retry_count = attempt
            result.validator_name = self.validator_name

            logger.info(
                f"[{self.validator_name}] Attempt {attempt + 1}: "
                f"Accuracy={result.accuracy:.2%}, Errors={len(result.errors)}"
            )

            # 2. 100% 달성 시 성공
            if result.is_perfect:
                result.status = ValidationStatus.PASS
                result.validation_time_ms = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                self.validation_history.append(result)
                logger.info(f"[{self.validator_name}] ✅ Validation passed (100%)")
                return result

            # 3. 오류 식별
            errors = self.identify_errors(current_data, result)
            if not errors:
                # 오류를 식별할 수 없으면 현재 결과 반환
                logger.warning(
                    f"[{self.validator_name}] Could not identify errors, "
                    f"returning current result"
                )
                break

            # 4. 자동 수정 시도
            corrected_data, correction_success = self.auto_correct(current_data, errors)

            if not correction_success:
                logger.warning(
                    f"[{self.validator_name}] Auto-correction failed at attempt {attempt + 1}"
                )
                break

            # 5. 다음 iteration을 위해 데이터 업데이트
            current_data = corrected_data
            attempt += 1

            logger.info(
                f"[{self.validator_name}] Applied corrections, retrying validation..."
            )

        # 최대 시도 후에도 실패 → Manual Review 필요
        final_result = self.validate(current_data, context)
        final_result.status = ValidationStatus.MANUAL_REVIEW
        final_result.retry_count = attempt
        final_result.validator_name = self.validator_name
        final_result.validation_time_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000
        final_result.notes.append(
            f"Manual review required after {attempt} correction attempts"
        )

        if current_data != data:
            final_result.corrected_output = current_data
            final_result.status = ValidationStatus.CORRECTED

        self.validation_history.append(final_result)
        logger.warning(
            f"[{self.validator_name}] ⚠️ Validation incomplete. "
            f"Accuracy={final_result.accuracy:.2%}, Status={final_result.status.value}"
        )

        return final_result

    # =========================================================================
    # LLM Helper Methods
    # =========================================================================

    def _call_llm_for_validation(
        self, prompt: str, temperature: float = 0.1
    ) -> dict:
        """
        검증용 LLM 호출 (JSON 응답 기대)

        Args:
            prompt: 검증 프롬프트
            temperature: LLM temperature (검증은 낮은 값 권장)

        Returns:
            파싱된 JSON dict
        """
        try:
            response = self.llm.generate(prompt, temperature=temperature, max_tokens=2000)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"[{self.validator_name}] LLM call failed: {e}")
            return {}

    def _parse_json_response(self, response: str) -> dict:
        """
        LLM 응답에서 JSON 추출

        Args:
            response: LLM 응답 문자열

        Returns:
            파싱된 dict (실패 시 빈 dict)
        """
        try:
            # JSON 블록 추출
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                # 전체가 JSON일 수 있음
                json_str = response.strip()

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.validator_name}] JSON parse error: {e}")
            return {}
        except Exception as e:
            logger.warning(f"[{self.validator_name}] Unexpected parse error: {e}")
            return {}

    # =========================================================================
    # Reporting Methods
    # =========================================================================

    def generate_report(self, result: ValidationResult) -> str:
        """
        검증 결과 리포트 생성 (Markdown)

        Args:
            result: 검증 결과

        Returns:
            Markdown 형식 리포트
        """
        status_emoji = {
            ValidationStatus.PASS: "✅",
            ValidationStatus.FAIL: "❌",
            ValidationStatus.CORRECTED: "🔧",
            ValidationStatus.MANUAL_REVIEW: "⚠️",
        }

        lines = [
            f"## {self.validator_name} Validation Report",
            "",
            f"**Status**: {status_emoji.get(result.status, '?')} {result.status.value.upper()}",
            f"**Accuracy**: {result.accuracy:.1%}",
            f"**Retry Count**: {result.retry_count}",
            f"**Time**: {result.validation_time_ms:.1f}ms",
            "",
        ]

        if result.errors:
            lines.append("### Errors Found")
            for i, error in enumerate(result.errors, 1):
                lines.append(f"{i}. **{error.error_type}**: {error.description}")
                if error.location:
                    lines.append(f"   - Location: {error.location}")
                if error.suggested_fix:
                    lines.append(f"   - Suggested fix: {error.suggested_fix}")
            lines.append("")

        if result.warnings:
            lines.append("### Warnings")
            for warning in result.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        if result.notes:
            lines.append("### Notes")
            for note in result.notes:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)
