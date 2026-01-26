"""
Role Extractor - Extract SessionNotes, FL Summary, Moderator Summary

Parses Normal-style paragraphs for role information (CQ4 support).
Pattern: TdocID \t Title \t Role (Company)
"""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from docx import Document

from models import RoleInfo, RoleType, SummaryType


# Pattern for TDoc ID
TDOC_ID_PATTERN = re.compile(r'^(R\d-\d{7})')

# Pattern for Session Notes
# Example: "R1-2302051	Session notes for 6 (...)	Ad-hoc Chair (CMCC)"
# Note: Use [^\t]+ to match until tab, then role pattern at end
SESSION_NOTES_PATTERN = re.compile(
    r'^(R\d-\d{7})\s+([Ss]ession [Nn]otes[^\t]+)\s+((?:Ad-?[Hh]oc\s*[Cc]hair|Moderator)\s*\([^)]+\))\s*$'
)

# Pattern for FL Summary
# Example: "R1-2302021	FL summary of SPS PDSCH...	Moderator (ZTE)"
FL_SUMMARY_PATTERN = re.compile(
    r'^(R\d-\d{7})\s+((?:FL|Feature [Ll]ead)\s+[Ss]ummary.+?)\s+(Moderator\s*\([^)]+\))\s*$'
)

# Pattern for Moderator Summary
# Example: "R1-2301906	Moderator Summary [112-R8~R16-LTE]	Moderator (Ericsson)"
MODERATOR_SUMMARY_PATTERN = re.compile(
    r'^(R\d-\d{7})\s+(Moderator\s+[Ss]ummary.+?)\s+(Moderator\s*\([^)]+\))\s*$'
)

# Pattern to extract company from role text
COMPANY_PATTERN = re.compile(r'\(([^)]+)\)')

# Pattern to extract agenda from title
AGENDA_FROM_TITLE_PATTERN = re.compile(
    r'(?:for|AI)\s+(\d+(?:\.\d+)*)',
    re.IGNORECASE
)

# Pattern to extract round number
ROUND_PATTERN = re.compile(r'#(\d+)')

# Template text to filter out (not actual TDocs)
TEMPLATE_FILTERS = [
    "To be used for sharing updates",
    "to be discussed in online/offline",
    "tdoc number of the moderator summary",
]


@dataclass
class RoleCandidate:
    """Candidate role information before full parsing."""
    tdoc_number: str
    title: str
    role_text: str
    paragraph_index: int


class RoleExtractor:
    """
    Extract role information from document paragraphs.

    Detects:
    - Session Notes (Ad-hoc Chair)
    - FL Summary (Moderator)
    - Moderator Summary (Moderator)
    """

    def __init__(self, meeting_id: str):
        """
        Initialize extractor.

        Args:
            meeting_id: Meeting ID for context
        """
        self.meeting_id = meeting_id
        self._seen_tdocs: set[str] = set()  # For deduplication

    def extract_roles(
        self,
        paragraphs: list
    ) -> tuple[list[RoleInfo], list[RoleInfo], list[RoleInfo]]:
        """
        Extract all role information from paragraphs.

        Args:
            paragraphs: List of docx paragraphs

        Returns:
            Tuple of (session_notes, fl_summaries, moderator_summaries)
        """
        session_notes = []
        fl_summaries = []
        moderator_summaries = []

        for idx, para in enumerate(paragraphs):
            style = para.style.name.lower() if para.style else ""

            # Only process Normal style paragraphs
            if style != 'normal':
                continue

            text = para.text.strip()

            # Skip if doesn't start with TDoc ID
            if not TDOC_ID_PATTERN.match(text):
                continue

            # Skip template text
            if self._is_template_text(text):
                continue

            # Try each pattern
            role_info = self._try_session_notes(text, idx)
            if role_info:
                if self._add_if_unique(role_info):
                    session_notes.append(role_info)
                continue

            role_info = self._try_fl_summary(text, idx)
            if role_info:
                if self._add_if_unique(role_info):
                    fl_summaries.append(role_info)
                continue

            role_info = self._try_moderator_summary(text, idx)
            if role_info:
                if self._add_if_unique(role_info):
                    moderator_summaries.append(role_info)

        return session_notes, fl_summaries, moderator_summaries

    def _is_template_text(self, text: str) -> bool:
        """Check if text is template/boilerplate."""
        text_lower = text.lower()
        return any(template.lower() in text_lower for template in TEMPLATE_FILTERS)

    def _add_if_unique(self, role_info: RoleInfo) -> bool:
        """Add role if not duplicate. Returns True if added."""
        key = (role_info.tdoc_number, self.meeting_id)
        if key in self._seen_tdocs:
            return False
        self._seen_tdocs.add(key)
        return True

    def _try_session_notes(self, text: str, para_index: int) -> Optional[RoleInfo]:
        """Try to parse as Session Notes."""
        match = SESSION_NOTES_PATTERN.match(text)
        if not match:
            return None

        tdoc_number = match.group(1)
        title = match.group(2).strip()
        role_text = match.group(3)

        company = self._extract_company(role_text)
        agenda = self._extract_agenda(title)

        return RoleInfo(
            tdoc_number=tdoc_number,
            meeting_id=self.meeting_id,
            title=title,
            role_type=RoleType.SESSION_NOTES,
            agenda_item=agenda,
            company=company,
            paragraph_index=para_index,
        )

    def _try_fl_summary(self, text: str, para_index: int) -> Optional[RoleInfo]:
        """Try to parse as FL Summary."""
        match = FL_SUMMARY_PATTERN.match(text)
        if not match:
            return None

        tdoc_number = match.group(1)
        title = match.group(2).strip()
        role_text = match.group(3)

        company = self._extract_company(role_text)
        agenda = self._extract_agenda(title)
        round_number = self._extract_round(title)

        return RoleInfo(
            tdoc_number=tdoc_number,
            meeting_id=self.meeting_id,
            title=title,
            role_type=RoleType.FL_SUMMARY,
            agenda_item=agenda,
            company=company,
            paragraph_index=para_index,
            summary_type=SummaryType.FL,
            round_number=round_number,
        )

    def _try_moderator_summary(self, text: str, para_index: int) -> Optional[RoleInfo]:
        """Try to parse as Moderator Summary."""
        match = MODERATOR_SUMMARY_PATTERN.match(text)
        if not match:
            return None

        tdoc_number = match.group(1)
        title = match.group(2).strip()
        role_text = match.group(3)

        company = self._extract_company(role_text)
        agenda = self._extract_agenda(title)
        round_number = self._extract_round(title)

        return RoleInfo(
            tdoc_number=tdoc_number,
            meeting_id=self.meeting_id,
            title=title,
            role_type=RoleType.MODERATOR_SUMMARY,
            agenda_item=agenda,
            company=company,
            paragraph_index=para_index,
            summary_type=SummaryType.MODERATOR,
            round_number=round_number,
        )

    def _extract_company(self, role_text: str) -> str:
        """Extract company name from role text like 'Moderator (ZTE)'."""
        match = COMPANY_PATTERN.search(role_text)
        if match:
            return match.group(1).strip()
        return "UNKNOWN"

    def _extract_agenda(self, title: str) -> str:
        """Extract agenda number from title."""
        match = AGENDA_FROM_TITLE_PATTERN.search(title)
        if match:
            return match.group(1)
        return "UNKNOWN"

    def _extract_round(self, title: str) -> Optional[int]:
        """Extract round number from title like 'FL summary #1'."""
        match = ROUND_PATTERN.search(title)
        if match:
            return int(match.group(1))
        return None


def extract_roles_from_docx(
    docx_path: Path,
    meeting_id: str
) -> tuple[list[RoleInfo], list[RoleInfo], list[RoleInfo]]:
    """
    Extract role information from a DOCX file.

    Args:
        docx_path: Path to DOCX file
        meeting_id: Meeting ID

    Returns:
        Tuple of (session_notes, fl_summaries, moderator_summaries)
    """
    doc = Document(docx_path)
    extractor = RoleExtractor(meeting_id)
    return extractor.extract_roles(doc.paragraphs)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python role_extractor.py <docx_path>")
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    meeting_id = "RAN1#" + docx_path.stem.split('-')[-1].replace('_hybrid', '')

    session_notes, fl_summaries, mod_summaries = extract_roles_from_docx(docx_path, meeting_id)

    print(f"Extracted from {docx_path.name}:")
    print(f"  Session Notes: {len(session_notes)}")
    print(f"  FL Summaries: {len(fl_summaries)}")
    print(f"  Moderator Summaries: {len(mod_summaries)}")

    print("\nSample Session Notes:")
    for sn in session_notes[:3]:
        print(f"  {sn.tdoc_number}: {sn.title[:50]}... -> {sn.company}")

    print("\nSample FL Summaries:")
    for fl in fl_summaries[:3]:
        print(f"  {fl.tdoc_number}: {fl.title[:50]}... -> {fl.company}")
