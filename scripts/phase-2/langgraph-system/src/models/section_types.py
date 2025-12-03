"""
Section Types for Phase-2 LangGraph System

Meta Agent가 분류한 Section 타입 및 메타데이터 정의

Note: 콘텐츠 기반 모델 - Section 번호에 종속되지 않음
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class SectionType(str, Enum):
    """
    Section 타입 (LLM이 분류)

    Note: Section 번호가 아닌 콘텐츠 유형으로 정의
    """

    INCOMING_LS = "incoming_ls"  # Incoming Liaison Statements
    MAINTENANCE = "maintenance"  # Maintenance (Rel-18, Pre-Rel-18 등)
    RELEASE_WORK = "release_work"  # Release 19/20 Work Items
    DRAFT_LS = "draft_ls"  # Draft Liaison Statements
    ADMINISTRATIVE = "administrative"  # Opening, Closing, Approval 등
    ANNEX = "annex"  # Annex sections
    OTHER = "other"  # 분류 불가

    def __str__(self) -> str:
        return self.value


class Technology(str, Enum):
    """
    기술 타입 (LLM이 분류)

    Note: Maintenance Section에서 사용
    """

    NR = "NR"  # New Radio (5G)
    E_UTRA = "E-UTRA"  # LTE
    COMMON = "common"  # 공통 (NR/E-UTRA 모두 해당)

    def __str__(self) -> str:
        return self.value


class Release(str, Enum):
    """
    Release 타입 (LLM이 분류)

    Note: Maintenance/Work Item Section에서 사용
    """

    REL_18 = "Rel-18"
    REL_19 = "Rel-19"
    REL_20 = "Rel-20"
    PRE_REL_18 = "Pre-Rel-18"  # Rel-17 이하

    def __str__(self) -> str:
        return self.value


@dataclass
class SectionClassification:
    """
    LLM이 분류한 Section 정보

    MetaSectionAgent의 출력 구조
    """

    section_type: SectionType
    release: Optional[Release] = None  # Maintenance/Work Item인 경우
    technology: Optional[Technology] = None  # Maintenance인 경우
    confidence: float = 0.0  # 분류 신뢰도 (0.0 ~ 1.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_type": str(self.section_type),
            "release": str(self.release) if self.release else None,
            "technology": str(self.technology) if self.technology else None,
            "confidence": self.confidence,
        }


@dataclass
class SectionMetadata:
    """
    Section 메타데이터

    워크플로우에 전달되는 Section 컨텍스트 정보
    """

    title: str  # Section 제목 (원본)
    classification: SectionClassification  # LLM 분류 결과
    content_preview: str = ""  # 콘텐츠 미리보기 (첫 500자)

    # 추출 정보 (DocumentParser에서 설정)
    start_index: int = 0  # 문서 내 시작 위치
    end_index: int = 0  # 문서 내 종료 위치

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "classification": self.classification.to_dict(),
            "content_preview": self.content_preview[:100] + "..."
            if len(self.content_preview) > 100
            else self.content_preview,
            "start_index": self.start_index,
            "end_index": self.end_index,
        }

    @property
    def section_type(self) -> SectionType:
        """편의 프로퍼티: classification.section_type"""
        return self.classification.section_type

    @property
    def release(self) -> Optional[Release]:
        """편의 프로퍼티: classification.release"""
        return self.classification.release

    @property
    def technology(self) -> Optional[Technology]:
        """편의 프로퍼티: classification.technology"""
        return self.classification.technology

    def get_output_filename_suffix(self) -> str:
        """
        출력 파일명 suffix 생성

        예시:
        - incoming_ls
        - maintenance_rel18
        - maintenance_pre_rel18_nr
        - maintenance_pre_rel18_eutra
        """
        suffix = str(self.section_type)

        if self.release:
            release_str = str(self.release).lower().replace("-", "_").replace(" ", "_")
            suffix = f"{suffix}_{release_str}"

        if self.technology:
            tech_str = str(self.technology).lower().replace("-", "_")
            suffix = f"{suffix}_{tech_str}"

        return suffix


@dataclass
class ParsedSection:
    """
    파싱된 Section 데이터

    DocumentParser가 추출한 Section 전체 정보
    """

    metadata: SectionMetadata
    content: str  # Section 전체 텍스트
    raw_paragraphs: list[str] = field(default_factory=list)  # 원본 paragraph 목록

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "content_length": len(self.content),
            "paragraph_count": len(self.raw_paragraphs),
        }
