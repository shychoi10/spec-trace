"""
Base Section Agent

모든 Section Agent의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSectionAgent(ABC):
    """Section Agent 기본 클래스

    명세서 5.1장 참조:
    - Depth 1 섹션을 담당
    - Leaf 탐색 후 SubSection Agent 호출
    """

    def __init__(self, config: dict | None = None):
        """초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}

    @abstractmethod
    def process(
        self,
        section_id: str,
        section_content: str,
        toc_info: dict,
    ) -> dict[str, Any]:
        """섹션 처리

        Args:
            section_id: Depth 1 섹션 ID
            section_content: 섹션 Markdown 내용
            toc_info: TOC 정보 (children, section_type 등)

        Returns:
            SectionResult 형태의 딕셔너리
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> list[str]:
        """지원하는 section_type 목록 반환"""
        pass
