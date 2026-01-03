"""
정규식 기반 메타데이터 파싱

명세서 4.1 참조: 역할 1 메타데이터 추출
전략: 정규식 파싱 우선, 실패 시 LLM fallback
"""

import re

from dateutil import parser as date_parser


def parse_metadata_regex(header_text: str) -> tuple[dict | None, list[str]]:
    """정규식으로 메타데이터 추출

    Args:
        header_text: 문서 헤더 텍스트

    Returns:
        tuple[dict | None, list[str]]: (추출된 데이터 dict, 누락 필드 리스트)
    """
    data = {}
    missing = []

    # Source
    if source := parse_source(header_text):
        data["source"] = source
    else:
        missing.append("source")

    # Title 파싱 (TSG, WG, meeting_number, version)
    if title_data := parse_title(header_text):
        data.update(title_data)
    else:
        missing.extend(["tsg", "wg", "wg_code", "meeting_number", "version"])

    # Location
    if location := parse_location(header_text):
        data["location"] = location
    else:
        missing.append("location")

    # Date range
    if dates := parse_date_range(header_text):
        data["start_date"], data["end_date"] = dates
    else:
        missing.extend(["start_date", "end_date"])

    # Document for
    if doc_for := parse_document_for(header_text):
        data["document_for"] = doc_for
    else:
        missing.append("document_for")

    # meeting_id 조합
    if "wg_code" in data and "meeting_number" in data:
        data["meeting_id"] = f"{data['wg_code']}_{data['meeting_number']}"
    else:
        missing.append("meeting_id")

    return data if data else None, missing


def parse_source(text: str) -> str | None:
    """Source: 필드 추출

    Args:
        text: 헤더 텍스트

    Returns:
        Source 값 또는 None
    """
    match = re.search(r"Source:\s*(.+)", text)
    return match.group(1).strip() if match else None


def parse_title(text: str) -> dict | None:
    """Title에서 TSG, WG, meeting_number, version 추출

    패턴: TSG RAN WG1 #120 v1.0.0
    pandoc이 #을 \\#로 escape함 (파일에서는 \#로 보임)

    Args:
        text: 헤더 텍스트

    Returns:
        dict with tsg, wg, wg_code, meeting_number, version 또는 None
    """
    # pandoc이 #을 \#로 escape (파일에서 \\#로 저장됨)
    # \\#, \#, # 모두 매칭
    pattern = r"TSG\s+(\w+)\s+(\w+)\s+(?:\\\\#|\\#|#)(\d+\w*)\s+v([\d.]+)"
    match = re.search(pattern, text)
    if match:
        tsg, wg, num, ver = match.groups()
        wg_code = tsg + wg[-1]  # RAN + 1 = RAN1
        return {
            "tsg": tsg,
            "wg": wg,
            "wg_code": wg_code,
            "meeting_number": num,
            "version": ver,
        }
    return None


def parse_location(text: str) -> str | None:
    """괄호 내 장소 추출

    패턴: (Athens, Greece, ...)

    Args:
        text: 헤더 텍스트

    Returns:
        Location 문자열 또는 None
    """
    match = re.search(r"\(([^,]+(?:,\s*[^,)]+)?)", text)
    if match:
        loc = match.group(1).strip()
        # "Online meeting" 처리
        if "online" in loc.lower():
            return "Online meeting"
        return loc
    return None


def parse_date_range(text: str) -> tuple[str, str] | None:
    """날짜 범위 추출 → ISO 8601 변환

    지원 패턴:
    - February 17th -- 21st, 2025 (같은 달)
    - 24^th^ February -- 6^th^ March 2020 (다른 달)
    - 15^th^ -- 19^th^ February 2016 (superscript ordinals)

    Args:
        text: 헤더 텍스트

    Returns:
        tuple[start_date, end_date] in YYYY-MM-DD format 또는 None
    """
    # 같은 달 패턴: February 17th -- 21st, 2025
    pattern1 = r"(\w+)\s+(\d+)(?:st|nd|rd|th)?\s*[-–]+\s*(\d+)(?:st|nd|rd|th)?,?\s+(\d{4})"
    match = re.search(pattern1, text)
    if match:
        month, start_day, end_day, year = match.groups()
        try:
            start = date_parser.parse(f"{month} {start_day}, {year}")
            end = date_parser.parse(f"{month} {end_day}, {year}")
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        except Exception:
            pass

    # 다른 달 패턴: 24^th^ February -- 6^th^ March 2020
    pattern2 = r"(\d+)(?:\^?(?:st|nd|rd|th)\^?)?\s*(\w+)\s*[-–]+\s*(\d+)(?:\^?(?:st|nd|rd|th)\^?)?\s*(\w+)\s+(\d{4})"
    match = re.search(pattern2, text)
    if match:
        start_day, start_month, end_day, end_month, year = match.groups()
        try:
            start = date_parser.parse(f"{start_month} {start_day}, {year}")
            end = date_parser.parse(f"{end_month} {end_day}, {year}")
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        except Exception:
            pass

    return None


def parse_document_for(text: str) -> str | None:
    """Document for: 필드 추출

    Args:
        text: 헤더 텍스트

    Returns:
        Document for 값 또는 None
    """
    match = re.search(r"Document for:\s*(.+)", text)
    return match.group(1).strip() if match else None
