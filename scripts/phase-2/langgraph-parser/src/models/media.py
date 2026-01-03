"""
MediaIndex 모델

명세서 3.5장 참조: 문서 내 이미지/테이블과 Item 간 연결 관계 추적
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class MediaReference(BaseModel):
    """미디어를 참조하는 Item 정보"""

    item_id: str = Field(
        ...,
        description="Item 식별자 (예: RAN1_120_9.1.1_001)",
    )
    leaf_id: str = Field(
        ...,
        description="Leaf 섹션 번호 (예: 9.1.1)",
    )


class ImageEntry(BaseModel):
    """이미지 인덱스 항목"""

    id: str = Field(
        ...,
        description="이미지 식별자 (img_001, img_002, ...)",
    )
    path: str = Field(
        ...,
        description="파일 경로 (media/image1.png)",
    )
    referenced_in: List[MediaReference] = Field(
        default_factory=list,
        description="참조하는 Item 목록",
    )
    label: Optional[str] = Field(
        default=None,
        description="Figure 레이블 (예: Figure 3)",
    )


class TableEntry(BaseModel):
    """테이블 인덱스 항목"""

    id: str = Field(
        ...,
        description="테이블 식별자 (tbl_001, tbl_002, ...)",
    )
    referenced_in: List[MediaReference] = Field(
        default_factory=list,
        description="포함된 Item 목록",
    )
    label: Optional[str] = Field(
        default=None,
        description="Table 레이블 (예: Table 1)",
    )


class MediaStatistics(BaseModel):
    """미디어 통계"""

    total_images: int = Field(
        default=0,
        description="총 이미지 수",
    )
    total_tables: int = Field(
        default=0,
        description="총 테이블 수",
    )
    items_with_media: int = Field(
        default=0,
        description="미디어 포함 Item 수",
    )


class MediaIndex(BaseModel):
    """미디어 인덱스 (역할 4 출력)

    명세서 3.5장 참조:
    - 문서 내 이미지/테이블과 Item 간 연결 관계 추적
    - Item의 media_refs와 양방향 참조 관계
    """

    meeting_id: str = Field(
        ...,
        description="회의 식별자 (예: RAN1_120)",
    )
    images: List[ImageEntry] = Field(
        default_factory=list,
        description="이미지 목록",
    )
    tables: List[TableEntry] = Field(
        default_factory=list,
        description="테이블 목록",
    )
    statistics: MediaStatistics = Field(
        default_factory=MediaStatistics,
        description="미디어 통계",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_id": "RAN1_120",
                "images": [
                    {
                        "id": "img_001",
                        "path": "media/image1.png",
                        "referenced_in": [
                            {"item_id": "RAN1_120_9.1.1_001", "leaf_id": "9.1.1"}
                        ],
                        "label": "Figure 3",
                    }
                ],
                "tables": [
                    {
                        "id": "tbl_001",
                        "referenced_in": [
                            {"item_id": "RAN1_120_9.1.2_002", "leaf_id": "9.1.2"}
                        ],
                        "label": "Table 1",
                    }
                ],
                "statistics": {
                    "total_images": 15,
                    "total_tables": 8,
                    "items_with_media": 12,
                },
            }
        }
