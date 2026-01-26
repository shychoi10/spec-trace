"""
TOC Parser - Extract Agenda number to Title mapping from Table of Contents

Parses TOC entries (toc 1-5 styles) to build a mapping table:
  agenda_number -> title

This mapping is used to assign correct agenda numbers to Headings.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import zipfile
import xml.etree.ElementTree as ET

from docx import Document
from docx.oxml.ns import qn

from models import TocEntry


# Namespace for Word XML
WORD_NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}

# Pattern to extract agenda number, title, and page number from TOC text
# Examples:
#   "7.1	Maintenance of E-UTRA Releases 8 – 13	12"
#   "9.1.1.1	Multi-TRP enhancement	45"
#   "1Opening of the meeting7" (DOCM - no spaces)
TOC_PATTERN = re.compile(
    r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)$'
)

# Pattern for DOCM files where agenda/title/page might be concatenated
# Example: "1.1Call for IPR7" -> agenda=1.1, title=Call for IPR, page=7
TOC_PATTERN_CONCATENATED = re.compile(
    r'^(\d+(?:\.\d+)*)([A-Z][^0-9]+?)(\d+)$'
)

# Alternative pattern without page number (some edge cases)
TOC_PATTERN_NO_PAGE = re.compile(
    r'^(\d+(?:\.\d+)*)\s+(.+)$'
)


def parse_toc_from_docx(docx_path: Path) -> list[TocEntry]:
    """
    Parse TOC entries from a DOCX file.

    Args:
        docx_path: Path to the DOCX file

    Returns:
        List of TocEntry objects with agenda number, title, and level
    """
    doc = Document(docx_path)
    toc_entries = []

    for idx, para in enumerate(doc.paragraphs):
        style_name = para.style.name.lower() if para.style else ""

        # Check for TOC styles (toc 1, toc 2, ..., toc 5)
        if style_name.startswith('toc '):
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                continue

            if 1 <= level <= 5:
                text = para.text.strip()
                entry = _parse_toc_text(text, level, idx)
                if entry:
                    toc_entries.append(entry)

    return toc_entries


def parse_toc_from_docm(docm_path: Path) -> list[TocEntry]:
    """
    Parse TOC entries from a DOCM (macro-enabled) file using zipfile + XML.

    Args:
        docm_path: Path to the DOCM file

    Returns:
        List of TocEntry objects
    """
    toc_entries = []

    with zipfile.ZipFile(docm_path, 'r') as zf:
        # Read document.xml
        with zf.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()

        # Read styles.xml to get style names
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

        # Parse paragraphs
        for idx, para in enumerate(root.findall('.//w:p', WORD_NS)):
            # Get paragraph style
            pPr = para.find('w:pPr', WORD_NS)
            if pPr is None:
                continue

            pStyle = pPr.find('w:pStyle', WORD_NS)
            if pStyle is None:
                continue

            style_id = pStyle.get(qn('w:val'), '')
            style_name = style_map.get(style_id, style_id.lower())

            # Check for TOC styles
            if style_name.startswith('toc') or style_id.lower().startswith('toc'):
                # Extract level from style name
                level = _extract_toc_level(style_name) or _extract_toc_level(style_id.lower())
                if level is None or level < 1 or level > 5:
                    continue

                # Extract text
                text_parts = []
                for t in para.findall('.//w:t', WORD_NS):
                    if t.text:
                        text_parts.append(t.text)
                text = ''.join(text_parts).strip()

                entry = _parse_toc_text(text, level, idx)
                if entry:
                    toc_entries.append(entry)

    return toc_entries


def _extract_toc_level(style_name: str) -> Optional[int]:
    """Extract TOC level from style name like 'toc 2' or 'toc2'."""
    match = re.search(r'toc\s*(\d)', style_name)
    if match:
        return int(match.group(1))
    return None


def _parse_toc_text(text: str, level: int, para_index: int) -> Optional[TocEntry]:
    """
    Parse TOC text to extract agenda number, title, and page number.

    Args:
        text: Raw TOC text like "7.1	Maintenance of E-UTRA	12"
        level: TOC level (1-5)
        para_index: Paragraph index in document

    Returns:
        TocEntry if parsing successful, None otherwise
    """
    if not text:
        return None

    # Try pattern with page number (normal DOCX with tabs/spaces)
    match = TOC_PATTERN.match(text)
    if match:
        agenda_number = match.group(1)
        title = match.group(2).strip()
        page_number = int(match.group(3))

        return TocEntry(
            agenda_number=agenda_number,
            title=title,
            level=level,
            page_number=page_number,
            paragraph_index=para_index
        )

    # Try concatenated pattern (DOCM files where spaces are stripped)
    # Example: "1.1Call for IPR7" -> 1.1, "Call for IPR", 7
    match = TOC_PATTERN_CONCATENATED.match(text)
    if match:
        agenda_number = match.group(1)
        title = match.group(2).strip()
        page_number = int(match.group(3))

        return TocEntry(
            agenda_number=agenda_number,
            title=title,
            level=level,
            page_number=page_number,
            paragraph_index=para_index
        )

    # Try pattern without page number
    match = TOC_PATTERN_NO_PAGE.match(text)
    if match:
        agenda_number = match.group(1)
        title = match.group(2).strip()

        return TocEntry(
            agenda_number=agenda_number,
            title=title,
            level=level,
            page_number=None,
            paragraph_index=para_index
        )

    return None


def build_agenda_mapping(toc_entries: list[TocEntry]) -> dict[str, str]:
    """
    Build agenda number -> title mapping from TOC entries.

    Args:
        toc_entries: List of parsed TOC entries

    Returns:
        Dictionary mapping agenda number to title
    """
    return {entry.agenda_number: entry.title for entry in toc_entries}


def build_title_to_agenda_mapping(toc_entries: list[TocEntry]) -> dict[str, str]:
    """
    Build title -> agenda number mapping for Heading matching.

    Args:
        toc_entries: List of parsed TOC entries

    Returns:
        Dictionary mapping title to agenda number
    """
    return {entry.title: entry.agenda_number for entry in toc_entries}


if __name__ == "__main__":
    # Test with a sample file
    import sys

    if len(sys.argv) < 2:
        print("Usage: python toc_parser.py <docx_path>")
        sys.exit(1)

    docx_path = Path(sys.argv[1])

    if docx_path.suffix.lower() == '.docm':
        entries = parse_toc_from_docm(docx_path)
    else:
        entries = parse_toc_from_docx(docx_path)

    print(f"Found {len(entries)} TOC entries:")
    for entry in entries[:20]:  # Show first 20
        print(f"  [{entry.level}] {entry.agenda_number}: {entry.title[:50]}...")

    if len(entries) > 20:
        print(f"  ... and {len(entries) - 20} more")
