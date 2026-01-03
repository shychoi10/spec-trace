"""
Annex 모델

명세서 3.4장 참조: Annex 스키마 정의
- Annex B: CR 목록 (크로스체크용)
- Annex C-1: Outgoing LS
- Annex C-2: Incoming LS
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# === Entry 모델 ===


class AnnexBEntry(BaseModel):
    """Annex B Entry (CR 항목)

    명세서 3.4장 참조
    """

    tdoc_id: str = Field(
        ...,
        description="CR TDoc 번호",
    )
    title: str = Field(
        ...,
        description="CR 제목",
    )
    source: str = Field(
        ...,
        description="제안자",
    )
    spec: str = Field(
        ...,
        description="대상 스펙",
    )
    cr_number: str = Field(
        ...,
        description="CR 번호",
    )


class AnnexC1Entry(BaseModel):
    """Annex C-1 Entry (Outgoing LS)

    명세서 3.4장 참조
    """

    tdoc_id: str = Field(
        ...,
        description="Outgoing LS TDoc",
    )
    title: str = Field(
        ...,
        description="LS 제목",
    )
    to: str = Field(
        ...,
        description="수신 그룹",
    )


class AnnexC2Entry(BaseModel):
    """Annex C-2 Entry (Incoming LS)

    명세서 3.4장 참조
    """

    tdoc_id: str = Field(
        ...,
        description="Incoming LS TDoc",
    )
    title: str = Field(
        ...,
        description="LS 제목",
    )
    source: str = Field(
        ...,
        description="발신 그룹",
    )
    handled_in: Optional[str] = Field(
        default=None,
        description="처리된 agenda item (선택)",
    )


# === Annex 모델 ===


class AnnexB(BaseModel):
    """Annex B 모델 (CR 목록)

    명세서 3.4장 참조: 크로스체크용
    """

    annex_id: str = Field(
        default="annex_b",
        description="Annex 식별자",
    )
    title: str = Field(
        default="List of CRs agreed",
        description="Annex 제목",
    )
    entries: List[AnnexBEntry] = Field(
        default_factory=list,
        description="CR 항목 목록",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "annex_id": "annex_b",
                "title": "List of CRs agreed",
                "entries": [
                    {
                        "tdoc_id": "R1-2501501",
                        "title": "Correction on transition time...",
                        "source": "vivo",
                        "spec": "TS 38.213",
                        "cr_number": "0693",
                    }
                ],
            }
        }


class AnnexC1(BaseModel):
    """Annex C-1 모델 (Outgoing LS)

    명세서 3.4장 참조: 크로스체크용
    """

    annex_id: str = Field(
        default="annex_c1",
        description="Annex 식별자",
    )
    title: str = Field(
        default="List of Outgoing LSs",
        description="Annex 제목",
    )
    entries: List[AnnexC1Entry] = Field(
        default_factory=list,
        description="Outgoing LS 항목 목록",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "annex_id": "annex_c1",
                "title": "List of Outgoing LSs",
                "entries": [
                    {
                        "tdoc_id": "R1-2501479",
                        "title": "Reply LS on...",
                        "to": "RAN2",
                    }
                ],
            }
        }


class AnnexC2(BaseModel):
    """Annex C-2 모델 (Incoming LS)

    명세서 3.4장 참조: 크로스체크용
    """

    annex_id: str = Field(
        default="annex_c2",
        description="Annex 식별자",
    )
    title: str = Field(
        default="List of Incoming LSs",
        description="Annex 제목",
    )
    entries: List[AnnexC2Entry] = Field(
        default_factory=list,
        description="Incoming LS 항목 목록",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "annex_id": "annex_c2",
                "title": "List of Incoming LSs",
                "entries": [
                    {
                        "tdoc_id": "R1-2500012",
                        "title": "LS on UL 8Tx",
                        "source": "RAN2",
                        "handled_in": "8.1",
                    }
                ],
            }
        }
