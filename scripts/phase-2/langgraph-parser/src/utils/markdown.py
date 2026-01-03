"""
Markdown 파싱 유틸리티

TOC 추출, 섹션 추출, 헤더 추출 등
"""

import re


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


def extract_section(
    markdown_content: str,
    section_id: str,
    section_title: str,
    next_section_id: str | None = None,
    next_section_title: str | None = None,
) -> str:
    """Markdown에서 특정 섹션 내용 추출

    명세서 4.3.1 Leaf 본문 추출:
    1. Leaf 섹션 제목 찾기
    2. 다음 섹션 제목 찾기
    3. 두 제목 사이의 본문이 해당 Leaf의 내용

    ※ 페이지 번호가 아닌 섹션 제목의 의미로 경계 판단 (일반화 원칙)
    ※ ATX 스타일 (# Header)과 Setext 스타일 (Header\n===) 모두 지원

    Args:
        markdown_content: 전체 Markdown 내용
        section_id: 추출할 섹션 ID
        section_title: 섹션 제목 (패턴 매칭용)
        next_section_id: 다음 섹션 ID
        next_section_title: 다음 섹션 제목

    Returns:
        섹션 내용 텍스트
    """
    # === 섹션 시작 찾기 ===
    # Spec 4.3.1: 섹션 제목의 의미로 경계 판단
    # 전략: ATX 스타일 → Setext 스타일 → 제목 fallback

    is_virtual = section_id and 'v' in section_id  # 8.1v1, 8.1v2 등
    start_match = None
    is_setext = False

    # Step 1: ATX 스타일 - 번호로 찾기 시도 (# 5 Title)
    if section_id and not is_virtual:
        start_pattern = r"^(#{1,4})\s*" + re.escape(section_id) + r"\s+"
        start_match = re.search(start_pattern, markdown_content, re.MULTILINE | re.IGNORECASE)

    # Step 2: ATX 스타일 - 제목으로 찾기 (# Title)
    if not start_match and section_title:
        escaped_title = re.escape(section_title[:50] if len(section_title) > 50 else section_title)
        start_pattern = r"^(#{1,4})\s+.*?" + escaped_title
        start_match = re.search(start_pattern, markdown_content, re.MULTILINE | re.IGNORECASE)

    # Step 3: Setext 스타일 - 제목으로 찾기 (Title\n===)
    if not start_match and section_title:
        escaped_title = re.escape(section_title[:50] if len(section_title) > 50 else section_title)
        # Setext 패턴: 제목 줄 + 다음 줄에 === 또는 ---
        setext_pattern = r"^(" + escaped_title + r")\s*\n(={3,}|-{3,})"
        start_match = re.search(setext_pattern, markdown_content, re.MULTILINE | re.IGNORECASE)
        if start_match:
            is_setext = True

    if not start_match:
        return ""

    content_start = start_match.start()

    # === 섹션 끝 찾기 ===
    # Spec 4.3.1: 다음 섹션 제목 찾기 → 두 제목 사이가 본문
    # 전략: 번호로 먼저 시도 → 실패 시 제목으로 fallback (Spec 준수)

    if next_section_id and next_section_title:
        next_is_virtual = 'v' in next_section_id
        end_match = None

        # Step 1: 번호로 찾기 시도
        if not next_is_virtual:
            end_pattern = r"^(#{1,4})\s*" + re.escape(next_section_id) + r"\s+"
            end_match = re.search(end_pattern, markdown_content[content_start + 1:], re.MULTILINE | re.IGNORECASE)

        # Step 2: 번호로 못 찾으면 제목으로 찾기 (Spec 준수 - 핵심 수정)
        if not end_match:
            escaped_next = re.escape(next_section_title[:50] if len(next_section_title) > 50 else next_section_title)
            end_pattern = r"^(#{1,4})\s+.*?" + escaped_next
            end_match = re.search(end_pattern, markdown_content[content_start + 1:], re.MULTILINE | re.IGNORECASE)

        if end_match:
            content_end = content_start + 1 + end_match.start()
            return markdown_content[content_start:content_end].strip()

    # 다음 섹션 정보 없으면 다음 동일/상위 레벨 헤더까지
    current_level = start_match.group(1).count('#')
    remaining = markdown_content[content_start + len(start_match.group(0)):]

    # 동일 또는 상위 레벨 헤더 찾기 (숫자로 시작하거나 일반 텍스트)
    next_header = rf"^#{{{1},{current_level}}}\s+\S"
    next_match = re.search(next_header, remaining, re.MULTILINE)

    if next_match:
        return markdown_content[content_start:content_start + len(start_match.group(0)) + next_match.start()].strip()

    # 최종 fallback: 문서 끝까지 (섹션이 마지막인 경우)
    # 이전: 20000자 제한 → Spec 준수를 위해 제한 제거
    return markdown_content[content_start:].strip()


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
