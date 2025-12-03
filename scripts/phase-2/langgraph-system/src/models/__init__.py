"""
Models for Phase-2 LangGraph System
"""

from .enums import (
    DecisionType,
    DocType,
    IssueType,
    OriginType,
    ProcessingStatus,
    ValidationLevel,
)
from .issue import (
    CCOnlyItem,
    Issue,
    Origin,
    SectionOutput,
    TdocRef,
)
from .maintenance_item import (
    # Ground Truth 형식 (신규)
    CRMetadata,
    IssueOrigin,
    MaintenanceIssue,
    TdocWithType,
    # 기존 호환성
    CRInfo,
    MaintenanceItem,
    MaintenanceSectionOutput,
    TopicSection,
)
from .section_types import (
    ParsedSection,
    Release,
    SectionClassification,
    SectionMetadata,
    SectionType,
    Technology,
)

__all__ = [
    # Enums
    "DecisionType",
    "DocType",
    "IssueType",
    "OriginType",
    "ProcessingStatus",
    "ValidationLevel",
    # Section Types (Step-2)
    "SectionType",
    "Technology",
    "Release",
    "SectionClassification",
    "SectionMetadata",
    "ParsedSection",
    # Issue Models (Step-1: Incoming LS)
    "TdocRef",
    "Origin",
    "Issue",
    "CCOnlyItem",
    "SectionOutput",
    # Maintenance Models - Ground Truth 형식 (Step-2)
    "TdocWithType",
    "IssueOrigin",
    "CRMetadata",
    "MaintenanceIssue",
    # Maintenance Models - 기존 호환성
    "CRInfo",
    "MaintenanceItem",
    "TopicSection",
    "MaintenanceSectionOutput",
]
