"""
Pydantic 데이터 모델 패키지

명세서 3장 기반 데이터 모델 정의:
- MeetingInfo: 회의 메타데이터
- TOCSection, SectionType: 목차 구조
- Item: 추출 결과 단위
- Annex: 부록 데이터 (크로스체크용)
- MediaIndex: 미디어 인덱스 (이미지/테이블-Item 연결)
"""

from .meeting import MeetingInfo
from .toc import SectionType, TOCSection
from .item import (
    ItemContext,
    ResolutionContent,
    Resolution,
    Topic,
    Input,
    SessionInfo,
    CRInfo,
    TRInfo,
    LSInInfo,
    LSOutInfo,
    ErrorInfo,
    ProcessingInfo,
    WarningInfo,
    MediaRef,
    Item,
)
from .annex import AnnexBEntry, AnnexC1Entry, AnnexC2Entry, AnnexB, AnnexC1, AnnexC2
from .media import (
    MediaReference,
    ImageEntry,
    TableEntry,
    MediaStatistics,
    MediaIndex,
)

__all__ = [
    # Meeting
    "MeetingInfo",
    # TOC
    "SectionType",
    "TOCSection",
    # Item
    "ItemContext",
    "ResolutionContent",
    "Resolution",
    "Topic",
    "Input",
    "SessionInfo",
    "CRInfo",
    "TRInfo",
    "LSInInfo",
    "LSOutInfo",
    "ErrorInfo",
    "ProcessingInfo",
    "WarningInfo",
    "MediaRef",
    "Item",
    # Annex
    "AnnexBEntry",
    "AnnexC1Entry",
    "AnnexC2Entry",
    "AnnexB",
    "AnnexC1",
    "AnnexC2",
    # Media
    "MediaReference",
    "ImageEntry",
    "TableEntry",
    "MediaStatistics",
    "MediaIndex",
]
