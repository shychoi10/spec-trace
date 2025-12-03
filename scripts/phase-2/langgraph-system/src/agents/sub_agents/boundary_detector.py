"""
BoundaryDetector Sub-Agent

Section 텍스트에서 개별 Issue의 경계를 식별합니다.
모든 경계 감지는 LLM이 수행합니다 (no regex).

True Agentic AI: 하드코딩된 규칙 없음
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class BoundaryDetector(BaseAgent):
    """Issue 경계 감지 Sub-Agent"""

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.section_hints = self.config.get("incoming_ls_hints", {})

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Incoming LS 텍스트에서 Issue 경계 식별 (콘텐츠 기반)

        Args:
            state: LangGraph state
                - content: Incoming LS 전체 텍스트
                - metadata: 메타데이터

        Returns:
            업데이트된 state
                - boundaries: Issue 경계 리스트
        """
        content = state.get("content", "")
        metadata = state.get("metadata", {})

        self.log_start("Issue boundary detection")

        # LLM으로 경계 감지
        result = self._detect_boundaries(content, metadata)

        if result.success:
            state["boundaries"] = result.output
            state["boundary_confidence"] = result.confidence_score
            self.log_end("Issue boundary detection", success=True)
        else:
            state["boundaries"] = []
            state["boundary_confidence"] = 0.0
            self.log_end("Issue boundary detection", success=False)

        return state

    def _detect_boundaries(
        self, content: str, metadata: dict
    ) -> AgentResult:
        """
        LLM을 사용하여 Issue 경계 감지 (청킹 방식으로 전체 문서 분석)

        Args:
            content: Section 텍스트
            metadata: 메타데이터

        Returns:
            AgentResult with boundaries list
        """
        # 전체 콘텐츠를 한 번에 분석 (max_tokens 늘림)
        # 콘텐츠가 너무 길면 청킹 적용
        content_length = len(content)

        if content_length <= 25000:
            # 짧은 콘텐츠: 전체 분석
            return self._detect_boundaries_single(content)
        else:
            # 긴 콘텐츠: 청킹 분석
            return self._detect_boundaries_chunked(content)

    def _detect_boundaries_single(self, content: str, meeting_number: str = "") -> AgentResult:
        """단일 콘텐츠에서 경계 감지 (콘텐츠 기반) - 전체 Issue 텍스트 추출"""
        boundary_hints = self.section_hints.get("boundary_detection", {})

        prompt = f"""Extract ALL Incoming LS items from this 3GPP RAN1 meeting report.

RULES:
- Issue = Incoming LS with ID (R1-25XXXXX) and title like "LS on...", "Reply LS..."
- Each Issue has: ls_id, title, source_wg, decision, relevant_tdocs, agenda_item
- "Discussion on..." and "Draft reply LS..." are relevant_tdocs, NOT separate issues
- Issue Types: actionable (needs response), non_action (no action), reference (CC-only)
- AGENDA ITEM: Extract from text like "agenda item 8.1 (Coverage Enh)" → "8.1 — Coverage Enhancement"

CONTENT:
{content[:25000]}

OUTPUT JSON (no markdown):
{{"boundaries":[{{"item_number":1,"ls_id":"R1-25XXXXX","title":"LS on...","source_wg":"RAN2","source_companies":["Company"],"relevant_tdocs":[{{"id":"R1-25XXXXX","title":"Discussion...","companies":["Company"],"doc_type":"discussion"}}],"decision":"text","agenda_item":"8.1 — Topic","is_primary":true,"issue_type":"actionable"}}],"cc_only_items":[{{"ls_id":"R1-25XXXXX","title":"LS title","source_wg":"RAN2"}}],"total_primary":1,"total_cc_only":1,"confidence":0.9}}"""

        try:
            # max_tokens 증가: 20+ Issues × 1,500자 + JSON 오버헤드 = 48K 필요
            # See: docs/phase-2/LLM_TOKEN_GUIDELINES.md
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=48000)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"[BoundaryDetector] JSON parse failed: {error}")
                return AgentResult(
                    success=False,
                    output=[],
                    confidence_score=0.0,
                    error_message=error,
                )

            boundaries = parsed.get("boundaries", [])
            cc_only_items = parsed.get("cc_only_items", [])
            confidence = parsed.get("confidence", 0.7)

            # 기본 검증
            validation_notes = []
            if len(boundaries) == 0:
                validation_notes.append("No boundaries detected")
                confidence = 0.3

            # CC-only 항목도 결과에 포함
            result_output = {
                "boundaries": boundaries,
                "cc_only_items": cc_only_items,
                "total_primary": len(boundaries),
                "total_cc_only": len(cc_only_items),
            }

            return AgentResult(
                success=True,
                output=result_output,
                confidence_score=confidence,
                validation_notes=validation_notes,
            )

        except Exception as e:
            logger.error(f"[BoundaryDetector] LLM call failed: {e}")
            return AgentResult(
                success=False,
                output=[],
                confidence_score=0.0,
                error_message=str(e),
            )

    def _detect_boundaries_chunked(self, content: str) -> AgentResult:
        """청킹 방식으로 경계 감지 (긴 콘텐츠용)"""
        chunk_size = 20000
        overlap = 3000
        all_boundaries = []
        all_cc_only = []
        seen_ls_ids = set()

        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i:i + chunk_size]
            chunk_result = self._detect_boundaries_single(chunk)

            if chunk_result.success and isinstance(chunk_result.output, dict):
                # 중복 제거하며 병합
                for boundary in chunk_result.output.get("boundaries", []):
                    ls_id = boundary.get("ls_id", "")
                    if ls_id and ls_id not in seen_ls_ids:
                        seen_ls_ids.add(ls_id)
                        all_boundaries.append(boundary)

                for cc_item in chunk_result.output.get("cc_only_items", []):
                    ls_id = cc_item.get("ls_id", "")
                    if ls_id and ls_id not in seen_ls_ids:
                        seen_ls_ids.add(ls_id)
                        all_cc_only.append(cc_item)

        result_output = {
            "boundaries": all_boundaries,
            "cc_only_items": all_cc_only,
            "total_primary": len(all_boundaries),
            "total_cc_only": len(all_cc_only),
        }

        return AgentResult(
            success=True,
            output=result_output,
            confidence_score=0.8 if all_boundaries else 0.3,
            validation_notes=[f"Chunked analysis: {len(all_boundaries)} primary, {len(all_cc_only)} CC-only"],
        )

    def detect_pattern(self, content: str) -> float:
        """Incoming LS 패턴 감지 (콘텐츠 기반)"""
        # 간단한 키워드 체크 (실제 분류는 LLM이 수행)
        ls_indicators = ["incoming liaison", "ls on", "reply ls", "liaison statement"]
        content_lower = content.lower()

        matches = sum(1 for ind in ls_indicators if ind in content_lower)
        return min(1.0, matches * 0.3) if matches > 0 else 0.0
