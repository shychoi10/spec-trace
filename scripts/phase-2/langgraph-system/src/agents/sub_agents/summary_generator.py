"""
SummaryGenerator Sub-Agent

Issue 내용을 분석하여 한국어 요약을 생성합니다.

True Agentic AI: 모든 요약은 LLM이 수행
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class SummaryGenerator(BaseAgent):
    """한국어 요약 생성 Sub-Agent"""

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.summary_hints = self.config.get("incoming_ls_hints", {}).get(
            "summary_generation", {}
        )

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Issue 내용을 한국어로 요약

        Args:
            state: LangGraph state
                - issue_text: Issue 전체 텍스트
                - title: Issue 제목
                - decision: Decision 텍스트

        Returns:
            업데이트된 state
                - summary_ko: 한국어 요약
        """
        issue_text = state.get("issue_text", "")
        title = state.get("title", "")
        decision = state.get("decision", "")

        self.log_start("Korean summary generation")

        result = self._generate_summary(issue_text, title, decision)

        if result.success:
            state["summary_ko"] = result.output
            state["summary_confidence"] = result.confidence_score
            self.log_end("Korean summary generation", success=True)
        else:
            state["summary_ko"] = f"{title}에 대한 요약을 생성할 수 없습니다."
            state["summary_confidence"] = 0.0
            self.log_end("Korean summary generation", success=False)

        return state

    def _generate_summary(
        self, issue_text: str, title: str, decision: str
    ) -> AgentResult:
        """
        LLM을 사용하여 한국어 요약 생성

        Args:
            issue_text: Issue 전체 텍스트
            title: Issue 제목
            decision: Decision 텍스트

        Returns:
            AgentResult with Korean summary string
        """
        style_hints = self.summary_hints.get("style", {})
        length_guide = self.summary_hints.get("length", "2-4 sentences")

        prompt = f"""You are summarizing a 3GPP RAN1 Liaison Statement discussion for Korean readers.

**Style Guidelines:**
{json.dumps(style_hints, indent=2, ensure_ascii=False)}

**Length Guide:** {length_guide}

**Issue Title:**
{title}

**Decision:**
{decision}

**Full Issue Text:**
{issue_text[:3000]}  # Truncated if too long

**Instructions:**
1. Write a concise summary in **Korean**
2. Focus on:
   - What the LS is about (main topic)
   - What RAN1 decided or needs to do
   - Any important technical details
3. Use professional technical Korean
4. Keep it {length_guide}

Return your summary as JSON:
{{
  "summary_ko": "한국어 요약 텍스트",
  "key_points": ["핵심 포인트 1", "핵심 포인트 2"],
  "confidence": 0.0-1.0
}}
"""

        try:
            response = self.llm.generate(prompt, temperature=0.3, max_tokens=800)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"[SummaryGenerator] JSON parse failed: {error}")
                # 폴백: 제목 기반 기본 요약
                default_summary = self._create_fallback_summary(title, decision)
                return AgentResult(
                    success=True,
                    output=default_summary,
                    confidence_score=0.4,
                    validation_notes=[f"Parse failed, using fallback: {error}"],
                )

            summary_ko = parsed.get("summary_ko", "")
            confidence = parsed.get("confidence", 0.7)
            key_points = parsed.get("key_points", [])

            if not summary_ko:
                summary_ko = self._create_fallback_summary(title, decision)
                confidence = 0.3

            return AgentResult(
                success=True,
                output=summary_ko,
                confidence_score=confidence,
                validation_notes=key_points,
            )

        except Exception as e:
            logger.error(f"[SummaryGenerator] LLM call failed: {e}")
            fallback = self._create_fallback_summary(title, decision)
            return AgentResult(
                success=True,
                output=fallback,
                confidence_score=0.2,
                error_message=str(e),
            )

    def _create_fallback_summary(self, title: str, decision: str) -> str:
        """
        LLM 실패 시 기본 요약 생성

        Args:
            title: Issue 제목
            decision: Decision 텍스트

        Returns:
            기본 한국어 요약
        """
        if decision:
            # Decision이 있으면 포함
            return f"{title}에 대한 논의가 진행되었습니다. {decision}"
        else:
            return f"{title}에 대한 Liaison Statement입니다."

    def generate_batch(
        self, issues: list[dict[str, str]]
    ) -> list[str]:
        """
        여러 Issue를 일괄 요약

        Args:
            issues: [{"issue_text": ..., "title": ..., "decision": ...}, ...]

        Returns:
            한국어 요약 리스트
        """
        results = []
        for issue in issues:
            result = self._generate_summary(
                issue.get("issue_text", ""),
                issue.get("title", ""),
                issue.get("decision", ""),
            )
            results.append(result.output)
        return results

    def generate_section_overview(
        self,
        section_text: str,
        meeting_number: str,
        issue_count: int,
        issues_info: list[dict] = None,
    ) -> AgentResult:
        """
        Section 전체 Overview 생성 (한국어) - LLM 기반

        Args:
            section_text: Section 전체 텍스트
            meeting_number: 미팅 번호 (예: "120")
            issue_count: Issue 개수
            issues_info: 처리된 Issues 정보 리스트
                [{"title": ..., "source_wg": ..., "agenda_item": ...}, ...]

        Returns:
            AgentResult with Section Overview
        """
        # Issues 정보를 LLM에 전달할 형식으로 준비
        issues_summary = ""
        if issues_info:
            issues_list = []
            for i, issue in enumerate(issues_info, 1):
                title = issue.get("title", "Unknown")
                source_wg = issue.get("source_wg", "Unknown")
                agenda = issue.get("agenda_item", "N/A")
                issues_list.append(f"{i}. [{source_wg}] {title} (Agenda: {agenda})")
            issues_summary = "\n".join(issues_list)

        prompt = f"""You are creating a Korean overview for RAN1 #{meeting_number} Incoming Liaison Statements.

**Processed Issues ({issue_count} total):**
{issues_summary if issues_summary else "No detailed issue info available"}

**Section Text (first 1500 chars for context):**
{section_text[:1500]}

**Instructions:**
1. Write a comprehensive overview in **Korean** (3-5 sentences)
2. Analyze the processed issues and:
   - Identify main topics/themes discussed
   - Note the source Working Groups
   - Summarize key technical areas
3. Generate accurate categories by grouping related issues
4. Professional, informative tone

**IMPORTANT for Categories:**
- Group the {issue_count} issues by their technical topic/theme
- Each category should have an accurate count
- Categories should reflect actual issue topics (e.g., "MIMO", "NTN", "Positioning", "Coverage Enh", "Mobility Enh")
- The sum of all category counts should approximately equal {issue_count}

Return as JSON:
{{
  "overview": "한국어 오버뷰 텍스트 (3-5문장)",
  "source_wgs": ["RAN2", "RAN3", ...],
  "categories": {{"기술_주제_1": count, "기술_주제_2": count, ...}},
  "confidence": 0.0-1.0
}}
"""

        try:
            response = self.llm.generate(prompt, temperature=0.3, max_tokens=1500)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"[SummaryGenerator] Overview parse failed: {error}")
                default = f"RAN1 #{meeting_number} Incoming LS 섹션에서 총 {issue_count}개의 Liaison Statement가 처리되었습니다."
                return AgentResult(
                    success=True,
                    output={"overview": default, "source_wgs": [], "categories": {}},
                    confidence_score=0.3,
                )

            return AgentResult(
                success=True,
                output=parsed,
                confidence_score=parsed.get("confidence", 0.7),
            )

        except Exception as e:
            logger.error(f"[SummaryGenerator] Overview generation failed: {e}")
            default = f"RAN1 #{meeting_number} Incoming LS 섹션에서 총 {issue_count}개의 Liaison Statement가 처리되었습니다."
            return AgentResult(
                success=True,
                output={"overview": default, "source_wgs": [], "categories": {}},
                confidence_score=0.2,
                error_message=str(e),
            )
