"""
MetaSectionAgent: LLM 기반 Section 타입 분류 Agent

🚨 제1 원칙 준수:
1. True Agentic AI: 모든 분류는 LLM 프롬프트로만 수행 (NO REGEX!)
2. 콘텐츠 기반: Section 번호가 아닌 콘텐츠 유형으로 분류
3. 범용 설계: 단일 Agent가 모든 Section 타입 분류

이 Agent는 Section Title과 Content Preview를 받아서
해당 Section의 타입 (incoming_ls, maintenance, release_work 등)을 분류합니다.
"""

import json
import logging
from typing import Any, Optional

from ..models.section_types import (
    Release,
    SectionClassification,
    SectionType,
    Technology,
)
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MetaSectionAgent(BaseAgent):
    """
    LLM 기반 Section 타입 분류 Agent

    🚨 True Agentic AI 원칙:
    - Section Title만으로 regex 매칭 금지
    - LLM이 콘텐츠 기반으로 타입 결정
    - 하드코딩된 규칙 사용 금지
    """

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.agent_name = "MetaSectionAgent"

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        LangGraph state를 받아 Section 분류 수행

        Args:
            state: {
                "section_title": str,  # Section 제목
                "content_preview": str,  # 콘텐츠 미리보기 (첫 500자)
            }

        Returns:
            state + {"classification": SectionClassification}
        """
        section_title = state.get("section_title", "")
        content_preview = state.get("content_preview", "")

        self.log_start(f"Classifying section: {section_title[:50]}...")

        classification = self.classify(section_title, content_preview)

        self.log_end(
            f"Classified as: {classification.section_type} "
            f"(confidence: {classification.confidence:.2f})"
        )

        return {**state, "classification": classification}

    def classify(
        self, section_title: str, content_preview: str
    ) -> SectionClassification:
        """
        Section 타입 분류 (LLM 전용)

        🚨 NO REGEX: 모든 분류는 LLM이 수행

        Args:
            section_title: Section 제목
            content_preview: 콘텐츠 미리보기 (첫 500자)

        Returns:
            SectionClassification
        """
        import time

        prompt = self._build_classification_prompt(section_title, content_preview)
        max_retries = 5  # 재시도 횟수 증가
        base_delay = 2  # 지수 백오프 시작 (2초)
        last_error = None

        for attempt in range(max_retries):
            try:
                # 지수 백오프 계산
                delay = base_delay * (2 ** attempt)  # 2, 4, 8, 16, 32초

                response = self.llm.generate(prompt, temperature=0.1, max_tokens=1024)

                # 빈 응답 체크 - retry 필요
                if not response or not response.strip():
                    logger.warning(
                        f"[{self.agent_name}] Empty response on attempt {attempt + 1}/{max_retries}, "
                        f"retrying after {delay}s..."
                    )
                    if attempt < max_retries - 1:
                        time.sleep(delay)  # 지수 백오프 적용
                        continue
                    else:
                        logger.error(f"[{self.agent_name}] All retries exhausted with empty responses")
                        # 폴백: 제목 기반 휴리스틱 (LLM 실패 시 안전한 기본값)
                        return self._fallback_classification(section_title)

                result = self._parse_classification_response(response)

                # 파싱 성공 시 반환
                if result.confidence > 0.0:
                    return result

                # confidence가 0인 경우 (파싱 실패) - retry
                if attempt < max_retries - 1:
                    logger.warning(
                        f"[{self.agent_name}] Parse failed on attempt {attempt + 1}/{max_retries}, "
                        f"retrying after {delay}s..."
                    )
                    time.sleep(delay)
                    continue

            except Exception as e:
                last_error = e
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"[{self.agent_name}] Attempt {attempt + 1}/{max_retries} failed: {e}, "
                    f"retrying after {delay}s..."
                )
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue

        # 모든 재시도 실패 - 폴백 사용
        logger.error(
            f"[{self.agent_name}] Classification failed after {max_retries} attempts. "
            f"Last error: {last_error}. Using fallback classification."
        )
        return self._fallback_classification(section_title)

    def _fallback_classification(self, section_title: str) -> SectionClassification:
        """
        LLM 실패 시 안전한 폴백 분류

        🚨 Note: 이것은 True Agentic AI 원칙의 예외적 폴백입니다.
        LLM이 완전히 실패한 경우에만 사용됩니다.
        """
        title_lower = section_title.lower()

        # 명확한 키워드 기반 폴백 (최소한의 휴리스틱)
        if "liaison" in title_lower or "incoming ls" in title_lower:
            return SectionClassification(
                section_type=SectionType.INCOMING_LS,
                confidence=0.3,  # 낮은 신뢰도 표시
            )
        elif "maintenance" in title_lower:
            # Release/Technology 정보는 LLM 없이 판단 불가
            release = None
            technology = None
            if "rel-18" in title_lower or "release 18" in title_lower:
                release = Release.REL_18
            elif "pre-rel" in title_lower:
                release = Release.PRE_REL_18
            if "nr" in title_lower and "eutra" not in title_lower:
                technology = Technology.NR
            elif "eutra" in title_lower or "e-utra" in title_lower:
                technology = Technology.E_UTRA
            return SectionClassification(
                section_type=SectionType.MAINTENANCE,
                release=release,
                technology=technology,
                confidence=0.3,
            )
        elif "opening" in title_lower or "closing" in title_lower or "approval" in title_lower:
            return SectionClassification(
                section_type=SectionType.ADMINISTRATIVE,
                confidence=0.3,
            )
        elif "annex" in title_lower:
            return SectionClassification(
                section_type=SectionType.ANNEX,
                confidence=0.3,
            )
        else:
            return SectionClassification(
                section_type=SectionType.OTHER,
                confidence=0.0,
            )

    def _build_classification_prompt(
        self, section_title: str, content_preview: str
    ) -> str:
        """
        분류 프롬프트 생성

        Note: 프롬프트가 모든 분류 로직을 담당 (True Agentic AI)

        🚨 Token Efficiency:
        - content_preview를 250자로 제한 (MAX_TOKENS 이슈 방지)
        - 프롬프트 간결화
        - 탭/특수문자 정리 (테이블 구조 문제 방지)
        """
        # 콘텐츠 미리보기 정리 및 크기 제한
        preview_text = ""
        if content_preview:
            # 탭을 공백으로, 연속 공백/줄바꿈 정리
            import re
            cleaned = content_preview.replace("\t", " ")
            cleaned = re.sub(r"\s+", " ", cleaned)
            preview_text = cleaned[:250].strip()

        return f"""Classify this 3GPP meeting section.

Title: {section_title}
Preview: {preview_text}

Section Types:
- incoming_ls: Incoming Liaison Statements (LS from other WGs)
- maintenance: CR/maintenance for releases (has release & technology info)
- release_work: New release work items (Rel-19, Rel-20)
- draft_ls: Outgoing LS drafts
- administrative: Opening, Closing, Agenda, Minutes approval
- annex: Attendee lists, annexes
- other: Cannot classify

For maintenance: determine release (Rel-18/Rel-19/Pre-Rel-18) and technology (NR/E-UTRA/common).

Return ONLY JSON:
{{"section_type":"...", "release":"...|null", "technology":"...|null", "confidence":0.0-1.0}}"""

    def _parse_classification_response(self, response: str) -> SectionClassification:
        """
        LLM 응답 파싱

        Args:
            response: LLM 응답 문자열

        Returns:
            SectionClassification
        """
        success, data, error = self.validate_json_response(response)

        if not success:
            logger.warning(
                f"[{self.agent_name}] JSON parse failed: {error}. Response: {response[:200]}"
            )
            return SectionClassification(
                section_type=SectionType.OTHER,
                confidence=0.0,
            )

        # section_type 파싱
        section_type_str = data.get("section_type", "other")
        try:
            section_type = SectionType(section_type_str)
        except ValueError:
            logger.warning(
                f"[{self.agent_name}] Unknown section_type: {section_type_str}"
            )
            section_type = SectionType.OTHER

        # release 파싱 (optional)
        release = None
        release_str = data.get("release")
        if release_str and release_str != "null":
            try:
                release = Release(release_str)
            except ValueError:
                logger.warning(f"[{self.agent_name}] Unknown release: {release_str}")

        # technology 파싱 (optional)
        technology = None
        tech_str = data.get("technology")
        if tech_str and tech_str != "null":
            try:
                technology = Technology(tech_str)
            except ValueError:
                logger.warning(f"[{self.agent_name}] Unknown technology: {tech_str}")

        # confidence
        confidence = float(data.get("confidence", 0.5))

        return SectionClassification(
            section_type=section_type,
            release=release,
            technology=technology,
            confidence=confidence,
        )

    def classify_batch(
        self, sections: list[dict[str, str]]
    ) -> list[SectionClassification]:
        """
        여러 Section 일괄 분류

        Args:
            sections: [{"title": str, "preview": str}, ...]

        Returns:
            [SectionClassification, ...]
        """
        results = []
        for section in sections:
            classification = self.classify(
                section.get("title", ""), section.get("preview", "")
            )
            results.append(classification)
        return results

    def should_process(self, classification: SectionClassification) -> bool:
        """
        이 Section을 처리해야 하는지 결정

        Args:
            classification: Section 분류 결과

        Returns:
            True if should process, False otherwise
        """
        # 처리 대상 Section 타입
        processable_types = {
            SectionType.INCOMING_LS,
            SectionType.MAINTENANCE,
            SectionType.RELEASE_WORK,
            SectionType.DRAFT_LS,
        }

        return (
            classification.section_type in processable_types
            and classification.confidence >= 0.5
        )

    def get_workflow_name(self, classification: SectionClassification) -> str:
        """
        Section 타입에 맞는 워크플로우 이름 반환

        Args:
            classification: Section 분류 결과

        Returns:
            워크플로우 이름 (예: "incoming_ls_workflow", "maintenance_workflow")
        """
        workflow_mapping = {
            SectionType.INCOMING_LS: "incoming_ls_workflow",
            SectionType.MAINTENANCE: "maintenance_workflow",
            SectionType.RELEASE_WORK: "release_work_workflow",
            SectionType.DRAFT_LS: "draft_ls_workflow",
        }

        return workflow_mapping.get(classification.section_type, "unknown_workflow")
