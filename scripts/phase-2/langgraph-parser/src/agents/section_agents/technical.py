"""
Technical Agent

Maintenance, Release, Study, UE_Features 섹션 처리
"""

from typing import Any

from .base import BaseSectionAgent
from ..subsection_agents.maintenance import MaintenanceSubAgent
from ..subsection_agents.release import ReleaseSubAgent
from ..subsection_agents.study import StudySubAgent
from ..subsection_agents.ue_features import UEFeaturesSubAgent
from ...utils.markdown import extract_section

# section_type → SubSection Agent 매핑
SUBSECTION_AGENT_MAP = {
    "Maintenance": MaintenanceSubAgent,
    "Release": ReleaseSubAgent,
    "Study": StudySubAgent,
    "UE_Features": UEFeaturesSubAgent,
}


class TechnicalAgent(BaseSectionAgent):
    """Technical Agent

    명세서 5.1장 참조:
    - 담당: Maintenance, Release, Study, UE_Features
    - Leaf 탐색 후 해당 SubSection Agent 호출
    """

    def get_supported_types(self) -> list[str]:
        """지원하는 section_type 목록"""
        return ["Maintenance", "Release", "Study", "UE_Features"]

    def process(
        self,
        section_id: str,
        section_content: str,
        toc_info: dict,
    ) -> dict[str, Any]:
        """섹션 처리

        명세서 4.3.1 Leaf 본문 추출:
        - Leaf 섹션 탐색 (children: [])
        - section_type에 따라 SubSection Agent 선택
        - 각 Leaf에 대해 SubSection Agent 호출
        - 결과 취합

        Args:
            section_id: 섹션 ID
            section_content: 섹션 본문 (Markdown)
            toc_info: TOC 정보 (leaves, section_type 포함)

        Returns:
            처리 결과 (section_id, items, leaves 등)
        """
        section_type = toc_info.get("section_type", "Maintenance")
        leaves = toc_info.get("leaves", [])
        meeting_id = toc_info.get("meeting_id", "")

        # SubSection Agent 선택 (기본값: MaintenanceSubAgent)
        agent_class = SUBSECTION_AGENT_MAP.get(section_type, MaintenanceSubAgent)
        agent = agent_class()

        all_items = []
        leaf_results = []

        # 각 Leaf에 대해 Item 추출
        for i, leaf in enumerate(leaves):
            leaf_id = leaf.get("id", "")
            leaf_title = leaf.get("title", "")

            # 다음 Leaf 정보 (본문 추출 경계용)
            next_leaf = leaves[i + 1] if i + 1 < len(leaves) else None
            next_id = next_leaf.get("id") if next_leaf else None
            next_title = next_leaf.get("title") if next_leaf else None

            # Leaf 본문 추출
            leaf_content = extract_section(
                markdown_content=section_content,
                section_id=leaf_id,
                section_title=leaf_title,
                next_section_id=next_id,
                next_section_title=next_title,
            )

            if not leaf_content:
                leaf_results.append({
                    "leaf_id": leaf_id,
                    "title": leaf_title,
                    "status": "empty",
                    "item_count": 0,
                })
                continue

            # SubSection Agent 호출
            context = {
                "meeting_id": meeting_id,
                "section_id": section_id,
                "section_type": section_type,
            }

            items = agent.extract_items(
                leaf_id=leaf_id,
                leaf_title=leaf_title,
                leaf_content=leaf_content,
                context=context,
            )

            all_items.extend(items)
            leaf_results.append({
                "leaf_id": leaf_id,
                "title": leaf_title,
                "status": "completed",
                "item_count": len(items),
            })

        return {
            "section_id": section_id,
            "title": toc_info.get("title", ""),
            "section_type": section_type,
            "status": "completed",
            "leaves": leaf_results,
            "items": all_items,
        }
