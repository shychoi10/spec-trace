"""
Annex SubSection Agent

Annex B, C-1, C-2 처리
"""

from typing import Any

from .base import BaseSubSectionAgent
from ...prompts.subsection_prompts import ANNEX_PROMPTS
from ...utils.llm_client import call_llm_for_annex


class AnnexSubAgent(BaseSubSectionAgent):
    """Annex SubSection Agent

    명세서 5.2.6 참조:
    - 대상: Annex B (CR), C-1 (Outgoing LS), C-2 (Incoming LS)
    - 크로스체크용 목록 추출
    - Item이 아닌 Entry 추출
    """

    def get_section_type(self) -> str:
        """담당 section_type"""
        return "Annex"

    def extract_items(
        self,
        leaf_id: str,
        leaf_title: str,
        leaf_content: str,
        context: dict,
    ) -> list[dict[str, Any]]:
        """Annex 처리 (별도 스키마)

        명세서 5.2.6, 6.5.6 참조:
        - Annex 유형 판단 (B, C-1, C-2)
        - 해당 스키마로 목록 추출
        - Item이 아닌 Entry 반환

        Args:
            leaf_id: Leaf 섹션 ID (사용 안함)
            leaf_title: Leaf 섹션 제목
            leaf_content: Annex 본문
            context: 컨텍스트 (annex_id 포함)

        Returns:
            Entry 목록 (Annex 스키마)
        """
        if not leaf_content or not leaf_content.strip():
            return []

        # annex_id 확인
        annex_id = context.get("annex_id", "")
        if not annex_id:
            return []

        # annex_id에 맞는 프롬프트 선택
        prompt_template = ANNEX_PROMPTS.get(annex_id)
        if not prompt_template:
            return []

        # LLM 호출로 Entry 추출
        entries = call_llm_for_annex(
            annex_content=leaf_content,
            annex_id=annex_id,
            prompt_template=prompt_template,
        )

        return entries

    def extract_entries(
        self,
        annex_content: str,
        annex_id: str,
    ) -> list[dict[str, Any]]:
        """Annex Entry 추출 (직접 호출용)

        Args:
            annex_content: Annex 본문
            annex_id: annex_b, annex_c1, annex_c2

        Returns:
            Entry 목록
        """
        context = {"annex_id": annex_id}
        return self.extract_items(
            leaf_id="",
            leaf_title="",
            leaf_content=annex_content,
            context=context,
        )
