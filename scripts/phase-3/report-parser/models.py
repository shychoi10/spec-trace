"""
Phase-3 Report Parser Data Models

Defines data structures for TOC entries, sections, decisions, and role information.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class DecisionType(Enum):
    AGREEMENT = "Agreement"
    CONCLUSION = "Conclusion"
    WORKING_ASSUMPTION = "WorkingAssumption"


class RoleType(Enum):
    SESSION_NOTES = "SessionNotes"
    FL_SUMMARY = "FLSummary"
    MODERATOR_SUMMARY = "ModeratorSummary"


class SummaryType(Enum):
    FL = "FL"
    MODERATOR = "Moderator"


@dataclass
class TocEntry:
    """Table of Contents entry with agenda number and title."""
    agenda_number: str  # e.g., "8.1", "9.1.1.1"
    title: str  # e.g., "Maintenance on Further enhancements on MIMO"
    level: int  # 1-5, derived from toc style (toc 1 -> level 1)
    page_number: Optional[int] = None
    paragraph_index: int = 0  # Index in document


@dataclass
class Section:
    """Document section with agenda mapping."""
    agenda_number: str  # From TOC mapping
    title: str  # Heading text
    heading_level: int  # 1-5
    start_index: int  # Paragraph start index
    end_index: int  # Paragraph end index (exclusive)

    @property
    def paragraph_count(self) -> int:
        return self.end_index - self.start_index


@dataclass
class Decision:
    """Parsed decision (Agreement, Conclusion, or WorkingAssumption)."""
    decision_id: str  # e.g., "AGR-112-8.1-001"
    decision_type: DecisionType
    meeting_id: str  # e.g., "RAN1#112"
    agenda_item: str  # e.g., "8.1"
    content: str  # Decision content text
    paragraph_index: int  # Source paragraph index

    # Optional fields
    session_context: Optional[str] = None  # e.g., "Thursday session"
    note: Optional[str] = None
    has_ffs: bool = False  # For Further Study
    has_tbd: bool = False  # To Be Determined
    has_consensus: Optional[bool] = None  # For Conclusion only

    # References to Tdocs
    referenced_tdocs: list[str] = field(default_factory=list)  # e.g., ["R1-2302088"]


@dataclass
class RoleInfo:
    """Parsed role information (SessionNotes, Summary)."""
    tdoc_number: str  # e.g., "R1-2302051"
    meeting_id: str  # e.g., "RAN1#112"
    title: str  # Full title text
    role_type: RoleType
    agenda_item: str  # e.g., "8.2"
    company: str  # e.g., "CMCC", "ZTE"
    paragraph_index: int  # Source paragraph index

    # For Summary only
    summary_type: Optional[SummaryType] = None  # FL or Moderator
    round_number: Optional[int] = None  # e.g., 1, 2


@dataclass
class ParsedReport:
    """Complete parsed report for a single meeting."""
    meeting_id: str  # e.g., "RAN1#112"
    docx_path: str
    parsed_at: str  # ISO timestamp

    # TOC mapping
    toc_entries: list[TocEntry] = field(default_factory=list)

    # Sections
    sections: list[Section] = field(default_factory=list)

    # Decisions
    agreements: list[Decision] = field(default_factory=list)
    conclusions: list[Decision] = field(default_factory=list)
    working_assumptions: list[Decision] = field(default_factory=list)

    # Role information
    session_notes: list[RoleInfo] = field(default_factory=list)
    fl_summaries: list[RoleInfo] = field(default_factory=list)
    moderator_summaries: list[RoleInfo] = field(default_factory=list)

    # Statistics
    @property
    def total_decisions(self) -> int:
        return len(self.agreements) + len(self.conclusions) + len(self.working_assumptions)

    @property
    def total_roles(self) -> int:
        return len(self.session_notes) + len(self.fl_summaries) + len(self.moderator_summaries)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "meeting_id": self.meeting_id,
            "docx_path": self.docx_path,
            "parsed_at": self.parsed_at,
            "stats": {
                "toc_entries": len(self.toc_entries),
                "sections": len(self.sections),
                "agreements": len(self.agreements),
                "conclusions": len(self.conclusions),
                "working_assumptions": len(self.working_assumptions),
                "total_decisions": self.total_decisions,
                "session_notes": len(self.session_notes),
                "fl_summaries": len(self.fl_summaries),
                "moderator_summaries": len(self.moderator_summaries),
                "total_roles": self.total_roles,
            },
            "toc_entries": [
                {
                    "agenda_number": e.agenda_number,
                    "title": e.title,
                    "level": e.level,
                    "page_number": e.page_number,
                }
                for e in self.toc_entries
            ],
            "sections": [
                {
                    "agenda_number": s.agenda_number,
                    "title": s.title,
                    "heading_level": s.heading_level,
                    "start_index": s.start_index,
                    "end_index": s.end_index,
                }
                for s in self.sections
            ],
            "agreements": [self._decision_to_dict(d) for d in self.agreements],
            "conclusions": [self._decision_to_dict(d) for d in self.conclusions],
            "working_assumptions": [self._decision_to_dict(d) for d in self.working_assumptions],
            "session_notes": [self._role_to_dict(r) for r in self.session_notes],
            "fl_summaries": [self._role_to_dict(r) for r in self.fl_summaries],
            "moderator_summaries": [self._role_to_dict(r) for r in self.moderator_summaries],
        }

    def _decision_to_dict(self, d: Decision) -> dict:
        result = {
            "decision_id": d.decision_id,
            "decision_type": d.decision_type.value,
            "agenda_item": d.agenda_item,
            "content": d.content,
            "paragraph_index": d.paragraph_index,
            "referenced_tdocs": d.referenced_tdocs,
        }
        if d.session_context:
            result["session_context"] = d.session_context
        if d.note:
            result["note"] = d.note
        if d.has_ffs:
            result["has_ffs"] = True
        if d.has_tbd:
            result["has_tbd"] = True
        if d.has_consensus is not None:
            result["has_consensus"] = d.has_consensus
        return result

    def _role_to_dict(self, r: RoleInfo) -> dict:
        result = {
            "tdoc_number": r.tdoc_number,
            "title": r.title,
            "role_type": r.role_type.value,
            "agenda_item": r.agenda_item,
            "company": r.company,
            "paragraph_index": r.paragraph_index,
        }
        if r.summary_type:
            result["summary_type"] = r.summary_type.value
        if r.round_number:
            result["round_number"] = r.round_number
        return result
