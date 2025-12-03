"""
Issue Data Models for Phase-2 LangGraph System

Incoming Liaison Statements 처리를 위한 핵심 데이터 모델
Note: 콘텐츠 기반 모델 - Section 번호에 종속되지 않음
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import DocType, IssueType, OriginType


@dataclass
class TdocRef:
    """Tdoc 참조 정보"""

    id: str  # R1-XXXXXXX
    title: Optional[str] = None
    companies: list[str] = field(default_factory=list)
    doc_type: Optional[DocType] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "companies": self.companies,
            "doc_type": str(self.doc_type) if self.doc_type else None,
        }

    def to_markdown(self) -> str:
        """Markdown 형식으로 출력"""
        parts = [f"- {self.id}"]
        if self.title:
            parts.append(f" — *{self.title}*")
        if self.companies:
            parts.append(f" ({', '.join(self.companies)})")
        if self.doc_type:
            parts.append(f" — `{self.doc_type}`")
        return "".join(parts)


@dataclass
class Origin:
    """Issue의 원본 정보"""

    type: OriginType  # LS, Maintenance, WorkItem
    section: str  # 섹션 번호

    # LS-specific fields
    ls_id: Optional[str] = None  # R1-XXXXXXX
    source_wg: Optional[str] = None  # RAN2, RAN3, etc.
    source_companies: list[str] = field(default_factory=list)

    # WorkItem-specific fields
    parent_section: Optional[str] = None  # 상위 섹션

    def to_dict(self) -> dict[str, Any]:
        result = {
            "type": str(self.type),
            "section": self.section,
        }
        if self.ls_id:
            result["ls_id"] = self.ls_id
        if self.source_wg:
            result["source_wg"] = self.source_wg
        if self.source_companies:
            result["source_companies"] = self.source_companies
        if self.parent_section:
            result["parent_section"] = self.parent_section
        return result

    def to_markdown(self) -> str:
        """Markdown 형식으로 출력"""
        lines = ["**Origin**"]
        lines.append(f"- Type: `{self.type}` (Section {self.section} — Incoming LS)")
        if self.ls_id:
            lines.append(f"- LS ID: {self.ls_id}")
        if self.source_wg:
            lines.append(f"- Source WG: {self.source_wg}")
        if self.source_companies:
            lines.append(f"- Source companies: [{', '.join(self.source_companies)}]")
        return "\n".join(lines)


@dataclass
class Issue:
    """Issue 데이터 모델 (Incoming LS용, Section 번호 무관)"""

    issue_id: str  # Issue_5_1, Issue_5_2, ...
    origin: Origin
    title: str
    summary_ko: str  # Korean 요약
    relevant_tdocs: list[TdocRef] = field(default_factory=list)
    decision: str = ""
    agenda_item: Optional[str] = None
    issue_type: IssueType = IssueType.NON_ACTION
    is_cc_only: bool = False  # CC-only Item 여부

    # 검증용 메타데이터
    confidence_score: float = 0.0
    validation_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "origin": self.origin.to_dict(),
            "title": self.title,
            "summary_ko": self.summary_ko,
            "relevant_tdocs": [t.to_dict() for t in self.relevant_tdocs],
            "decision": self.decision,
            "agenda_item": self.agenda_item,
            "issue_type": str(self.issue_type),
            "is_cc_only": self.is_cc_only,
            "confidence_score": self.confidence_score,
            "validation_notes": self.validation_notes,
        }

    def to_markdown(self) -> str:
        """Issue를 Markdown 형식으로 출력"""
        lines = []

        # Issue 제목
        issue_num = self.issue_id.split("_")[-1]  # Issue_5_1 -> 1
        lines.append(f"### Issue {issue_num}: {self.title}")
        lines.append("")

        # Origin
        lines.append(self.origin.to_markdown())
        lines.append("")

        # LS 정보 (Origin에 ls_id가 있으면)
        if self.origin.ls_id:
            lines.append("**LS**")
            ls_info = f"- {self.origin.ls_id}"
            if self.title:
                ls_info += f" — *{self.title}*"
            if self.origin.source_wg:
                ls_info += f" ({self.origin.source_wg}"
                if self.origin.source_companies:
                    ls_info += f", [{', '.join(self.origin.source_companies)}]"
                ls_info += ")"
            ls_info += " — `ls_incoming`"
            lines.append(ls_info)
            lines.append("")

        # Summary
        lines.append("**Summary**")
        lines.append(self.summary_ko)
        lines.append("")

        # Relevant Tdocs
        lines.append("**Relevant Tdocs**")
        if self.relevant_tdocs:
            for tdoc in self.relevant_tdocs:
                lines.append(tdoc.to_markdown())
        else:
            lines.append("- 없음")
        lines.append("")

        # Decision
        lines.append("**Decision**")
        lines.append(self.decision if self.decision else "- 없음")
        lines.append("")

        # Agenda Item
        lines.append("**Agenda Item**")
        lines.append(f"- {self.agenda_item}" if self.agenda_item else "- 없음")
        lines.append("")

        # Issue Type
        lines.append("**Issue Type**")
        lines.append(f"- {self.issue_type}")
        lines.append("")

        return "\n".join(lines)


@dataclass
class CCOnlyItem:
    """CC-only Item (해당 WG가 CC된 LS)"""

    ls_id: str
    title: str
    decision: str

    def to_markdown(self) -> str:
        """CC-only Item Markdown 출력"""
        lines = [
            f"#### {self.ls_id}: {self.title}",
            f"**Decision:** {self.decision}",
            "",
        ]
        return "\n".join(lines)


@dataclass
class SectionOutput:
    """Section 출력 데이터"""

    section_number: str
    meeting_number: str
    overview: str  # Section Overview (Korean)
    working_group: str = "RAN1"  # 동적 WG 지원 (기본값: RAN1)
    issues: list[Issue] = field(default_factory=list)
    cc_only_items: list[CCOnlyItem] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """전체 섹션을 Markdown으로 출력"""
        lines = []

        # 헤더 (동적 WG 지원)
        lines.append(
            f"# Section {self.section_number}: Incoming Liaison Statements ({self.working_group} #{self.meeting_number})"
        )
        lines.append("")

        # Section Overview
        lines.append("## Section Overview")
        lines.append("")
        lines.append(self.overview)
        lines.append("")

        # Statistics
        if self.statistics:
            lines.append("**Statistics:**")
            total_primary = self.statistics.get("total_primary", len(self.issues))
            total_cc = self.statistics.get("total_cc_only", len(self.cc_only_items))
            source_wgs = self.statistics.get("source_wgs", "")
            lines.append(f"- Total Primary LS Items: {total_primary}")
            lines.append(f"- CC-only Items: {total_cc}")
            if source_wgs:
                lines.append(f"- Source Working Groups: {source_wgs}")
            lines.append("")

            # Categories
            categories = self.statistics.get("categories", {})
            if categories:
                lines.append("**Categories:**")
                for cat, count in categories.items():
                    lines.append(f"- {cat}: {count}개")
                lines.append("")

        # Total Issues
        lines.append("---")
        lines.append("")
        lines.append(f"**Total: {len(self.issues)} Issues**")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Issues
        for issue in self.issues:
            lines.append(issue.to_markdown())
            lines.append("---")
            lines.append("")

        # CC-only Items (동적 WG 지원)
        if self.cc_only_items:
            lines.append(f"### {self.working_group} was cc-ed in the following incoming LSs")
            lines.append("")
            for item in self.cc_only_items:
                lines.append(item.to_markdown())

        return "\n".join(lines)
