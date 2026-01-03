"""
Markdown 파싱 유틸리티

TOC 추출, 섹션 추출, 헤더 추출 등

Spec 4.3.1 준수:
- page는 탐색 범위 축소용 힌트
- 최종 경계 판단은 LLM이 의미 기반으로 수행
- 정규식은 fallback으로만 사용
"""

import json
import re

from .llm_client import get_llm_client


def extract_header(markdown_content: str) -> str:
    """Markdown에서 헤더 영역 추출 (TOC 이전)

    명세서 4.1 참조: TOC 이전까지의 헤더 영역 추출

    Args:
        markdown_content: 전체 Markdown 내용

    Returns:
        헤더 영역 텍스트

    TOC 마커:
        - "Table of contents" (대소문자 무시)
    """
    # TOC 시작 패턴 찾기
    toc_pattern = r"(?i)table\s+of\s+contents"
    match = re.search(toc_pattern, markdown_content)

    if match:
        return markdown_content[:match.start()].strip()

    # TOC 없으면 처음 50줄 반환 (fallback)
    lines = markdown_content.split('\n')
    return '\n'.join(lines[:50])


def extract_toc(markdown_content: str) -> str:
    """Markdown에서 TOC 영역 추출

    명세서 4.2 참조:
    - 시작: "Table of contents" 이후
    - 끝: 본문 시작 전

    pandoc 변환 결과 분석:
    - TOC 항목: [제목 페이지](#anchor) 형식
    - 본문 시작: "**\" + "Main facts summary" (페이지 브레이크)
    - 섹션 헤더: Setext 스타일 (텍스트 + ======)

    Args:
        markdown_content: 전체 Markdown 내용

    Returns:
        TOC 영역 텍스트 (없으면 빈 문자열)
    """
    # TOC 시작 찾기
    toc_pattern = r"(?i)table\s+of\s+contents"
    toc_match = re.search(toc_pattern, markdown_content)

    if not toc_match:
        return ""

    toc_start = toc_match.end()
    remaining = markdown_content[toc_start:]

    # TOC 끝 찾기 (우선순위 순)
    body_patterns = [
        # 1. 페이지 브레이크 후 본문 시작 (**\ + Main facts summary)
        r"\n\*\*\\\n.*?facts\s+summary",
        # 2. Setext 스타일 헤더 (텍스트 + ===== 또는 -----)
        r"\n[^\n]+\n={3,}",
        r"\n[^\n]+\n-{3,}",
        # 3. ATX 스타일 헤더 (# 1 또는 ## 1)
        r"\n#{1,2}\s+\d+",
    ]

    earliest_match = None
    earliest_pos = len(remaining)

    for pattern in body_patterns:
        match = re.search(pattern, remaining, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
            earliest_match = match

    if earliest_match:
        return remaining[:earliest_pos].strip()

    # fallback: 마지막 TOC 링크 패턴 이후까지
    # TOC 링크 형식: [텍스트](#anchor)
    toc_link_pattern = r"\[[^\]]+\]\(#[^\)]+\)"
    all_links = list(re.finditer(toc_link_pattern, remaining))
    if all_links:
        last_link = all_links[-1]
        return remaining[:last_link.end()].strip()

    # 최종 fallback: 처음 15000자 반환
    return remaining[:15000].strip()


def _estimate_char_position_from_page(
    markdown_content: str,
    page: int | None,
    chars_per_page: int = 3000,
) -> tuple[int, int]:
    """페이지 번호로 대략적인 문자 위치 범위 추정

    Spec 4.3.1: page는 탐색 범위 축소용 힌트

    Args:
        markdown_content: 전체 Markdown 내용
        page: 페이지 번호 (None이면 전체 범위)
        chars_per_page: 페이지당 평균 문자 수 (휴리스틱)

    Returns:
        (시작 위치, 끝 위치) - 탐색 범위
    """
    if page is None:
        return 0, len(markdown_content)

    # 페이지 기반 위치 추정 (버퍼 포함)
    buffer_pages = 2  # 앞뒤 2페이지 여유
    start_page = max(1, page - buffer_pages)
    end_page = page + buffer_pages + 3  # 섹션이 여러 페이지일 수 있음

    start_pos = (start_page - 1) * chars_per_page
    end_pos = min(end_page * chars_per_page, len(markdown_content))

    return start_pos, end_pos


def _extract_section_with_regex(
    markdown_content: str,
    section_id: str,
    section_title: str,
    next_section_id: str | None = None,
    next_section_title: str | None = None,
    search_start: int = 0,
    search_end: int | None = None,
) -> str:
    """정규식 기반 섹션 추출 (fallback용)

    Args:
        markdown_content: 전체 Markdown 내용
        section_id: 추출할 섹션 ID
        section_title: 섹션 제목
        next_section_id: 다음 섹션 ID
        next_section_title: 다음 섹션 제목
        search_start: 탐색 시작 위치
        search_end: 탐색 끝 위치 (None이면 끝까지)

    Returns:
        섹션 내용 텍스트
    """
    if search_end is None:
        search_end = len(markdown_content)

    search_content = markdown_content[search_start:search_end]

    is_virtual = section_id and 'v' in section_id
    start_match = None

    # Step 1: ATX 스타일 - 번호로 찾기
    if section_id and not is_virtual:
        start_pattern = r"^(#{1,4})\s*" + re.escape(section_id) + r"\s+"
        start_match = re.search(start_pattern, search_content, re.MULTILINE | re.IGNORECASE)

    # Step 2: ATX 스타일 - 제목으로 찾기
    if not start_match and section_title:
        escaped_title = re.escape(section_title[:50] if len(section_title) > 50 else section_title)
        start_pattern = r"^(#{1,4})\s+.*?" + escaped_title
        start_match = re.search(start_pattern, search_content, re.MULTILINE | re.IGNORECASE)

    # Step 3: Setext 스타일 - 제목으로 찾기
    if not start_match and section_title:
        escaped_title = re.escape(section_title[:50] if len(section_title) > 50 else section_title)
        setext_pattern = r"^(" + escaped_title + r")\s*\n(={3,}|-{3,})"
        start_match = re.search(setext_pattern, search_content, re.MULTILINE | re.IGNORECASE)

    if not start_match:
        return ""

    content_start = search_start + start_match.start()

    # 끝 찾기
    if next_section_id and next_section_title:
        next_is_virtual = 'v' in next_section_id
        end_match = None

        remaining = markdown_content[content_start + 1:]

        if not next_is_virtual:
            end_pattern = r"^(#{1,4})\s*" + re.escape(next_section_id) + r"\s+"
            end_match = re.search(end_pattern, remaining, re.MULTILINE | re.IGNORECASE)

        if not end_match:
            escaped_next = re.escape(next_section_title[:50] if len(next_section_title) > 50 else next_section_title)
            end_pattern = r"^(#{1,4})\s+.*?" + escaped_next
            end_match = re.search(end_pattern, remaining, re.MULTILINE | re.IGNORECASE)

        if end_match:
            content_end = content_start + 1 + end_match.start()
            return markdown_content[content_start:content_end].strip()

    # 다음 동일/상위 레벨 헤더까지
    if hasattr(start_match, 'group') and start_match.group(1):
        current_level = start_match.group(1).count('#')
        remaining = markdown_content[content_start + len(start_match.group(0)):]
        next_header = rf"^#{{{1},{current_level}}}\s+\S"
        next_match = re.search(next_header, remaining, re.MULTILINE)

        if next_match:
            return markdown_content[content_start:content_start + len(start_match.group(0)) + next_match.start()].strip()

    return markdown_content[content_start:].strip()


# LLM 섹션 경계 판단 프롬프트
SECTION_BOUNDARY_PROMPT = """당신은 3GPP 회의록 문서 분석 전문가입니다.

주어진 문서 텍스트에서 특정 섹션의 정확한 시작과 끝 위치를 찾아주세요.

## 찾을 섹션
- 섹션 ID: {section_id}
- 섹션 제목: {section_title}
- 다음 섹션 ID: {next_section_id}
- 다음 섹션 제목: {next_section_title}

## 문서 텍스트 (탐색 범위)
```
{text_snippet}
```

## 출력 형식
JSON으로 응답하세요:
```json
{{
  "found": true/false,
  "start_marker": "섹션 시작을 나타내는 텍스트 (헤더 전체)",
  "end_marker": "섹션 끝을 나타내는 텍스트 (다음 섹션 헤더 또는 null)",
  "confidence": 0.0-1.0,
  "reason": "판단 근거"
}}
```

## 주의사항
- 섹션 번호뿐 아니라 제목의 의미를 함께 고려
- 다음 섹션이 시작되기 직전까지가 현재 섹션의 범위
- 헤더 형식은 ATX (# Header) 또는 Setext (Header\\n===) 스타일일 수 있음
"""


def extract_section(
    markdown_content: str,
    section_id: str,
    section_title: str,
    next_section_id: str | None = None,
    next_section_title: str | None = None,
    page: int | None = None,
    use_llm: bool = True,
) -> str:
    """Markdown에서 특정 섹션 내용 추출 (LLM 기반)

    Spec 4.3.1 Leaf 본문 추출:
    1. TOC의 page 정보로 대략적 탐색 범위 확보
    2. 해당 범위 내에서 Leaf 섹션 제목 찾기
    3. LLM이 의미 기반으로 정확한 경계 판단

    ※ page는 탐색 범위 축소용 힌트이며, 최종 경계 판단은 LLM이 의미 기반으로 수행
    ※ 정규식은 fallback으로만 사용

    Args:
        markdown_content: 전체 Markdown 내용
        section_id: 추출할 섹션 ID
        section_title: 섹션 제목
        next_section_id: 다음 섹션 ID
        next_section_title: 다음 섹션 제목
        page: 페이지 번호 (탐색 범위 힌트)
        use_llm: LLM 사용 여부 (False면 regex fallback)

    Returns:
        섹션 내용 텍스트
    """
    # Step 1: page 힌트로 탐색 범위 축소
    search_start, search_end = _estimate_char_position_from_page(markdown_content, page)

    # Step 2: 먼저 regex로 시도 (빠른 경로)
    regex_result = _extract_section_with_regex(
        markdown_content=markdown_content,
        section_id=section_id,
        section_title=section_title,
        next_section_id=next_section_id,
        next_section_title=next_section_title,
        search_start=search_start,
        search_end=search_end,
    )

    # regex가 성공하고 결과가 있으면 사용
    if regex_result:
        return regex_result

    # Step 3: regex 실패 시 전체 범위에서 다시 시도
    if search_start > 0 or search_end < len(markdown_content):
        regex_result = _extract_section_with_regex(
            markdown_content=markdown_content,
            section_id=section_id,
            section_title=section_title,
            next_section_id=next_section_id,
            next_section_title=next_section_title,
        )
        if regex_result:
            return regex_result

    # Step 4: LLM 기반 경계 판단 (use_llm=True이고 regex 실패 시)
    if use_llm:
        try:
            # 탐색 범위 텍스트 추출 (토큰 제한 고려)
            snippet_start = max(0, search_start - 2000)
            snippet_end = min(len(markdown_content), search_end + 5000)
            text_snippet = markdown_content[snippet_start:snippet_end]

            # 너무 길면 truncate
            if len(text_snippet) > 15000:
                text_snippet = text_snippet[:15000] + "\n... (truncated)"

            llm = get_llm_client()
            prompt = SECTION_BOUNDARY_PROMPT.format(
                section_id=section_id,
                section_title=section_title,
                next_section_id=next_section_id or "없음",
                next_section_title=next_section_title or "없음",
                text_snippet=text_snippet,
            )

            response = llm.invoke(prompt)
            content = response.content

            # JSON 추출
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            if result.get("found") and result.get("start_marker"):
                start_marker = result["start_marker"]
                end_marker = result.get("end_marker")

                # 마커 위치로 섹션 추출
                start_idx = markdown_content.find(start_marker)
                if start_idx >= 0:
                    if end_marker:
                        end_idx = markdown_content.find(end_marker, start_idx + 1)
                        if end_idx > start_idx:
                            return markdown_content[start_idx:end_idx].strip()

                    # end_marker 없으면 시작점부터 끝까지
                    return markdown_content[start_idx:].strip()

        except Exception:
            # LLM 실패 시 빈 문자열 반환
            pass

    return ""


def find_leaf_sections(toc: list[dict]) -> list[dict]:
    """TOC에서 Leaf 섹션 찾기 (children: [])

    Args:
        toc: TOC 섹션 목록

    Returns:
        Leaf 섹션 목록 (children이 빈 리스트인 섹션들)
    """
    return [section for section in toc if not section.get("children")]


def get_next_section(toc: list[dict], current_index: int) -> dict | None:
    """현재 섹션의 다음 섹션 정보 반환

    Args:
        toc: TOC 섹션 목록
        current_index: 현재 섹션 인덱스

    Returns:
        다음 섹션 dict 또는 None
    """
    if current_index + 1 < len(toc):
        return toc[current_index + 1]
    return None
