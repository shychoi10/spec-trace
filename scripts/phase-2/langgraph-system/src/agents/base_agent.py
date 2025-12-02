"""
BaseAgent: 모든 Agent의 추상 기반 클래스

모든 Agent는 이 클래스를 상속받아 process() 메서드를 구현해야 합니다.
EVRIRL 사이클 (Execute → Validate → Reflect → Improve → Re-execute → Learn) 지원
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Agent 실행 결과"""

    success: bool
    output: Any
    confidence_score: float = 0.0
    validation_notes: list[str] = field(default_factory=list)
    retry_count: int = 0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None


@dataclass
class ReflectionResult:
    """Reflection 결과"""

    missed_info: list[str] = field(default_factory=list)
    wrong_assumptions: list[str] = field(default_factory=list)
    needed_context: list[str] = field(default_factory=list)
    improved_approach: str = ""


class BaseAgent(ABC):
    """모든 Agent의 기반이 되는 추상 클래스"""

    # EVRIRL 설정
    MAX_RETRIES = 3
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, llm_manager, config: Optional[dict] = None):
        """
        Args:
            llm_manager: LLM 호출을 담당하는 매니저 객체
            config: Agent 설정 (domain_hints 등)
        """
        self.llm = llm_manager
        self.agent_name = self.__class__.__name__
        self.config = config or {}

        # 실행 기록
        self.execution_history: list[AgentResult] = []
        self.learned_patterns: list[dict] = []

    @abstractmethod
    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Agent의 핵심 처리 로직

        Args:
            state: LangGraph state dictionary
                - content: 처리할 텍스트 내용
                - metadata: 메타데이터 (meeting_number 등)

        Returns:
            업데이트된 state dictionary
                - structured_output: 구조화된 결과
                - agent_used: 사용된 agent 이름
        """
        pass

    def detect_pattern(self, content: str) -> float:
        """
        이 Agent가 처리해야 하는 패턴인지 점수 반환

        Args:
            content: 분석할 텍스트

        Returns:
            0.0-1.0 사이의 신뢰도 점수
            높을수록 이 Agent가 적합함
        """
        return 0.0

    # =========================================================================
    # EVRIRL Cycle Methods
    # =========================================================================

    def execute_with_evrirl(
        self, task_fn: callable, input_data: Any, validation_fn: callable
    ) -> AgentResult:
        """
        EVRIRL 사이클로 작업 실행

        Args:
            task_fn: 실행할 함수 (input_data -> output)
            input_data: 입력 데이터
            validation_fn: 검증 함수 (output -> confidence_score, notes)

        Returns:
            최종 AgentResult
        """
        retry_count = 0
        reflection: Optional[ReflectionResult] = None

        while retry_count < self.MAX_RETRIES:
            start_time = datetime.now()

            # 1. Execute
            try:
                if reflection and reflection.improved_approach:
                    # 개선된 접근법으로 실행
                    output = task_fn(input_data, improved_context=reflection)
                else:
                    output = task_fn(input_data)
            except Exception as e:
                logger.error(f"[{self.agent_name}] Execution failed: {e}")
                return AgentResult(
                    success=False,
                    output=None,
                    error_message=str(e),
                    retry_count=retry_count,
                )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # 2. Validate
            confidence_score, validation_notes = validation_fn(output)

            # 성공 조건 확인
            if confidence_score >= self.CONFIDENCE_THRESHOLD:
                result = AgentResult(
                    success=True,
                    output=output,
                    confidence_score=confidence_score,
                    validation_notes=validation_notes,
                    retry_count=retry_count,
                    execution_time_ms=execution_time,
                )

                # 6. Learn (성공 시)
                self._learn_from_success(input_data, output, confidence_score)

                self.execution_history.append(result)
                return result

            # 3. Reflect
            reflection = self._reflect(
                input_data, output, confidence_score, validation_notes
            )
            logger.info(
                f"[{self.agent_name}] Reflection (retry {retry_count}): {reflection.improved_approach[:100]}..."
            )

            # 4. Improve (다음 iteration에서 사용)
            retry_count += 1

            if retry_count >= self.MAX_RETRIES:
                logger.warning(
                    f"[{self.agent_name}] Max retries reached. Returning best effort result."
                )
                result = AgentResult(
                    success=True,  # partial success
                    output=output,
                    confidence_score=confidence_score,
                    validation_notes=validation_notes + ["Max retries reached"],
                    retry_count=retry_count,
                    execution_time_ms=execution_time,
                )
                self.execution_history.append(result)
                return result

        # Should not reach here
        return AgentResult(success=False, output=None, error_message="Unexpected error")

    def _reflect(
        self,
        input_data: Any,
        output: Any,
        confidence_score: float,
        validation_notes: list[str],
    ) -> ReflectionResult:
        """
        실패 원인 분석 (LLM 사용)

        Args:
            input_data: 입력 데이터
            output: 현재 출력
            confidence_score: 현재 신뢰도
            validation_notes: 검증 노트

        Returns:
            ReflectionResult
        """
        reflection_prompt = f"""You just completed a task but the confidence is low ({confidence_score:.2f}).

Validation notes: {validation_notes}

Reflect on:
1. What information did you miss?
2. What assumption was wrong?
3. What additional context would help?
4. How should you approach this differently?

Return your reflection as JSON:
{{
  "missed_info": ["..."],
  "wrong_assumptions": ["..."],
  "needed_context": ["..."],
  "improved_approach": "..."
}}"""

        try:
            response = self.llm.generate(
                reflection_prompt, temperature=0.3, max_tokens=500
            )
            reflection_data = json.loads(response)
            return ReflectionResult(**reflection_data)
        except Exception as e:
            logger.warning(f"[{self.agent_name}] Reflection LLM call failed: {e}")
            return ReflectionResult(
                improved_approach="Try with more context and broader search"
            )

    def _learn_from_success(
        self, input_data: Any, output: Any, confidence_score: float
    ) -> None:
        """
        성공적인 처리에서 패턴 학습

        Args:
            input_data: 입력 데이터
            output: 성공한 출력
            confidence_score: 신뢰도
        """
        if confidence_score < 0.85:
            return  # 높은 신뢰도에서만 학습

        pattern = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "confidence": confidence_score,
            "input_summary": str(input_data)[:100],
            "output_summary": str(output)[:100],
            "validated": False,
        }

        self.learned_patterns.append(pattern)
        logger.debug(f"[{self.agent_name}] Learned new pattern (confidence: {confidence_score:.2f})")

    # =========================================================================
    # Validation Helper Methods
    # =========================================================================

    def validate_required_fields(
        self, data: dict, required_fields: list[str]
    ) -> tuple[float, list[str]]:
        """
        필수 필드 존재 여부 검증

        Args:
            data: 검증할 데이터
            required_fields: 필수 필드 목록

        Returns:
            (confidence_score, validation_notes)
        """
        notes = []
        present_count = 0

        for field in required_fields:
            if field in data and data[field]:
                present_count += 1
            else:
                notes.append(f"Missing required field: {field}")

        score = present_count / len(required_fields) if required_fields else 1.0
        return score, notes

    def validate_json_response(self, response: str) -> tuple[bool, Any, str]:
        """
        LLM 응답의 JSON 유효성 검증

        Args:
            response: LLM 응답 문자열

        Returns:
            (success, parsed_data, error_message)
        """
        try:
            # JSON 블록 추출 시도
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            parsed = json.loads(json_str)
            return True, parsed, ""
        except json.JSONDecodeError as e:
            return False, None, f"JSON parse error: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"

    # =========================================================================
    # Logging Methods
    # =========================================================================

    def log_start(self, operation: str) -> None:
        """작업 시작 로그"""
        logger.info(f"[{self.agent_name}] Starting: {operation}")

    def log_end(self, operation: str, success: bool = True) -> None:
        """작업 종료 로그"""
        status = "✅" if success else "❌"
        logger.info(f"[{self.agent_name}] {status} Completed: {operation}")

    def log_progress(self, message: str) -> None:
        """진행 상황 로그"""
        logger.info(f"[{self.agent_name}] {message}")
