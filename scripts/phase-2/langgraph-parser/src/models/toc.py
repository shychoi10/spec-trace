"""
TOCSection 및 SectionType 모델

명세서 3.3.1장, 4.2장 참조: 목차 구조 및 섹션 타입 정의
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SectionType(str, Enum):
    """섹션 타입 (7종)

    명세서 3.3.1장 참조:
    - Procedural: 절차 섹션 (skip 처리)
    - Maintenance: 기존 Release 유지보수
    - Release: 새 기능 개발
    - Study: 연구 단계
    - UE_Features: UE 기능 정의
    - LS: Incoming LS 처리
    - Annex: 부록 (별도 스키마)
    """

    PROCEDURAL = "Procedural"
    MAINTENANCE = "Maintenance"
    RELEASE = "Release"
    STUDY = "Study"
    UE_FEATURES = "UE_Features"
    LS = "LS"
    ANNEX = "Annex"
    UNKNOWN = "unknown"


class TOCSection(BaseModel):
    """TOC 섹션 모델 (역할 2 출력)

    명세서 4.2장 참조:
    - TOC 파싱 + section_type 판단 + Agent 할당
    """

    id: str = Field(
        ...,
        description="섹션 ID (예: 9.1.1, 8.1v1)",
        examples=["9", "9.1", "9.1.1", "8.1v1"],
    )
    title: str = Field(
        ...,
        description="섹션 제목",
        examples=["Release 19", "Beam management"],
    )
    depth: int = Field(
        ...,
        description="TOC 계층 깊이 (1=최상위)",
        ge=1,
        examples=[1, 2, 3],
    )
    parent: Optional[str] = Field(
        default=None,
        description="부모 섹션 ID (Depth 1이면 None)",
        examples=["9", "9.1", None],
    )
    children: List[str] = Field(
        default_factory=list,
        description="자식 섹션 ID 목록 (Leaf면 빈 리스트)",
        examples=[["9.1", "9.2"], []],
    )
    section_type: SectionType = Field(
        ...,
        description="섹션 콘텐츠 유형 (7종)",
    )
    type_reason: str = Field(
        ...,
        description="section_type 판단 근거",
        examples=["Title contains 'Release 19'", "Section handles incoming LS"],
    )
    skip: bool = Field(
        ...,
        description="처리 제외 여부",
    )
    skip_reason: Optional[str] = Field(
        default=None,
        description="skip=true 시 제외 사유",
        examples=["Procedural section", "Not in extraction scope", None],
    )
    virtual: bool = Field(
        default=False,
        description="가상 번호 여부 (중간 노드에 콘텐츠가 있는 경우)",
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "examples": [
                {
                    "id": "9",
                    "title": "Release 19",
                    "depth": 1,
                    "parent": None,
                    "children": ["9.1", "9.2"],
                    "section_type": "Release",
                    "type_reason": "Title contains 'Release 19'",
                    "skip": False,
                    "skip_reason": None,
                    "virtual": False,
                },
                {
                    "id": "1",
                    "title": "Opening of the meeting",
                    "depth": 1,
                    "parent": None,
                    "children": [],
                    "section_type": "Procedural",
                    "type_reason": "Procedural section - Opening",
                    "skip": True,
                    "skip_reason": "Procedural section",
                    "virtual": False,
                },
                {
                    "id": "8.1v1",
                    "title": "MIMO (virtual)",
                    "depth": 2,
                    "parent": "8",
                    "children": [],
                    "section_type": "Maintenance",
                    "type_reason": "Intro content in non-leaf section",
                    "skip": False,
                    "skip_reason": None,
                    "virtual": True,
                },
            ]
        }
