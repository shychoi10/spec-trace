"""
Base SubSection Agent

모든 SubSection Agent의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSubSectionAgent(ABC):
    """SubSection Agent 기본 클래스

    명세서 5.2장 참조:
    - Leaf Section에서 Item 추출
    - 의미 기반 경계 판단
    """

    def __init__(self, config: dict | None = None):
        """초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}

    @abstractmethod
    def extract_items(
        self,
        leaf_id: str,
        leaf_title: str,
        leaf_content: str,
        context: dict,
    ) -> list[dict[str, Any]]:
        """Item 추출

        Args:
            leaf_id: Leaf 섹션 ID
            leaf_title: Leaf 섹션 제목
            leaf_content: Leaf Markdown 내용
            context: 컨텍스트 (meeting_id, section_id, section_type 등)

        Returns:
            Item 목록 (Item 모델 직렬화)
        """
        pass

    @abstractmethod
    def get_section_type(self) -> str:
        """담당 section_type 반환"""
        pass
