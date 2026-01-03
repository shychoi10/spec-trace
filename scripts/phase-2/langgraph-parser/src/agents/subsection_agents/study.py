"""
Study SubSection Agent

Study 섹션에서 Item 추출
"""

from typing import Any

from .base import BaseSubSectionAgent
from ...prompts.subsection_prompts import STUDY_PROMPT
from ...utils.llm_client import call_llm_for_items


class StudySubAgent(BaseSubSectionAgent):
    """Study SubSection Agent

    명세서 5.2.3 참조:
    - 단위: Moderator Summary
    - 주요 결과: Agreement, Conclusion, Observation, FFS
    - TR 정보 추출
    """

    def get_section_type(self) -> str:
        """담당 section_type"""
        return "Study"

    def extract_items(
        self,
        leaf_id: str,
        leaf_title: str,
        leaf_content: str,
        context: dict,
    ) -> list[dict[str, Any]]:
        """Item 추출

        명세서 5.2.3, 6.5.3 참조:
        - Moderator Summary 경계 판단
        - Agreement, Conclusion, Observation, FFS 추출
        - tr_info, session_info 필드 생성

        Args:
            leaf_id: Leaf 섹션 ID
            leaf_title: Leaf 섹션 제목
            leaf_content: Leaf Markdown 내용
            context: 컨텍스트 (meeting_id, section_id, section_type 등)

        Returns:
            Item 목록
        """
        if not leaf_content or not leaf_content.strip():
            return []

        # 컨텍스트에 leaf 정보 추가
        full_context = {
            **context,
            "leaf_id": leaf_id,
            "leaf_title": leaf_title,
            "section_type": self.get_section_type(),
        }

        # LLM 호출로 Item 추출
        items = call_llm_for_items(
            leaf_content=leaf_content,
            context=full_context,
            prompt_template=STUDY_PROMPT,
        )

        # 각 Item에 context.leaf_id 추가 (role_3에서 필터링용)
        for item in items:
            if "context" not in item:
                item["context"] = {}
            item["context"]["leaf_id"] = leaf_id

        return items
