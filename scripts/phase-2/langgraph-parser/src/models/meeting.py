"""
MeetingInfo 모델

명세서 4.1장 참조: 회의 메타데이터 추출
"""

from pydantic import BaseModel, Field


class MeetingInfo(BaseModel):
    """회의 메타데이터 모델 (역할 1 출력)"""

    meeting_id: str = Field(
        ...,
        description="회의 식별자 (예: RAN1_120)",
        examples=["RAN1_120", "RAN1_122"],
    )
    tsg: str = Field(
        ...,
        description="TSG 이름 (예: RAN)",
        examples=["RAN"],
    )
    wg: str = Field(
        ...,
        description="Working Group (예: WG1)",
        examples=["WG1", "WG2"],
    )
    wg_code: str = Field(
        ...,
        description="WG 코드 (예: RAN1)",
        examples=["RAN1", "RAN2"],
    )
    meeting_number: str = Field(
        ...,
        description="회의 번호 (예: 120)",
        examples=["120", "122"],
    )
    version: str = Field(
        ...,
        description="문서 버전 (예: 1.0.0)",
        examples=["1.0.0", "1.1.0"],
    )
    location: str = Field(
        ...,
        description="회의 장소 (예: Athens, Greece)",
        examples=["Athens, Greece", "Bengaluru, India"],
    )
    start_date: str = Field(
        ...,
        description="시작일 (ISO 8601 형식: YYYY-MM-DD)",
        examples=["2025-02-17", "2025-08-25"],
    )
    end_date: str = Field(
        ...,
        description="종료일 (ISO 8601 형식: YYYY-MM-DD)",
        examples=["2025-02-21", "2025-08-29"],
    )
    source: str = Field(
        ...,
        description="문서 출처 (예: MCC Support)",
        examples=["MCC Support"],
    )
    document_for: str = Field(
        ...,
        description="문서 용도 (예: Approval)",
        examples=["Approval", "Information"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_id": "RAN1_120",
                "tsg": "RAN",
                "wg": "WG1",
                "wg_code": "RAN1",
                "meeting_number": "120",
                "version": "1.0.0",
                "location": "Athens, Greece",
                "start_date": "2025-02-17",
                "end_date": "2025-02-21",
                "source": "MCC Support",
                "document_for": "Approval",
            }
        }
