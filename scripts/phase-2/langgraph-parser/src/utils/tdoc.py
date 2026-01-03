"""
TDoc 유틸리티

TDoc 정규화 및 파싱 (명세서 3.5장 참조)
"""

import re


def normalize_tdoc(tdoc: str) -> str:
    """TDoc 번호 정규화

    다양한 형식의 TDoc 번호를 표준 형식으로 변환

    Args:
        tdoc: 원본 TDoc 번호 (예: "R1-2501410", "R1‑2501410", "R1 2501410")

    Returns:
        정규화된 TDoc 번호 (예: "R1-2501410")

    Examples:
        >>> normalize_tdoc("R1-2501410")
        'R1-2501410'
        >>> normalize_tdoc("R1‑2501410")  # en-dash
        'R1-2501410'
        >>> normalize_tdoc("R1 2501410")
        'R1-2501410'
    """
    if not tdoc:
        return ""

    # 다양한 대시/공백 문자를 표준 하이픈으로 변환
    normalized = tdoc.strip()
    normalized = re.sub(r"[\u2010-\u2015\u2212\s]+", "-", normalized)  # 다양한 대시 및 공백
    normalized = normalized.upper()  # 대문자 변환

    return normalized


def parse_tdoc(tdoc: str) -> dict | None:
    """TDoc 번호 파싱

    TDoc 번호에서 그룹, 미팅 정보 추출

    Args:
        tdoc: TDoc 번호 (예: "R1-2501410")

    Returns:
        파싱 결과 딕셔너리 또는 None (파싱 실패 시)
        {
            "group": "R1",
            "meeting_number": "25",
            "sequence": "01410"
        }
    """
    normalized = normalize_tdoc(tdoc)

    # 패턴: {그룹}-{회의번호 2자리}{순번 5자리}
    pattern = r"^([A-Z]+\d*)-(\d{2})(\d{5})$"
    match = re.match(pattern, normalized)

    if not match:
        return None

    return {
        "group": match.group(1),
        "meeting_number": match.group(2),
        "sequence": match.group(3),
    }
