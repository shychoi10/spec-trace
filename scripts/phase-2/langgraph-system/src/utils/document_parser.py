"""
Document Parser for DOCX files - LLM-Based Architecture

DOCX 파일을 파싱하여 LLM이 구조를 이해하고 섹션을 추출합니다.

핵심 원칙:
- 정규식/규칙 기반 파싱 금지
- LLM이 문서 구조를 파악하고 섹션 경계를 결정
- True Agentic AI: 모든 분류/추출은 LLM이 수행
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from docx import Document
from docx.document import Document as DocxDocument

logger = logging.getLogger(__name__)


@dataclass
class ParsedSection:
    """파싱된 Section 정보"""

    section_number: str
    title: str
    raw_text: str
    start_index: int = 0
    end_index: int = 0


@dataclass
class ParsedDocument:
    """전체 문서 파싱 결과"""

    file_path: str
    file_name: str
    total_paragraphs: int
    full_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentParser:
    """DOCX 문서 파서 - LLM 기반 섹션 추출"""

    def __init__(self, file_path: str | Path, llm_manager=None):
        """
        Args:
            file_path: DOCX 파일 경로
            llm_manager: LLM 매니저 (섹션 추출 시 필요)
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        if not self.file_path.suffix.lower() == ".docx":
            raise ValueError(f"Expected .docx file, got: {self.file_path.suffix}")

        self._doc: Optional[DocxDocument] = None
        self._full_text: str = ""
        self._paragraphs: list[str] = []
        self._llm = llm_manager

    def set_llm_manager(self, llm_manager):
        """LLM 매니저 설정"""
        self._llm = llm_manager

    def load(self) -> "DocumentParser":
        """DOCX 파일 로드"""
        self._doc = Document(str(self.file_path))
        return self

    def parse_paragraphs(self) -> list[str]:
        """모든 Paragraph 텍스트 추출 (LLM에 전달할 원본 데이터)"""
        if self._doc is None:
            self.load()

        self._paragraphs = []
        for para in self._doc.paragraphs:
            text = para.text.strip()
            if text:
                self._paragraphs.append(text)

        self._full_text = "\n".join(self._paragraphs)
        return self._paragraphs

    def get_full_text(self) -> str:
        """전체 문서 텍스트 반환"""
        if not self._full_text:
            self.parse_paragraphs()
        return self._full_text

    def get_section_text(self, section_identifier: str) -> str:
        """특정 섹션의 텍스트를 LLM을 사용하여 추출

        Args:
            section_identifier: 섹션 식별자
                - 숫자 (예: "5"): Section 번호로 검색
                - 콘텐츠 타입 (예: "incoming_ls"): 제목으로 검색

        Returns:
            섹션의 전체 텍스트
        """
        if not self._full_text:
            self.parse_paragraphs()

        if self._llm is None:
            logger.warning("[Parser] LLM not set, returning empty section")
            return ""

        # 콘텐츠 유형과 Section 번호 매핑 (참고용, LLM이 콘텐츠 기반으로 식별)
        content_type_titles = {
            "incoming_ls": "Incoming Liaison Statements",
            "reports_work_plan": "Reports and Work Plan",
            "draft_ls": "Draft liaison statements",
            "maintenance": "Maintenance",
            "work_items": "Work Items",
        }

        section_number_titles = {
            "5": "Incoming Liaison Statements",
            "6": "Reports and Work Plan",
            "7": "Draft liaison statements",
            "8": "Maintenance",
            "9": "Work Items",
        }

        # 콘텐츠 기반 식별자인지 확인
        is_content_based = section_identifier in content_type_titles
        section_title = content_type_titles.get(
            section_identifier,
            section_number_titles.get(section_identifier, f"Section {section_identifier}")
        )

        # LLM에게 섹션 추출 요청 (콘텐츠 기반 vs 번호 기반)
        if is_content_based:
            # 콘텐츠 기반: 제목으로만 검색
            prompt = f"""You are a document structure analyzer. Extract the content of a specific section from a 3GPP RAN1 meeting minutes document.

**Task**: Extract the "{section_title}" section from the document.

**Instructions**:
1. Find where the "{section_title}" section begins in the document
2. The section starts with a heading containing "{section_title}" (could be "N Incoming Liaison Statements" where N is any section number)
3. The section ends when the next major section begins (look for next numbered section heading)
4. Include ALL content within this section - every LS item, discussion, and decision
5. Do NOT summarize - extract the FULL raw text

**Document Content** (showing relevant portion):
{self._full_text[:80000]}

**Response Format**:
Return ONLY the extracted section content, nothing else. Start from the section heading and include everything until the next section.

If you cannot find the "{section_title}" section, return exactly: "SECTION_NOT_FOUND"
"""
        else:
            # 번호 기반: Section 번호로 검색
            try:
                next_section = int(section_identifier) + 1
            except ValueError:
                next_section = "next"

            prompt = f"""You are a document structure analyzer. Extract the content of a specific section from a 3GPP RAN1 meeting minutes document.

**Task**: Extract Section {section_identifier} "{section_title}" from the document.

**Instructions**:
1. Find where Section {section_identifier} or "{section_title}" begins in the document
2. The section starts with a heading (could be "{section_identifier} {section_title}" or similar)
3. The section ends when the next major section begins (Section {next_section} or similar)
4. Include ALL content within this section - every LS item, discussion, and decision
5. Do NOT summarize - extract the FULL raw text

**Document Content** (showing relevant portion):
{self._full_text[:80000]}

**Response Format**:
Return ONLY the extracted section content, nothing else. Start from the section heading and include everything until the next section.

If you cannot find Section {section_identifier}, return exactly: "SECTION_NOT_FOUND"
"""

        try:
            response = self._llm.generate(prompt, temperature=0.0, max_tokens=16000)

            if "SECTION_NOT_FOUND" in response:
                logger.warning(f"[Parser] Section '{section_identifier}' not found by LLM")
                return ""

            logger.info(f"[Parser] LLM extracted Section '{section_identifier}': {len(response)} characters")
            return response.strip()

        except Exception as e:
            logger.error(f"[Parser] LLM extraction failed: {e}")
            return ""

    def extract_section_with_boundaries(self, section_number: str) -> dict:
        """LLM을 사용하여 섹션 추출 및 경계 정보 반환

        Args:
            section_number: 섹션 번호

        Returns:
            {"content": str, "start_marker": str, "end_marker": str}
        """
        if not self._full_text:
            self.parse_paragraphs()

        if self._llm is None:
            return {"content": "", "start_marker": "", "end_marker": ""}

        prompt = f"""Analyze this 3GPP RAN1 meeting document and extract Section {section_number}.

**Document** (first 80000 chars):
{self._full_text[:80000]}

**Instructions**:
1. Identify the exact start of Section {section_number}
2. Identify where Section {section_number} ends (start of next major section)
3. Extract ALL content between these boundaries

**Response** (JSON format):
{{
    "section_found": true/false,
    "start_text": "first 50 chars of section...",
    "end_text": "last 50 chars of section...",
    "content": "FULL section content here..."
}}

Return valid JSON only."""

        try:
            response = self._llm.generate(prompt, temperature=0.0, max_tokens=16000)

            # JSON 파싱 시도
            try:
                result = json.loads(response)
                if result.get("section_found"):
                    return {
                        "content": result.get("content", ""),
                        "start_marker": result.get("start_text", ""),
                        "end_marker": result.get("end_text", ""),
                    }
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 그대로 반환
                return {"content": response, "start_marker": "", "end_marker": ""}

        except Exception as e:
            logger.error(f"[Parser] Section extraction failed: {e}")

        return {"content": "", "start_marker": "", "end_marker": ""}

    def get_full_document(self) -> ParsedDocument:
        """전체 문서 파싱 결과 반환"""
        if not self._full_text:
            self.parse_paragraphs()

        return ParsedDocument(
            file_path=str(self.file_path),
            file_name=self.file_path.name,
            total_paragraphs=len(self._paragraphs),
            full_text=self._full_text,
            metadata=self._get_core_properties(),
        )

    def _get_core_properties(self) -> dict[str, Any]:
        """문서 메타데이터 추출"""
        if self._doc is None:
            return {}

        try:
            props = self._doc.core_properties
            return {
                "author": props.author,
                "title": props.title,
                "subject": props.subject,
                "created": str(props.created) if props.created else None,
                "modified": str(props.modified) if props.modified else None,
            }
        except Exception:
            return {}


def parse_docx(file_path: str | Path) -> ParsedDocument:
    """DOCX 파일을 파싱하여 구조화된 데이터로 반환

    Args:
        file_path: DOCX 파일 경로

    Returns:
        파싱된 문서 데이터
    """
    parser = DocumentParser(file_path)
    return parser.get_full_document()


def get_section_text(file_path: str | Path, section_number: str, llm_manager=None) -> str:
    """특정 섹션의 텍스트만 추출 (LLM 기반)

    Args:
        file_path: DOCX 파일 경로
        section_number: 섹션 번호 (예: "5")
        llm_manager: LLM 매니저

    Returns:
        섹션의 전체 텍스트
    """
    parser = DocumentParser(file_path, llm_manager)
    parser.parse_paragraphs()
    return parser.get_section_text(section_number)
