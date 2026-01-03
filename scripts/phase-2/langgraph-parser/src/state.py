"""
ParserState 정의

LangGraph State 기반 파이프라인 상태 관리
명세서 2장 참조: 역할 간 의존 관계 및 데이터 흐름
"""

from operator import add
from typing import Annotated, Optional, TypedDict


class SectionResult(TypedDict):
    """섹션 처리 결과 (역할 3)

    Section Agent가 반환하는 결과 구조
    """

    section_id: str
    """Depth 1 섹션 번호"""

    title: str
    """섹션 제목"""

    section_type: str
    """섹션 타입 (Maintenance, Release, Study, UE_Features, LS, Annex)"""

    status: str
    """처리 상태 (completed, partial, failed, skipped)"""

    leaves: list[dict]
    """처리된 Leaf 섹션 목록"""

    items: list[dict]
    """추출된 Item 목록"""


class AnnexResult(TypedDict):
    """Annex 처리 결과 (역할 3)

    AnnexAgent가 반환하는 결과 구조
    """

    annex_id: str
    """Annex 식별자 (annex_b, annex_c1, annex_c2)"""

    title: str
    """Annex 제목"""

    entries: list[dict]
    """Annex 항목 목록"""

    status: str
    """처리 상태"""


class ErrorRecord(TypedDict):
    """에러 기록"""

    role: str
    """에러 발생 역할 (role_0, role_1, role_2, role_3, role_4)"""

    section_id: Optional[str]
    """에러 발생 섹션 (역할 3에서만)"""

    error_type: str
    """에러 유형"""

    error_message: str
    """에러 메시지"""

    timestamp: str
    """에러 발생 시각 (ISO 8601)"""


class WarningRecord(TypedDict):
    """경고 기록"""

    role: str
    """경고 발생 역할"""

    section_id: Optional[str]
    """경고 발생 섹션"""

    warning_type: str
    """경고 유형"""

    message: str
    """경고 메시지"""


class ParserState(TypedDict):
    """LangGraph 파이프라인 상태

    명세서 2.3장 참조: 역할 간 의존 관계
    - 역할 1: meeting_info 출력
    - 역할 2: toc 출력 (skip 정보 포함)
    - 역할 3: section_results, annex_results 출력
    - 역할 4: validation_result 출력
    """

    # === 입력 ===
    input_path: str
    """입력 .docx 파일 경로"""

    output_dir: str
    """출력 디렉토리 경로"""

    # === 역할 0 결과 (전처리) ===
    markdown_content: str
    """python-docx 변환된 Markdown 전체 내용 (서식 마커 포함)"""

    toc_raw: dict
    """python-docx에서 직접 추출한 TOC 구조 (Spec 4.0 toc_raw.yaml 형식)"""

    meeting_id: str
    """추출된 회의 ID (예: RAN1_120)"""

    # === 역할 1 결과 (메타데이터) ===
    meeting_info: Optional[dict]
    """회의 메타데이터 (MeetingInfo 직렬화)"""

    # === 역할 2 결과 (TOC) ===
    toc: Optional[list[dict]]
    """목차 정보 (TOCSection 목록 직렬화)"""

    # === 역할 3 결과 (섹션 처리) ===
    section_results: Annotated[list[SectionResult], add]
    """섹션별 처리 결과 (병렬 처리, 누적)"""

    annex_results: Annotated[list[AnnexResult], add]
    """Annex 처리 결과 (병렬 처리, 누적)"""

    # === 역할 4 결과 (검증) ===
    validation_result: Optional[dict]
    """검증 결과 (크로스체크 포함)"""

    # === 상태 관리 ===
    current_step: str
    """현재 실행 중인 역할 (role_0, role_1, role_2, role_3, role_4)"""

    errors: Annotated[list[ErrorRecord], add]
    """에러 기록 (누적)"""

    warnings: Annotated[list[WarningRecord], add]
    """경고 기록 (누적)"""


def create_initial_state(input_path: str, output_dir: str) -> ParserState:
    """초기 상태 생성

    Args:
        input_path: 입력 .docx 파일 경로
        output_dir: 출력 디렉토리 경로

    Returns:
        초기화된 ParserState
    """
    return ParserState(
        # 입력
        input_path=input_path,
        output_dir=output_dir,
        # 역할 0
        markdown_content="",
        toc_raw={},
        meeting_id="",
        # 역할 1
        meeting_info=None,
        # 역할 2
        toc=None,
        # 역할 3
        section_results=[],
        annex_results=[],
        # 역할 4
        validation_result=None,
        # 상태 관리
        current_step="init",
        errors=[],
        warnings=[],
    )
