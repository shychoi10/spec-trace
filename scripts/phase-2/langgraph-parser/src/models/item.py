"""
Item 모델 및 관련 서브 모델

명세서 3.3장 참조: Item 스키마 정의
- 필수 필드: id, context, resolution
- 선택 필드: topic, input, session_info, cr_info, tr_info, ls_in, ls_out, media_refs
- 메타데이터: _error, _processing, _warning
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# === 필수 필드 서브 모델 ===


class ItemContext(BaseModel):
    """Item 컨텍스트 (필수)

    명세서 3.3.2장 참조
    """

    meeting_id: str = Field(
        ...,
        description="회의 식별자 (예: RAN1_120)",
    )
    section_id: str = Field(
        ...,
        description="Depth 1 섹션 번호 (예: 9)",
    )
    leaf_id: str = Field(
        ...,
        description="Leaf 섹션 번호 (예: 9.1.1)",
    )
    leaf_title: str = Field(
        ...,
        description="Leaf 섹션 제목",
    )
    section_type: str = Field(
        ...,
        description="콘텐츠 유형 (Maintenance, Release, Study, UE_Features, LS)",
    )


class ResolutionContent(BaseModel):
    """Resolution 내용 항목

    명세서 3.3.2장 참조
    content.type 값: agreement, conclusion, decision, working_assumption, observation, ffs
    """

    type: str = Field(
        ...,
        description="내용 유형 (agreement, conclusion, decision, working_assumption, observation, ffs)",
    )
    text: str = Field(
        ...,
        description="전체 내용 (원문)",
    )
    marker: str = Field(
        ...,
        description="문서 내 마커 (예: [Agreement]{.mark})",
    )


class Resolution(BaseModel):
    """Resolution (필수)

    명세서 3.3.2장 참조
    status 값: Agreed, Concluded, No_Consensus, Deferred, Noted, Pending
    """

    status: str = Field(
        ...,
        description="결과 상태 (Agreed, Concluded, No_Consensus, Deferred, Noted, Pending)",
    )
    content: List[ResolutionContent] = Field(
        default_factory=list,
        description="결과 내용 목록",
    )


# === 선택 필드 서브 모델 ===


class Topic(BaseModel):
    """기술 논의 주제 (선택)

    명세서 3.3.3장 참조
    """

    summary: str = Field(
        ...,
        description="1줄 요약",
    )


class Input(BaseModel):
    """입력 문서 정보 (선택)

    명세서 3.3.3장 참조
    """

    moderator_summary: str = Field(
        ...,
        description="Summary TDoc 번호",
    )


class SessionInfo(BaseModel):
    """세션 추적 정보 (선택)

    명세서 3.3.3장 참조
    """

    first_discussed: Optional[str] = Field(
        default=None,
        description="첫 논의 세션 (예: Monday)",
    )
    concluded: Optional[str] = Field(
        default=None,
        description="결론 세션 (예: Thursday)",
    )
    comeback: bool = Field(
        default=False,
        description="재논의 여부",
    )


class CRInfo(BaseModel):
    """CR 정보 (선택, CR 승인 시)

    명세서 3.3.3장 참조
    """

    tdoc_id: str = Field(
        ...,
        description="CR TDoc 번호",
    )
    spec: str = Field(
        ...,
        description="대상 스펙 (예: TS 38.212)",
    )
    cr_number: str = Field(
        ...,
        description="CR 번호",
    )


class TRInfo(BaseModel):
    """TR 정보 (선택, Study용)

    명세서 3.3.3장 참조
    """

    tr_number: str = Field(
        ...,
        description="TR 번호 (예: TR 38.843)",
    )
    update_tdoc: Optional[str] = Field(
        default=None,
        description="업데이트 TDoc",
    )


class LSInInfo(BaseModel):
    """Incoming LS 정보 (선택)

    명세서 3.3.3장 참조
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
        description="발신 그룹 (예: RAN2)",
    )


class LSOutInfo(BaseModel):
    """Outgoing LS 정보 (선택)

    명세서 3.3.3장 참조
    """

    action: str = Field(
        ...,
        description="응답 액션 (Replied, Noted, No_Action)",
    )
    reply_tdoc: Optional[str] = Field(
        default=None,
        description="응답 TDoc",
    )


# === 메타데이터 서브 모델 ===


class ErrorInfo(BaseModel):
    """에러 정보 (에러 시)

    명세서 3.3.3장 참조
    error_type 권장 값: parsing_failed, extraction_failed, type_unknown, validation_failed
    """

    error_type: str = Field(
        ...,
        description="에러 유형",
    )
    error_message: str = Field(
        ...,
        description="에러 메시지",
    )


class ProcessingInfo(BaseModel):
    """처리 메타데이터

    명세서 3.3.3장 참조
    status 권장 값: completed, partial, failed
    """

    generated_at: str = Field(
        ...,
        description="생성 시각 (ISO 8601)",
    )
    status: str = Field(
        ...,
        description="처리 상태 (completed, partial, failed)",
    )
    chunked: bool = Field(
        default=False,
        description="청킹 여부",
    )
    chunk_count: Optional[int] = Field(
        default=None,
        description="청크 수 (chunked=true 시)",
    )


class WarningInfo(BaseModel):
    """경고 정보 (경고 시)

    명세서 3.3.3장 참조
    warning_type 권장 값: unknown_section_type, low_confidence, ambiguous_boundary, normalization_failed
    """

    type: str = Field(
        ...,
        description="경고 유형",
    )
    message: str = Field(
        ...,
        description="경고 메시지",
    )
    context: Optional[dict] = Field(
        default=None,
        description="추가 컨텍스트 (선택)",
    )


class MediaRef(BaseModel):
    """미디어 참조 (선택)

    명세서 3.3.3장 참조
    resolution.content.text에 이미지 또는 테이블이 포함된 경우 기록
    """

    type: str = Field(
        ...,
        description="미디어 유형 (image, table)",
    )
    ref: str = Field(
        ...,
        description="파일 경로 (media/image5.png) 또는 위치 식별자 (inline)",
    )
    label: Optional[str] = Field(
        default=None,
        description="Figure/Table 레이블 (예: Figure 3, Table 1)",
    )


# === Item 모델 ===


class Item(BaseModel):
    """Item 모델 (역할 3 출력)

    명세서 3.3장 참조:
    - 하나의 완결된 논의/처리 흐름
    - Agreement, Conclusion, Decision 중 하나 이상 포함

    id 형식: {meeting_id}_{leaf_id}_{sequence}
    예: RAN1_120_9.1.1_001
    """

    # 필수 필드
    id: str = Field(
        ...,
        description="Item 고유 식별자 (예: RAN1_120_9.1.1_001)",
    )
    context: ItemContext = Field(
        ...,
        description="맥락 정보",
    )
    resolution: Resolution = Field(
        ...,
        description="결과 정보",
    )

    # 선택 필드
    topic: Optional[Topic] = Field(
        default=None,
        description="기술 논의 주제",
    )
    input: Optional[Input] = Field(
        default=None,
        description="입력 문서 정보",
    )
    session_info: Optional[SessionInfo] = Field(
        default=None,
        description="세션 추적 정보",
    )
    cr_info: Optional[CRInfo] = Field(
        default=None,
        description="CR 정보",
    )
    tr_info: Optional[TRInfo] = Field(
        default=None,
        description="TR 정보",
    )
    ls_in: Optional[LSInInfo] = Field(
        default=None,
        description="Incoming LS 정보",
    )
    ls_out: Optional[LSOutInfo] = Field(
        default=None,
        description="Outgoing LS 정보",
    )
    media_refs: Optional[List[MediaRef]] = Field(
        default=None,
        description="미디어 참조 목록 (이미지/테이블이 포함된 경우)",
    )

    # 메타데이터 (언더스코어 prefix는 Pydantic에서 특별 취급되므로 별칭 사용)
    error: Optional[ErrorInfo] = Field(
        default=None,
        alias="_error",
        description="에러 정보",
    )
    processing: Optional[ProcessingInfo] = Field(
        default=None,
        alias="_processing",
        description="처리 메타데이터",
    )
    warning: Optional[WarningInfo] = Field(
        default=None,
        alias="_warning",
        description="경고 정보",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "RAN1_120_9.1.1_001",
                "context": {
                    "meeting_id": "RAN1_120",
                    "section_id": "9",
                    "leaf_id": "9.1.1",
                    "leaf_title": "Beam management",
                    "section_type": "Release",
                },
                "resolution": {
                    "status": "Agreed",
                    "content": [
                        {
                            "type": "agreement",
                            "text": "For Case 3b, support k = {0...5}",
                            "marker": "[Agreement]{.mark}",
                        }
                    ],
                },
                "topic": {"summary": "AI/ML positioning Case 3b 파라미터 결정"},
                "input": {"moderator_summary": "R1-2501410"},
            }
        }
