"""
프롬프트 템플릿 패키지

명세서 6장 참조:
- metadata_prompt: 역할 1 메타데이터 추출용
- toc_prompt: 역할 2 TOC 파싱용
- subsection_prompts/: SubSection Agent용
"""

from .metadata_prompt import METADATA_EXTRACTION_PROMPT
from .toc_prompt import TOC_PROMPT, TOC_PARSING_PROMPT

__all__ = [
    "METADATA_EXTRACTION_PROMPT",
    "TOC_PROMPT",
    "TOC_PARSING_PROMPT",
]
