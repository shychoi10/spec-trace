"""
TdocCategorizerAgent: Tdoc을 doc_type별로 분류하는 에이전트

Ground Truth 형식에서 Tdoc은 다음과 같이 분류됨:
- Draft / Discussion Tdocs
- Moderator Summaries
- LS 관련 Tdocs
- Final CRs

** 제1 원칙 준수 **
- 모든 분류는 LLM으로만 수행
- NO REGEX for semantic analysis
"""

import json
import logging
from typing import Any

from ..base_agent import BaseAgent
from ...models import DocType, TdocWithType

logger = logging.getLogger(__name__)


class TdocCategorizerAgent(BaseAgent):
    """
    Tdoc ID와 제목, 소스를 분석하여 doc_type 분류

    Ground Truth 출력 형식:
    - `R1-2500143` – *Draft CR on DCI size alignment* (ZTE, Sanechips) – `cr_draft`
    """

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Tdoc 목록을 분류하여 TdocWithType 객체 리스트 반환

        Args:
            state:
                - tdocs: list[dict] with tdoc_id, title, source
                - context: 추가 컨텍스트 (Section 타입 등)

        Returns:
            state with categorized_tdocs: list[TdocWithType]
        """
        self.log_start("Tdoc categorization")

        tdocs = state.get("tdocs", [])
        context = state.get("context", "")

        if not tdocs:
            self.log_end("Tdoc categorization (empty)", success=True)
            return {**state, "categorized_tdocs": []}

        # LLM으로 분류
        categorized = self._categorize_with_llm(tdocs, context)

        self.log_end(f"Tdoc categorization ({len(categorized)} items)")
        return {**state, "categorized_tdocs": categorized}

    def _categorize_with_llm(
        self, tdocs: list[dict], context: str
    ) -> list[TdocWithType]:
        """
        LLM을 사용하여 Tdoc 분류 (제1 원칙 준수)

        Args:
            tdocs: Tdoc 정보 리스트
            context: 추가 컨텍스트

        Returns:
            TdocWithType 객체 리스트
        """
        prompt = f"""You are a 3GPP document classifier. Analyze the following TDoc list and classify each one.

## Document Types (doc_type)
- cr_draft: Draft Change Request (contains "Draft CR", "dCR", or CR proposal)
- cr_final: Final approved CR (contains "CR" approved, "agreed", "final CR")
- ls_incoming: Incoming Liaison Statement (LS from other WGs, "LS on", "Reply LS from")
- ls_draft: Draft outgoing LS (draft reply LS)
- ls_final: Final approved outgoing LS
- summary: Moderator summary document (contains "Summary", "FL summary", "Moderator")
- summary_final: Final moderator summary
- discussion: Discussion paper or contribution
- session_notes: Session moderator notes
- ue_feature_list: UE feature list document
- other: Cannot classify

## Context
{context if context else "General maintenance discussion"}

## TDocs to classify
{json.dumps(tdocs, indent=2, ensure_ascii=False)}

## Output Format
Return a JSON array where each item has:
- tdoc_id: The TDoc ID
- title: The title
- source: The source/company
- doc_type: One of the doc_type values above

Example:
[
  {{"tdoc_id": "R1-2500143", "title": "Draft CR on DCI size alignment", "source": "ZTE, Sanechips", "doc_type": "cr_draft"}},
  {{"tdoc_id": "R1-2500200", "title": "Summary #5 for MIMO", "source": "Moderator", "doc_type": "summary"}}
]

Return ONLY the JSON array, no explanation.
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=4096)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"JSON parse failed: {error}")
                return self._create_default_categorization(tdocs)

            # TdocWithType 객체로 변환
            result = []
            for item in parsed:
                try:
                    doc_type = DocType(item.get("doc_type", "other"))
                except ValueError:
                    doc_type = DocType.OTHER

                result.append(TdocWithType(
                    tdoc_id=item.get("tdoc_id", ""),
                    title=item.get("title", ""),
                    source=item.get("source", ""),
                    doc_type=doc_type
                ))

            return result

        except Exception as e:
            logger.error(f"LLM categorization failed: {e}")
            return self._create_default_categorization(tdocs)

    def _create_default_categorization(
        self, tdocs: list[dict]
    ) -> list[TdocWithType]:
        """
        LLM 실패 시 기본 분류 (모두 'other'로)

        NOTE: 제1 원칙에 따라 regex fallback은 사용하지 않음
        """
        return [
            TdocWithType(
                tdoc_id=t.get("tdoc_id", ""),
                title=t.get("title", ""),
                source=t.get("source", ""),
                doc_type=DocType.OTHER
            )
            for t in tdocs
        ]

    def group_by_category(
        self, categorized_tdocs: list[TdocWithType]
    ) -> dict[str, list[TdocWithType]]:
        """
        분류된 Tdoc들을 Ground Truth 형식의 그룹으로 분류

        Returns:
            {
                "draft_discussion": [...],  # cr_draft, discussion
                "moderator_summaries": [...],  # summary, summary_final
                "ls_related": [...],  # ls_incoming, ls_draft, ls_final
                "final_crs": [...],  # cr_final
            }
        """
        groups = {
            "draft_discussion": [],
            "moderator_summaries": [],
            "ls_related": [],
            "final_crs": [],
            "others": []
        }

        for tdoc in categorized_tdocs:
            if tdoc.doc_type in [DocType.CR_DRAFT, DocType.DISCUSSION]:
                groups["draft_discussion"].append(tdoc)
            elif tdoc.doc_type in [DocType.SUMMARY, DocType.SUMMARY_FINAL]:
                groups["moderator_summaries"].append(tdoc)
            elif tdoc.doc_type in [DocType.LS_INCOMING, DocType.LS_DRAFT,
                                   DocType.LS_FINAL, DocType.LS_REPLY_DRAFT]:
                groups["ls_related"].append(tdoc)
            elif tdoc.doc_type == DocType.CR_FINAL:
                groups["final_crs"].append(tdoc)
            else:
                groups["others"].append(tdoc)

        return groups
