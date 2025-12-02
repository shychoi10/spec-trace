"""
Enums for Phase-2 LangGraph System

모든 열거형 타입 정의
"""

from enum import Enum


class DocType(str, Enum):
    """문서 타입 (LLM이 분류)"""

    LS_INCOMING = "ls_incoming"  # Incoming Liaison Statement
    LS_REPLY_DRAFT = "ls_reply_draft"  # Draft reply to LS
    DISCUSSION = "discussion"  # Discussion paper
    SESSION_NOTES = "session_notes"  # Session moderator notes
    CR = "cr"  # Change Request
    CR_DRAFT = "cr_draft"  # Draft CR
    REPORT = "report"  # Report document
    OTHER = "other"  # 분류 불가

    def __str__(self) -> str:
        return self.value


class IssueType(str, Enum):
    """Issue 타입 (LLM이 분류)"""

    ACTIONABLE = "Actionable Issue"  # RAN1 액션 필요
    NON_ACTION = "Non-action Issue"  # 액션 불필요
    REFERENCE = "Reference Issue"  # 참조용 (CC)

    def __str__(self) -> str:
        return self.value


class OriginType(str, Enum):
    """Origin 타입"""

    LS = "LS"  # Liaison Statement
    MAINTENANCE = "Maintenance"  # Maintenance item
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
