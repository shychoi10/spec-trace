"""
Enums for Phase-2 LangGraph System

모든 열거형 타입 정의
"""

from enum import Enum


class DocType(str, Enum):
    """문서 타입 (LLM이 분류)

    Ground Truth 기반 확장된 분류 체계:
    - CR 관련: cr_draft, cr_final
    - LS 관련: ls_incoming, ls_draft, ls_final, ls_reply_draft
    - Summary 관련: summary, summary_final
    - 기타: discussion, session_notes, report, other
    """

    # CR (Change Request)
    CR_DRAFT = "cr_draft"  # Draft CR
    CR_FINAL = "cr_final"  # Final approved CR

    # LS (Liaison Statement)
    LS_INCOMING = "ls_incoming"  # Incoming LS from other WGs
    LS_DRAFT = "ls_draft"  # Draft outgoing LS
    LS_FINAL = "ls_final"  # Final approved LS
    LS_REPLY_DRAFT = "ls_reply_draft"  # Draft reply to LS

    # Summary (Moderator)
    SUMMARY = "summary"  # Moderator summary
    SUMMARY_FINAL = "summary_final"  # Final moderator summary

    # Discussion & Others
    DISCUSSION = "discussion"  # Discussion paper
    SESSION_NOTES = "session_notes"  # Session moderator notes
    REPORT = "report"  # Report document
    UE_FEATURE_LIST = "ue_feature_list"  # UE feature list document
    OTHER = "other"  # 분류 불가

    def __str__(self) -> str:
        return self.value


class IssueType(str, Enum):
    """Issue 타입 (LLM이 분류)

    Incoming LS용 (기존):
    - ACTIONABLE, NON_ACTION, REFERENCE

    Maintenance용 (Ground Truth 기반 확장):
    - SPEC_CHANGE_FINAL_CR: 최종 CR 승인으로 Spec 변경
    - SPEC_CHANGE_ALIGNMENT_CR: Alignment CR로 Spec 변경
    - CLOSED_NOT_PURSUED: 논의 후 CR 미추진으로 종료
    - CLARIFICATION_NO_CR: Clarification만 (CR 없음)
    - OPEN_INCONCLUSIVE: 합의 없이 미결로 종료
    - LS_REPLY_ISSUE: LS Reply로 처리된 이슈
    - UE_FEATURE_DEFINITION: UE Feature 정의
    - UE_FEATURE_CLARIFICATION: UE Feature 해석 명확화
    """

    # Incoming LS용 (기존 유지 - 호환성)
    ACTIONABLE = "Actionable Issue"  # WG 액션 필요
    NON_ACTION = "Non-action Issue"  # 액션 불필요
    REFERENCE = "Reference Issue"  # 참조용 (CC)

    # Maintenance용 (Ground Truth 기반)
    SPEC_CHANGE_FINAL_CR = "SpecChange_FinalCR"  # Final CR 승인
    SPEC_CHANGE_ALIGNMENT_CR = "SpecChange_AlignmentCR"  # Alignment CR
    CLOSED_NOT_PURSUED = "Closed_Not_Pursued"  # Not pursued로 종료
    CLARIFICATION_NO_CR = "Clarification_NoCR"  # Clarification만
    OPEN_INCONCLUSIVE = "Open_Inconclusive"  # 미결 종료
    LS_REPLY_ISSUE = "LS_Reply_Issue"  # LS Reply 처리
    LS_REPLY_PARTIAL_CONSENSUS = "LS_Reply_Issue_PartialConsensus"  # 부분 합의 LS
    UE_FEATURE_DEFINITION = "UE_Feature_Definition"  # UE Feature 정의
    UE_FEATURE_CLARIFICATION = "UE_Feature_Clarification"  # UE Feature 명확화
    UE_FEATURE_LIST_CONSOLIDATION = "UE_Feature_List_Consolidation"  # UE Feature 통합

    def __str__(self) -> str:
        return self.value


class OriginType(str, Enum):
    """Origin 타입

    Ground Truth 기반 확장:
    - LS: Incoming LS 기반 이슈
    - INTERNAL_MAINTENANCE: 내부 유지보수 이슈
    - FROM_LS: LS에서 파생된 Maintenance 이슈
    """

    LS = "LS"  # Liaison Statement (Section 5)
    INTERNAL_MAINTENANCE = "Internal_Maintenance"  # Internal maintenance issue
    FROM_LS = "From_LS"  # Maintenance issue from LS
    WORK_ITEM = "WorkItem"  # Work Item
    ACTION_ITEM = "ActionItem"  # Action Item

    def __str__(self) -> str:
        return self.value


class ProcessingStatus(str, Enum):
    """처리 상태"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

    def __str__(self) -> str:
        return self.value


class ValidationLevel(str, Enum):
    """검증 레벨"""

    STAGE = "stage"  # Sub-Agent 출력 검증
    AGENT = "agent"  # Section Agent 출력 검증
    DOCUMENT = "document"  # 전체 문서 검증
    GROUND_TRUTH = "ground_truth"  # Ground Truth 비교

    def __str__(self) -> str:
        return self.value


class DecisionType(str, Enum):
    """Decision 타입 (Maintenance 섹션용)

    3GPP 미팅에서의 결정 유형:
    - Agreement: 합의 (기술적 내용에 대한 동의)
    - Decision: 결정 (절차적 사항에 대한 결정)
    - Conclusion: 결론 (논의 결과)
    - Other: 기타 또는 분류 불가
    """

    AGREEMENT = "Agreement"
    DECISION = "Decision"
    CONCLUSION = "Conclusion"
    OTHER = "Other"

    def __str__(self) -> str:
        return self.value
