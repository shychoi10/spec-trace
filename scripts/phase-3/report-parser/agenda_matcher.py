"""
Agenda Matcher - Match Heading titles to Agenda numbers using TOC mapping

Implements 3-stage matching strategy:
1. Exact match: Heading title == TOC title
2. Prefix match: First N characters match (for truncation)
3. Fuzzy match: Levenshtein distance (for minor differences)
"""

import re
from typing import Optional
from difflib import SequenceMatcher

from models import TocEntry, Section


class AgendaMatcher:
    """
    Matches Heading titles to Agenda numbers using TOC mapping.

    Supports 3-stage matching:
    1. Exact match (97.3% of cases)
    2. Prefix match (for truncation)
    3. Fuzzy match (for punctuation differences)
    """

    def __init__(
        self,
        toc_entries: list[TocEntry],
        prefix_threshold: int = 40,
        fuzzy_threshold: float = 0.85
    ):
        """
        Initialize matcher with TOC entries.

        Args:
            toc_entries: List of TOC entries from toc_parser
            prefix_threshold: Minimum characters for prefix matching
            fuzzy_threshold: Minimum similarity ratio for fuzzy matching
        """
        self.toc_entries = toc_entries
        self.prefix_threshold = prefix_threshold
        self.fuzzy_threshold = fuzzy_threshold

        # Build lookup tables
        self._title_to_agenda: dict[str, str] = {}
        self._normalized_title_to_agenda: dict[str, str] = {}
        self._prefix_index: dict[str, list[tuple[str, str]]] = {}  # prefix -> [(title, agenda)]

        for entry in toc_entries:
            title = entry.title
            agenda = entry.agenda_number

            # Exact match table
            self._title_to_agenda[title] = agenda

            # Normalized match table (lowercase, strip punctuation)
            normalized = self._normalize_title(title)
            self._normalized_title_to_agenda[normalized] = agenda

            # Prefix index for efficient prefix matching
            prefix = title[:prefix_threshold].lower() if len(title) >= prefix_threshold else title.lower()
            if prefix not in self._prefix_index:
                self._prefix_index[prefix] = []
            self._prefix_index[prefix].append((title, agenda))

    def match(self, heading_title: str) -> Optional[str]:
        """
        Find agenda number for a heading title.

        Args:
            heading_title: The heading text to match

        Returns:
            Agenda number if found, None otherwise
        """
        if not heading_title:
            return None

        # Stage 1: Exact match
        if heading_title in self._title_to_agenda:
            return self._title_to_agenda[heading_title]

        # Stage 2: Normalized exact match
        normalized = self._normalize_title(heading_title)
        if normalized in self._normalized_title_to_agenda:
            return self._normalized_title_to_agenda[normalized]

        # Stage 3: Prefix match (for truncation cases)
        prefix_result = self._prefix_match(heading_title)
        if prefix_result:
            return prefix_result

        # Stage 4: Fuzzy match (for minor differences)
        fuzzy_result = self._fuzzy_match(heading_title)
        if fuzzy_result:
            return fuzzy_result

        return None

    def match_with_fallback(
        self,
        heading_title: str,
        parent_agenda: Optional[str] = None
    ) -> str:
        """
        Match with fallback to parent agenda or UNKNOWN.

        Args:
            heading_title: The heading text to match
            parent_agenda: Parent section's agenda number for inheritance

        Returns:
            Matched agenda number, parent agenda, or "UNKNOWN"
        """
        result = self.match(heading_title)
        if result:
            return result

        if parent_agenda:
            return parent_agenda

        return "UNKNOWN"

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison: lowercase, strip trailing punctuation."""
        normalized = title.lower().strip()
        # Remove trailing period, common difference
        normalized = normalized.rstrip('.')
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        return normalized

    def _prefix_match(self, heading_title: str) -> Optional[str]:
        """
        Find match using prefix comparison.

        Handles cases where heading is truncated compared to TOC.
        """
        heading_lower = heading_title.lower()

        # Check if any TOC title starts with heading
        for title, agenda in self._title_to_agenda.items():
            title_lower = title.lower()

            # Heading is prefix of TOC title
            if title_lower.startswith(heading_lower) and len(heading_lower) >= self.prefix_threshold:
                return agenda

            # TOC title is prefix of heading
            if heading_lower.startswith(title_lower) and len(title_lower) >= self.prefix_threshold:
                return agenda

        return None

    def _fuzzy_match(self, heading_title: str) -> Optional[str]:
        """
        Find match using fuzzy string comparison.

        Uses SequenceMatcher for similarity ratio.
        """
        best_match = None
        best_ratio = 0.0

        heading_lower = heading_title.lower()

        for title, agenda in self._title_to_agenda.items():
            title_lower = title.lower()
            ratio = SequenceMatcher(None, heading_lower, title_lower).ratio()

            if ratio > best_ratio and ratio >= self.fuzzy_threshold:
                best_ratio = ratio
                best_match = agenda

        return best_match

    def get_all_entries(self) -> list[TocEntry]:
        """Get all TOC entries."""
        return self.toc_entries

    def get_agenda_for_level(self, level: int) -> list[str]:
        """Get all agenda numbers at a specific level."""
        return [e.agenda_number for e in self.toc_entries if e.level == level]


class SectionBuilder:
    """
    Build sections from document paragraphs using AgendaMatcher.
    """

    def __init__(self, matcher: AgendaMatcher):
        self.matcher = matcher
        self._current_agenda_stack: list[tuple[int, str]] = []  # (level, agenda)

    def process_heading(
        self,
        heading_title: str,
        heading_level: int,
        paragraph_index: int
    ) -> Section:
        """
        Process a heading and create a Section with correct agenda number.

        Args:
            heading_title: The heading text
            heading_level: Heading level (1-5)
            paragraph_index: Index of heading paragraph

        Returns:
            Section with matched agenda number
        """
        # Find parent agenda for fallback
        parent_agenda = self._get_parent_agenda(heading_level)

        # Match heading to agenda
        agenda_number = self.matcher.match_with_fallback(heading_title, parent_agenda)

        # Update agenda stack
        self._update_agenda_stack(heading_level, agenda_number)

        return Section(
            agenda_number=agenda_number,
            title=heading_title,
            heading_level=heading_level,
            start_index=paragraph_index,
            end_index=paragraph_index  # Will be updated when next section starts
        )

    def _get_parent_agenda(self, level: int) -> Optional[str]:
        """Get the agenda number of the parent section."""
        for stack_level, stack_agenda in reversed(self._current_agenda_stack):
            if stack_level < level:
                return stack_agenda
        return None

    def _update_agenda_stack(self, level: int, agenda: str) -> None:
        """Update the agenda stack when entering a new section."""
        # Remove all entries at same or deeper level
        self._current_agenda_stack = [
            (l, a) for l, a in self._current_agenda_stack if l < level
        ]
        # Add current
        self._current_agenda_stack.append((level, agenda))

    def reset(self) -> None:
        """Reset the agenda stack for a new document."""
        self._current_agenda_stack = []


# Patterns for extracting agenda from special titles
SESSION_NOTES_AGENDA_PATTERN = re.compile(
    r'[Ss]ession [Nn]otes for\s+(\d+(?:\.\d+)*|\d+)',
    re.IGNORECASE
)

FL_SUMMARY_AGENDA_PATTERN = re.compile(
    r'(?:FL|Feature [Ll]ead)\s+[Ss]ummary.*?(?:for\s+)?(?:AI\s+)?(\d+(?:\.\d+)*)',
    re.IGNORECASE
)


def extract_agenda_from_title(title: str) -> Optional[str]:
    """
    Extract agenda number directly from special titles.

    Handles:
    - "Session notes for 8.2 (...)"
    - "FL summary #1 for AI 8.11"

    Args:
        title: The title text

    Returns:
        Extracted agenda number or None
    """
    # Try Session notes pattern
    match = SESSION_NOTES_AGENDA_PATTERN.search(title)
    if match:
        return match.group(1)

    # Try FL summary pattern
    match = FL_SUMMARY_AGENDA_PATTERN.search(title)
    if match:
        return match.group(1)

    return None


if __name__ == "__main__":
    # Test matching
    from toc_parser import parse_toc_from_docx
    from pathlib import Path
    import sys

    if len(sys.argv) < 2:
        print("Usage: python agenda_matcher.py <docx_path>")
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    entries = parse_toc_from_docx(docx_path)

    matcher = AgendaMatcher(entries)

    # Test some matches
    test_titles = [
        "Maintenance of E-UTRA Releases 8 – 13",
        "Multi-Carrier enhancements for UMTS - WID in RP-15",  # Truncated
        "NB-IoT - WID in RP-152284.",  # Extra period
    ]

    print("Testing matches:")
    for title in test_titles:
        result = matcher.match(title)
        print(f"  '{title[:50]}...' -> {result}")
