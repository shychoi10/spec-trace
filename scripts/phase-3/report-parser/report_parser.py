"""
Report Parser - Main pipeline for parsing Final Reports

Orchestrates:
1. TOC parsing -> Agenda mapping
2. Section building with AgendaMatcher
3. Decision extraction
4. Role extraction
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import zipfile
import xml.etree.ElementTree as ET

from docx import Document
from docx.oxml.ns import qn

from models import ParsedReport, Section, TocEntry
from toc_parser import parse_toc_from_docx, parse_toc_from_docm
from agenda_matcher import AgendaMatcher, SectionBuilder
from decision_extractor import DecisionExtractor
from role_extractor import RoleExtractor


# Namespace for Word XML
WORD_NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}


class ReportParser:
    """
    Main parser for 3GPP Final Reports.

    Pipeline:
    1. Parse TOC -> Build agenda mapping
    2. Parse Headings -> Build sections with correct agenda
    3. Parse Decisions -> Extract Agreement/Conclusion/WA
    4. Parse Roles -> Extract SessionNotes/Summary
    """

    def __init__(self, docx_path: Path, meeting_id: Optional[str] = None):
        """
        Initialize parser.

        Args:
            docx_path: Path to DOCX/DOCM file
            meeting_id: Meeting ID (auto-detected if None)
        """
        self.docx_path = docx_path
        # Detect DOCM by content type, not just extension
        self.is_docm = self._is_docm_file(docx_path)

        # Auto-detect meeting ID from filename
        if meeting_id:
            self.meeting_id = meeting_id
        else:
            self.meeting_id = self._extract_meeting_id(docx_path)

    def _is_docm_file(self, path: Path) -> bool:
        """Check if file is DOCM by content type (handles misnamed files)."""
        if path.suffix.lower() == '.docm':
            return True

        # Check content type in ZIP
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                with zf.open('[Content_Types].xml') as f:
                    content = f.read().decode('utf-8')
                    return 'macroEnabled' in content
        except Exception:
            return False

    def parse(self) -> ParsedReport:
        """
        Parse the document and return ParsedReport.

        Returns:
            Complete ParsedReport with all extracted data
        """
        # Step 1: Parse TOC
        if self.is_docm:
            toc_entries = parse_toc_from_docm(self.docx_path)
        else:
            toc_entries = parse_toc_from_docx(self.docx_path)

        # Step 2: Build sections
        matcher = AgendaMatcher(toc_entries)
        sections = self._build_sections(matcher)

        # Step 3: Extract decisions
        agreements, conclusions, working_assumptions = self._extract_decisions(sections)

        # Step 4: Extract roles
        session_notes, fl_summaries, moderator_summaries = self._extract_roles()

        # Build result
        return ParsedReport(
            meeting_id=self.meeting_id,
            docx_path=str(self.docx_path),
            parsed_at=datetime.now().isoformat(),
            toc_entries=toc_entries,
            sections=sections,
            agreements=agreements,
            conclusions=conclusions,
            working_assumptions=working_assumptions,
            session_notes=session_notes,
            fl_summaries=fl_summaries,
            moderator_summaries=moderator_summaries,
        )

    def _build_sections(self, matcher: AgendaMatcher) -> list[Section]:
        """Build sections from document headings."""
        sections = []
        builder = SectionBuilder(matcher)

        if self.is_docm:
            paragraphs = self._get_docm_paragraphs()
        else:
            doc = Document(self.docx_path)
            paragraphs = [(p.text.strip(), p.style.name.lower() if p.style else "") for p in doc.paragraphs]

        for idx, (text, style) in enumerate(paragraphs):
            if style.startswith('heading'):
                # Extract level
                try:
                    level = int(style.split()[-1])
                except (ValueError, IndexError):
                    level = 1

                if 1 <= level <= 5:
                    section = builder.process_heading(text, level, idx)

                    # Update previous section's end index
                    if sections:
                        sections[-1].end_index = idx

                    sections.append(section)

        # Set last section's end index
        if sections:
            sections[-1].end_index = len(paragraphs)

        return sections

    def _extract_decisions(self, sections: list[Section]):
        """Extract decisions using sections for agenda mapping."""
        if self.is_docm:
            # For DOCM, we need special handling
            return self._extract_decisions_docm(sections)
        else:
            doc = Document(self.docx_path)
            extractor = DecisionExtractor(sections)
            return extractor.extract_decisions(doc.paragraphs, self.meeting_id)

    def _extract_decisions_docm(self, sections: list[Section]):
        """Extract decisions from DOCM file."""
        from decision_extractor import (
            DecisionExtractor, DECISION_PATTERNS_HEADER, DECISION_PATTERNS_INLINE,
            TDOC_PATTERN, FFS_PATTERN, TBD_PATTERN, ANNEX_PATTERN
        )
        from models import Decision, DecisionType

        paragraphs = self._get_docm_paragraphs_raw()
        extractor = DecisionExtractor(sections)

        # Find candidates (with Annex filtering and TOC skip)
        candidates = []
        in_annex = False
        for idx, (text, style) in enumerate(paragraphs):
            # Skip TOC entries (they may contain Annex references)
            if style.startswith('toc'):
                continue

            # Check for Annex start - only on headings, not TOC
            if ANNEX_PATTERN.match(text) and style.startswith('heading'):
                in_annex = True
                continue
            if in_annex:
                continue

            # Try header-only patterns first
            found = False
            for decision_type, pattern in DECISION_PATTERNS_HEADER.items():
                if pattern.match(text):
                    candidates.append((decision_type, idx, text, None))  # inline_content=None
                    found = True
                    break

            # Try inline patterns
            if not found:
                for decision_type, pattern in DECISION_PATTERNS_INLINE.items():
                    match = pattern.match(text)
                    if match:
                        inline_content = match.group(1).strip()
                        candidates.append((decision_type, idx, text, inline_content))
                        break

        # Extract content
        agreements = []
        conclusions = []
        working_assumptions = []
        counters = {}

        for i, (decision_type, keyword_idx, keyword_text, inline_content) in enumerate(candidates):
            # Find boundary
            next_idx = candidates[i + 1][1] if i + 1 < len(candidates) else len(paragraphs)

            # Find actual boundary (next keyword or heading or Annex)
            boundary = next_idx
            for idx in range(keyword_idx + 1, next_idx):
                text, style = paragraphs[idx]
                if style.startswith('heading'):
                    boundary = idx
                    break
                if ANNEX_PATTERN.match(text):
                    boundary = idx
                    break
                # Check header patterns
                for pattern in DECISION_PATTERNS_HEADER.values():
                    if pattern.match(text):
                        boundary = idx
                        break
                else:
                    # Check inline patterns
                    for pattern in DECISION_PATTERNS_INLINE.values():
                        if pattern.match(text):
                            boundary = idx
                            break
                    else:
                        continue
                    break
                break

            # Extract content (handle inline content)
            content_parts = []
            if inline_content:
                content_parts.append(inline_content)
            for idx in range(keyword_idx + 1, boundary):
                text, _ = paragraphs[idx]
                if text:
                    content_parts.append(text)
            content = '\n'.join(content_parts)

            if not content.strip():
                continue

            # Get agenda
            agenda = extractor._get_agenda_for_index(keyword_idx)

            # Generate ID
            counter_key = (decision_type, agenda)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            count = counters[counter_key]

            prefix = extractor._get_decision_prefix(decision_type)
            meeting_num = self.meeting_id.replace("RAN1#", "")
            decision_id = f"{prefix}-{meeting_num}-{agenda}-{count:03d}"

            decision = Decision(
                decision_id=decision_id,
                decision_type=decision_type,
                meeting_id=self.meeting_id,
                agenda_item=agenda,
                content=content,
                paragraph_index=keyword_idx,
                referenced_tdocs=TDOC_PATTERN.findall(content),
                has_ffs=bool(FFS_PATTERN.search(content)),
                has_tbd=bool(TBD_PATTERN.search(content)),
            )

            if decision_type == DecisionType.AGREEMENT:
                agreements.append(decision)
            elif decision_type == DecisionType.CONCLUSION:
                conclusions.append(decision)
            else:
                working_assumptions.append(decision)

        return agreements, conclusions, working_assumptions

    def _extract_roles(self):
        """Extract role information."""
        if self.is_docm:
            return self._extract_roles_docm()
        else:
            doc = Document(self.docx_path)
            extractor = RoleExtractor(self.meeting_id)
            return extractor.extract_roles(doc.paragraphs)

    def _extract_roles_docm(self):
        """Extract roles from DOCM file."""
        from role_extractor import (
            RoleExtractor, SESSION_NOTES_PATTERN, FL_SUMMARY_PATTERN,
            MODERATOR_SUMMARY_PATTERN, TDOC_ID_PATTERN, TEMPLATE_FILTERS,
            COMPANY_PATTERN, AGENDA_FROM_TITLE_PATTERN, ROUND_PATTERN
        )
        from models import RoleInfo, RoleType, SummaryType

        paragraphs = self._get_docm_paragraphs_raw()
        extractor = RoleExtractor(self.meeting_id)

        session_notes = []
        fl_summaries = []
        moderator_summaries = []
        seen = set()

        for idx, (text, style) in enumerate(paragraphs):
            if style != 'normal':
                continue

            if not TDOC_ID_PATTERN.match(text):
                continue

            # Skip templates
            text_lower = text.lower()
            if any(t.lower() in text_lower for t in TEMPLATE_FILTERS):
                continue

            # Try patterns
            role_info = None
            role_type = None

            match = SESSION_NOTES_PATTERN.match(text)
            if match:
                role_info = self._create_role_info(match, RoleType.SESSION_NOTES, idx)
                role_type = 'session_notes'

            if not role_info:
                match = FL_SUMMARY_PATTERN.match(text)
                if match:
                    role_info = self._create_role_info(match, RoleType.FL_SUMMARY, idx, SummaryType.FL)
                    role_type = 'fl_summaries'

            if not role_info:
                match = MODERATOR_SUMMARY_PATTERN.match(text)
                if match:
                    role_info = self._create_role_info(match, RoleType.MODERATOR_SUMMARY, idx, SummaryType.MODERATOR)
                    role_type = 'moderator_summaries'

            if role_info:
                key = (role_info.tdoc_number, self.meeting_id)
                if key not in seen:
                    seen.add(key)
                    if role_type == 'session_notes':
                        session_notes.append(role_info)
                    elif role_type == 'fl_summaries':
                        fl_summaries.append(role_info)
                    else:
                        moderator_summaries.append(role_info)

        return session_notes, fl_summaries, moderator_summaries

    def _create_role_info(self, match, role_type, idx, summary_type=None):
        """Create RoleInfo from regex match."""
        from role_extractor import COMPANY_PATTERN, AGENDA_FROM_TITLE_PATTERN, ROUND_PATTERN
        from models import RoleInfo

        tdoc_number = match.group(1)
        title = match.group(2).strip()
        role_text = match.group(3)

        company_match = COMPANY_PATTERN.search(role_text)
        company = company_match.group(1).strip() if company_match else "UNKNOWN"

        agenda_match = AGENDA_FROM_TITLE_PATTERN.search(title)
        agenda = agenda_match.group(1) if agenda_match else "UNKNOWN"

        round_match = ROUND_PATTERN.search(title)
        round_number = int(round_match.group(1)) if round_match else None

        return RoleInfo(
            tdoc_number=tdoc_number,
            meeting_id=self.meeting_id,
            title=title,
            role_type=role_type,
            agenda_item=agenda,
            company=company,
            paragraph_index=idx,
            summary_type=summary_type,
            round_number=round_number,
        )

    def _get_docm_paragraphs(self) -> list[tuple[str, str]]:
        """Get paragraphs from DOCM as (text, style) tuples."""
        return self._get_docm_paragraphs_raw()

    def _get_docm_paragraphs_raw(self) -> list[tuple[str, str]]:
        """Get raw paragraphs from DOCM file."""
        paragraphs = []

        with zipfile.ZipFile(self.docx_path, 'r') as zf:
            # Read styles
            style_map = {}
            try:
                with zf.open('word/styles.xml') as f:
                    styles_tree = ET.parse(f)
                    styles_root = styles_tree.getroot()

                    for style in styles_root.findall('.//w:style', WORD_NS):
                        style_id = style.get(qn('w:styleId'))
                        name_elem = style.find('w:name', WORD_NS)
                        if style_id and name_elem is not None:
                            style_map[style_id] = name_elem.get(qn('w:val'), '').lower()
            except KeyError:
                pass

            # Read document
            with zf.open('word/document.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()

            for para in root.findall('.//w:p', WORD_NS):
                # Get text
                text_parts = []
                for t in para.findall('.//w:t', WORD_NS):
                    if t.text:
                        text_parts.append(t.text)
                text = ''.join(text_parts).strip()

                # Get style
                style_name = 'normal'
                pPr = para.find('w:pPr', WORD_NS)
                if pPr is not None:
                    pStyle = pPr.find('w:pStyle', WORD_NS)
                    if pStyle is not None:
                        style_id = pStyle.get(qn('w:val'), '')
                        style_name = style_map.get(style_id, style_id.lower())

                paragraphs.append((text, style_name))

        return paragraphs

    def _extract_meeting_id(self, path: Path) -> str:
        """Extract meeting ID from filename."""
        stem = path.stem

        # Pattern: Final_Report_RAN1-84b or Final_Report_RAN1_84b
        import re
        match = re.search(r'RAN1[-_](\d+[a-z]?)', stem, re.IGNORECASE)
        if match:
            return f"RAN1#{match.group(1)}"

        # Fallback
        return f"RAN1#{stem}"


def parse_report(docx_path: Path, meeting_id: Optional[str] = None) -> ParsedReport:
    """
    Parse a Final Report.

    Args:
        docx_path: Path to DOCX/DOCM file
        meeting_id: Optional meeting ID

    Returns:
        ParsedReport with all extracted data
    """
    parser = ReportParser(docx_path, meeting_id)
    return parser.parse()


def save_report(report: ParsedReport, output_path: Path) -> None:
    """Save ParsedReport to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python report_parser.py <docx_path> [output_path]")
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"Parsing {docx_path.name}...")
    report = parse_report(docx_path)

    print(f"\nResults for {report.meeting_id}:")
    print(f"  TOC entries: {len(report.toc_entries)}")
    print(f"  Sections: {len(report.sections)}")
    print(f"  Agreements: {len(report.agreements)}")
    print(f"  Conclusions: {len(report.conclusions)}")
    print(f"  Working Assumptions: {len(report.working_assumptions)}")
    print(f"  Total Decisions: {report.total_decisions}")
    print(f"  Session Notes: {len(report.session_notes)}")
    print(f"  FL Summaries: {len(report.fl_summaries)}")
    print(f"  Moderator Summaries: {len(report.moderator_summaries)}")
    print(f"  Total Roles: {report.total_roles}")

    # Verify agenda numbers
    sample_decisions = report.agreements[:5]
    print(f"\nSample Agreements (agenda verification):")
    for d in sample_decisions:
        print(f"  {d.decision_id} -> agenda: {d.agenda_item}")

    if output_path:
        save_report(report, output_path)
        print(f"\nSaved to {output_path}")
