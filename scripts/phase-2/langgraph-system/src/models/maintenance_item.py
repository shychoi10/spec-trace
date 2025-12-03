"""
Maintenance Item Data Models for Phase-2 LangGraph System

Ground Truth 형식에 맞춘 Maintenance Section 처리 데이터 모델
Note: 콘텐츠 기반 모델 - Section 번호에 종속되지 않음
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import DecisionType, DocType, IssueType, OriginType


@dataclass
class TdocWithType:
    """Tdoc with doc_type 분류

    Ground Truth 예시:
    - `R1-2500143` – *Draft CR on DCI size alignment* (ZTE, Sanechips) – `cr_draft`
    """

    tdoc_id: str  # R1-2500143
    title: str  # Draft CR on DCI size alignment
    source: str  # ZTE, Sanechips
    doc_type: DocType  # cr_draft, summary, discussion 등

    def to_dict(self) -> dict[str, Any]:
        return {
            "tdoc_id": self.tdoc_id,
            "title": self.title,
            "source": self.source,
            "doc_type": str(self.doc_type),
        }

    def to_markdown(self) -> str:
        """Ground Truth 형식: `R1-25xxxxx` – *Title* (Source) – `doc_type`"""
        return f"- `{self.tdoc_id}` – *{self.title}* ({self.source}) – `{self.doc_type}`"


@dataclass
class IssueOrigin:
    """Issue Origin 블록

    Ground Truth 형식:
    **Origin**
    - Type: `Internal_Maintenance`
    - Section: `7 — Pre-Rel-18 NR`
    - Topic: `MIMO`
    - from_LS: R1-2500012 (if applicable)
    """

    type: OriginType  # Internal_Maintenance, From_LS
    section: str  # "7 — Pre-Rel-18 NR", "8.1 — Rel-18 MIMO"
    topic: Optional[str] = None  # MIMO, DSS, Coverage Enhancement
    from_ls: Optional[str] = None  # R1-2500012 (if From_LS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": str(self.type),
            "section": self.section,
            "topic": self.topic,
            "from_ls": self.from_ls,
        }

    def to_markdown(self) -> str:
        """Origin 블록 Markdown 출력"""
        lines = ["**Origin**", ""]
        lines.append(f"- Type: `{self.type}`")
        lines.append(f"- Section: `{self.section}`")
        if self.topic:
            lines.append(f"- Topic: `{self.topic}`")
        if self.from_ls:
            lines.append(f"- from_LS: {self.from_ls}")
        return "\n".join(lines)


@dataclass
class CRMetadata:
    """CR/Spec 메타데이터

    Ground Truth 형식:
    **CR / Spec 메타**
    - Release: **Rel-17**
    - Spec: **TS 38.214**
    - Work Item: `NR_MIMO_evo_DL_UL-Core`
    - CR: `CR0655`
    - Category: Cat F
    """

    release: str  # Rel-17, Rel-18
    spec: Optional[str] = None  # TS 38.211, TS 38.214
    work_item: Optional[str] = None  # NR_MIMO_evo_DL_UL-Core
    cr_id: Optional[str] = None  # CR0655
    category: Optional[str] = None  # Cat A, Cat F
    tdoc_id: Optional[str] = None  # R1-2501564 (Final CR tdoc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "spec": self.spec,
            "work_item": self.work_item,
            "cr_id": self.cr_id,
            "category": self.category,
            "tdoc_id": self.tdoc_id,
        }

    def to_markdown(self) -> str:
        """CR/Spec 메타 Markdown 출력"""
        lines = ["**CR / Spec 메타**", ""]
        lines.append(f"- Release: **{self.release}**")
        if self.spec:
            lines.append(f"- Spec: **{self.spec}**")
        if self.work_item:
            lines.append(f"- Work Item: `{self.work_item}`")
        if self.cr_id:
            lines.append(f"- CR: `{self.cr_id}`")
        if self.category:
            lines.append(f"- Category: {self.category}")
        if self.tdoc_id:
            lines.append(f"- Tdoc: {self.tdoc_id}")
        return "\n".join(lines)


@dataclass
class MaintenanceIssue:
    """Maintenance Issue (Ground Truth 형식)

    Ground Truth Issue Block 구조 완전 구현:
    - Origin
    - Draft/Discussion Tdocs
    - Moderator Summaries
    - LS 관련 Tdocs (if applicable)
    - Final CRs (if applicable)
    - Summary
    - Decision/Agreement
    - CR/Spec 메타
    - Agenda Item
    - Issue Type
    """

    # 필수 필드
    issue_title: str  # Issue 제목
    origin: IssueOrigin  # Origin 블록

    # Tdocs 분류별
    draft_discussion_tdocs: list[TdocWithType] = field(default_factory=list)
    moderator_summaries: list[TdocWithType] = field(default_factory=list)
    ls_related_tdocs: list[TdocWithType] = field(default_factory=list)
    final_crs: list[TdocWithType] = field(default_factory=list)

    # Summary (한국어)
    summary_ko: str = ""

    # Decision/Agreement
    decision_text: str = ""  # 원문 (영문)
    decision_type: Optional[DecisionType] = None

    # CR/Spec 메타 (여러 개 가능: Rel-17 + Rel-18 동시 CR)
    cr_metadata: list[CRMetadata] = field(default_factory=list)

    # Agenda Item
    agenda_item: str = ""  # "MIMO (Section 7)", "8.1 — Coverage Enhancement"

    # Issue Type
    issue_type: Optional[IssueType] = None

    # 메타데이터
    confidence_score: float = 0.0
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_title": self.issue_title,
            "origin": self.origin.to_dict(),
            "draft_discussion_tdocs": [t.to_dict() for t in self.draft_discussion_tdocs],
            "moderator_summaries": [t.to_dict() for t in self.moderator_summaries],
            "ls_related_tdocs": [t.to_dict() for t in self.ls_related_tdocs],
            "final_crs": [t.to_dict() for t in self.final_crs],
            "summary_ko": self.summary_ko,
            "decision_text": self.decision_text,
            "decision_type": str(self.decision_type) if self.decision_type else None,
            "cr_metadata": [cr.to_dict() for cr in self.cr_metadata],
            "agenda_item": self.agenda_item,
            "issue_type": str(self.issue_type) if self.issue_type else None,
            "confidence_score": self.confidence_score,
        }

    def to_markdown(self) -> str:
        """Ground Truth 형식 Markdown 출력"""
        lines = []

        # Issue 제목
        lines.append(f"### Issue: {self.issue_title}")
        lines.append("")

        # Origin
        lines.append(self.origin.to_markdown())
        lines.append("")

        # Draft / Discussion Tdocs
        if self.draft_discussion_tdocs:
            lines.append("**Draft / Discussion Tdocs**")
            lines.append("")
            for tdoc in self.draft_discussion_tdocs:
                lines.append(tdoc.to_markdown())
            lines.append("")

        # Moderator Summaries
        if self.moderator_summaries:
            lines.append("**Moderator Summaries**")
            lines.append("")
            for tdoc in self.moderator_summaries:
                lines.append(tdoc.to_markdown())
            lines.append("")

        # LS 관련 Tdocs
        if self.ls_related_tdocs:
            lines.append("**LS 관련 Tdocs**")
            lines.append("")
            for tdoc in self.ls_related_tdocs:
                lines.append(tdoc.to_markdown())
            lines.append("")

        # Final CRs
        if self.final_crs:
            lines.append("**Final CRs**")
            lines.append("")
            for tdoc in self.final_crs:
                lines.append(tdoc.to_markdown())
            lines.append("")

        # Summary
        if self.summary_ko:
            lines.append("**Summary**")
            lines.append("")
            lines.append(self.summary_ko)
            lines.append("")

        # Decision / Agreement
        if self.decision_text:
            lines.append("**Decision / Agreement**")
            lines.append("")
            lines.append(self.decision_text)
            lines.append("")

        # CR / Spec 메타
        if self.cr_metadata:
            for cr_meta in self.cr_metadata:
                lines.append(cr_meta.to_markdown())
                lines.append("")

        # Agenda Item
        if self.agenda_item:
            lines.append("**Agenda Item**")
            lines.append("")
            lines.append(f"- {self.agenda_item}")
            lines.append("")

        # Issue Type
        if self.issue_type:
            lines.append("**Issue Type**")
            lines.append("")
            lines.append(f"- `{self.issue_type}`")
            lines.append("")

        return "\n".join(lines)


# ============================================================
# 기존 호환성을 위한 클래스 (Backward Compatibility)
# ============================================================


@dataclass
class CRInfo:
    """CR(Change Request) 정보 (기존 호환성)"""

    cr_id: str  # CR0656
    spec: str  # 38.214
    release: str  # Rel-18
    category: str  # Cat F, Cat A

    def to_dict(self) -> dict[str, Any]:
        return {
            "cr_id": self.cr_id,
            "spec": self.spec,
            "release": self.release,
            "category": self.category,
        }

    def to_markdown(self) -> str:
        """CR 정보 Markdown 출력"""
        return f"- CR: {self.cr_id} ({self.spec}, {self.release}, {self.category})"


@dataclass
class MaintenanceItem:
    """Maintenance Item 데이터 모델 (기존 호환성)"""

    item_number: int
    topic: str  # MIMO, Network Energy Savings 등
    tdoc_id: str  # R1-2500200

    # 메타데이터
    title: str
    source: str  # 회사명 (ZTE Corporation, CATT 등)
    decision_type: DecisionType  # Agreement/Decision/Conclusion
    decision_text: str

    # CR 정보 (있는 경우)
    cr_info: Optional[CRInfo] = None

    # 관련 TDocs
    related_tdocs: list[str] = field(default_factory=list)

    # 요약
    summary_ko: str = ""  # Korean summary

    # 검증용 메타데이터
    confidence_score: float = 0.0
    raw_text: str = ""  # 원본 텍스트

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_number": self.item_number,
            "topic": self.topic,
            "tdoc_id": self.tdoc_id,
            "title": self.title,
            "source": self.source,
            "decision_type": str(self.decision_type),
            "decision_text": self.decision_text,
            "cr_info": self.cr_info.to_dict() if self.cr_info else None,
            "related_tdocs": self.related_tdocs,
            "summary_ko": self.summary_ko,
            "confidence_score": self.confidence_score,
        }

    def to_markdown(self) -> str:
        """Item을 Markdown 형식으로 출력"""
        lines = []

        # Item 제목
        lines.append(f"#### Item {self.item_number}: {self.title}")
        lines.append("")

        # TDoc 정보
        lines.append(f"**TDoc**: {self.tdoc_id}")
        lines.append(f"**Source**: {self.source}")
        lines.append(f"**Decision Type**: {self.decision_type}")
        lines.append("")

        # Summary
        if self.summary_ko:
            lines.append("**Summary**")
            lines.append(self.summary_ko)
            lines.append("")

        # Related TDocs
        if self.related_tdocs:
            lines.append("**Related TDocs**")
            for tdoc in self.related_tdocs:
                lines.append(f"- {tdoc}")
            lines.append("")

        # Decision
        lines.append("**Decision**")
        lines.append(self.decision_text if self.decision_text else "- 없음")
        lines.append("")

        # CR Information
        if self.cr_info:
            lines.append("**CR Information**")
            lines.append(f"- CR ID: {self.cr_info.cr_id}")
            lines.append(f"- Spec: {self.cr_info.spec}")
            lines.append(f"- Release: {self.cr_info.release}")
            lines.append(f"- Category: {self.cr_info.category}")
            lines.append("")

        return "\n".join(lines)


@dataclass
class TopicSection:
    """Topic 섹션 (MIMO, NES 등)"""

    name: str
    items: list[MaintenanceItem] = field(default_factory=list)

    # Ground Truth 형식 Issues
    issues: list[MaintenanceIssue] = field(default_factory=list)

    # 통계
    total_items: int = 0
    total_agreements: int = 0
    total_decisions: int = 0
    total_conclusions: int = 0
    crs_approved: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Topic 섹션 Markdown 출력"""
        lines = []

        # Topic 제목
        lines.append(f"## {self.name}")
        lines.append("")

        # Ground Truth 형식 Issues (우선)
        if self.issues:
            for issue in self.issues:
                lines.append(issue.to_markdown())
                lines.append("---")
                lines.append("")
        # 기존 Items (fallback)
        elif self.items:
            for item in self.items:
                lines.append(item.to_markdown())
                lines.append("---")
                lines.append("")

        return "\n".join(lines)


@dataclass
class MaintenanceSectionOutput:
    """Maintenance Section 출력 데이터"""

    section_title: str  # "Maintenance on Release 18"
    meeting_number: str
    working_group: str = "RAN1"
    release: str = "Rel-18"
    technology: Optional[str] = None  # NR, E-UTRA

    # Overview
    overview: str = ""

    # Topics
    topics: list[TopicSection] = field(default_factory=list)

    # Ground Truth 형식: Topic 없이 Issues만 있는 경우
    issues: list[MaintenanceIssue] = field(default_factory=list)

    # 통계
    statistics: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """전체 섹션을 Markdown으로 출력"""
        lines = []

        # 헤더
        lines.append(
            f"# {self.section_title} ({self.working_group} #{self.meeting_number})"
        )
        lines.append("")

        # Section Overview
        lines.append("## Section Overview")
        lines.append("")
        if self.overview:
            lines.append(self.overview)
            lines.append("")

        # Statistics
        if self.statistics:
            lines.append("**Statistics:**")
            lines.append(f"- Total Items: {self.statistics.get('total_items', 0)}")
            lines.append(f"- Topics: {self.statistics.get('total_topics', 0)}")
            lines.append(f"- Agreements: {self.statistics.get('total_agreements', 0)}")
            lines.append(f"- Decisions: {self.statistics.get('total_decisions', 0)}")
            lines.append(f"- CRs Approved: {self.statistics.get('crs_approved', 0)}")

            specs_affected = self.statistics.get("specs_affected", [])
            if specs_affected:
                lines.append(f"- Specs Affected: {', '.join(specs_affected)}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Topics
        for topic in self.topics:
            lines.append(topic.to_markdown())

        # Direct Issues (Topic 없이)
        for issue in self.issues:
            lines.append(issue.to_markdown())
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
