"""
유틸리티 패키지

- docx_converter: python-docx 변환 (하이라이트 마커 보존)
- markdown: Markdown 파싱
- metadata_parser: 정규식 메타데이터 파싱
- llm_client: LLM 클라이언트
- tdoc: TDoc 정규화
- file_io: YAML 파일 I/O
"""

from .docx_converter import (
    convert_docx_to_markdown,
    extract_meeting_id,
    extract_toc_from_docx,
)
from .toc_utils import (
    apply_virtual_numbering,
    compute_parent_children,
    process_toc_raw,
)
from .markdown import extract_header, extract_toc, extract_section
from .metadata_parser import parse_metadata_regex
from .llm_client import get_llm_client, call_llm_for_metadata, call_llm_for_toc
from .tdoc import normalize_tdoc, parse_tdoc
from .file_io import save_yaml, load_yaml, ensure_output_dir

__all__ = [
    # docx_converter
    "convert_docx_to_markdown",
    "extract_meeting_id",
    "extract_toc_from_docx",
    # toc_utils
    "apply_virtual_numbering",
    "compute_parent_children",
    "process_toc_raw",
    # markdown
    "extract_header",
    "extract_toc",
    "extract_section",
    # metadata_parser
    "parse_metadata_regex",
    # llm_client
    "get_llm_client",
    "call_llm_for_metadata",
    "call_llm_for_toc",
    # tdoc
    "normalize_tdoc",
    "parse_tdoc",
    # file_io
    "save_yaml",
    "load_yaml",
    "ensure_output_dir",
]
