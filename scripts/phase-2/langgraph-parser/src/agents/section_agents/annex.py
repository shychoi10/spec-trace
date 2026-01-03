"""
Annex Agent

Annex B, C-1, C-2 처리 (크로스체크용)
"""

import re
from typing import Any

from .base import BaseSectionAgent
from ..subsection_agents.annex import AnnexSubAgent


class AnnexAgent(BaseSectionAgent):
    """Annex Agent

    명세서 5.1장 참조:
    - 담당: Annex (B, C-1, C-2)
    - 크로스체크를 위한 목록 추출
    - Item이 아닌 Entry 반환
    """

    def get_supported_types(self) -> list[str]:
        """지원하는 section_type 목록"""
        return ["Annex"]

    def _determine_annex_id(self, title: str) -> str:
        """Annex 제목에서 annex_id 결정

        Args:
            title: Annex 섹션 제목

        Returns:
            annex_id (annex_b, annex_c1, annex_c2) 또는 빈 문자열
        """
        title_lower = title.lower()

        # Annex B: CRs
        if re.search(r"annex\s*b", title_lower):
            return "annex_b"

        # Annex C-1: Outgoing LS
        if re.search(r"annex\s*c[\-\s]*1", title_lower):
            return "annex_c1"

        # Annex C-2: Incoming LS
        if re.search(r"annex\s*c[\-\s]*2", title_lower):
            return "annex_c2"

        # 패턴 매칭 실패
        return ""

    def process(
        self,
        section_id: str,
        section_content: str,
        toc_info: dict,
    ) -> dict[str, Any]:
        """섹션 처리

        명세서 5.2.6 참조:
        - Annex 유형 판단 (B, C-1, C-2)
        - AnnexSubAgent 호출
        - Entry 목록 반환 (Item과 다른 스키마)

        Args:
            section_id: 섹션 ID
            section_content: 섹션 본문 (Markdown)
            toc_info: TOC 정보

        Returns:
            처리 결과 (section_id, entries 등)
        """
        title = toc_info.get("title", "")

        # Annex 유형 결정
        annex_id = self._determine_annex_id(title)

        if not annex_id:
            return {
                "section_id": section_id,
                "title": title,
                "section_type": "Annex",
                "annex_id": "",
                "status": "unsupported",
                "entries": [],
                "error": f"Unknown Annex type: {title}",
            }

        if not section_content or not section_content.strip():
            return {
                "section_id": section_id,
                "title": title,
                "section_type": "Annex",
                "annex_id": annex_id,
                "status": "empty",
                "entries": [],
            }

        # AnnexSubAgent 호출
        agent = AnnexSubAgent()
        entries = agent.extract_entries(
            annex_content=section_content,
            annex_id=annex_id,
        )

        return {
            "section_id": section_id,
            "title": title,
            "section_type": "Annex",
            "annex_id": annex_id,
            "status": "completed",
            "entries": entries,
            "entry_count": len(entries),
        }
