"""
TOC 유틸리티 (Spec 4.0 준수)

- Virtual Numbering: 번호 없는 섹션에 가상 번호 부여
- Parent/Children 계산: depth 기반 계층 관계 생성
- Spec 4.0 toc_raw.yaml 구조 처리
"""

import re
from typing import Optional


def parse_section_number_from_text(text: str) -> Optional[str]:
    """텍스트에서 섹션 번호 추출

    예: "9.1.1 MIMO 14" → "9.1.1"
        "1 Opening of the meeting 5" → "1"
        "MIMO 14" → None

    Args:
        text: TOC 항목 텍스트

    Returns:
        섹션 번호 (없으면 None)
    """
    match = re.match(r'^(\d+(?:\.\d+)*)\s+', text)
    return match.group(1) if match else None


def extract_title_from_text(text: str) -> str:
    """텍스트에서 제목 추출 (번호와 페이지 번호 제거)

    예: "9.1.1 MIMO 14" → "MIMO"
        "MIMO 14" → "MIMO"

    Args:
        text: TOC 항목 텍스트

    Returns:
        제목
    """
    # 페이지 번호 제거 (마지막 숫자)
    page_match = re.search(r'\s+\d+\s*$', text)
    if page_match:
        text = text[:page_match.start()].strip()

    # 섹션 번호 제거
    id_match = re.match(r'^(?:\d+(?:\.\d+)*)\s+', text)
    if id_match:
        text = text[id_match.end():].strip()

    return text


def apply_virtual_numbering(toc_raw: dict) -> list[dict]:
    """unnumbered: true인 항목에 가상 번호 부여 (Spec 4.0 준수)

    형식: {parent_id}v{sequence}
    예: 8.1 하위의 "MIMO" → 8.1v1, "MIMO (Alignment)" → 8.1v2

    Args:
        toc_raw: Spec 4.0 toc_raw.yaml 구조 (entries 포함)

    Returns:
        가상 번호가 부여된 TOC 리스트 (virtual 필드 추가)
    """
    # entries 래퍼 처리
    entries = toc_raw.get("entries", [])

    result = []
    parent_stack = []  # (id, depth) 스택
    virtual_counters = {}  # parent_id → 현재 virtual 번호

    for entry in entries:
        depth = entry.get("depth", 1)
        text = entry.get("text", "")
        page = entry.get("page")
        style = entry.get("style", "")
        anchor = entry.get("anchor", "")
        is_unnumbered = entry.get("unnumbered", False)

        # text에서 섹션 번호와 제목 파싱
        section_id = parse_section_number_from_text(text)
        title = extract_title_from_text(text)

        # 스택 정리: 현재 depth보다 같거나 깊은 항목 제거
        while parent_stack and parent_stack[-1][1] >= depth:
            parent_stack.pop()

        # 부모 ID 결정
        parent_id = parent_stack[-1][0] if parent_stack else None

        # Virtual Numbering 적용
        if is_unnumbered or section_id is None:
            # 부모 ID 기반 가상 번호 생성
            counter_key = parent_id or "root"
            if counter_key not in virtual_counters:
                virtual_counters[counter_key] = 0
            virtual_counters[counter_key] += 1

            if parent_id:
                section_id = f"{parent_id}v{virtual_counters[counter_key]}"
            else:
                section_id = f"v{virtual_counters[counter_key]}"

            virtual = True
        else:
            virtual = False
            # 실제 번호를 가진 섹션의 virtual counter 리셋
            virtual_counters[section_id] = 0

        # 스택에 추가 (다음 항목의 부모가 될 수 있음)
        parent_stack.append((section_id, depth))

        result.append({
            "id": section_id,
            "title": title,
            "depth": depth,
            "page": page,
            "style": style,
            "anchor": anchor,
            "virtual": virtual,
        })

    return result


def compute_parent_children(toc_numbered: list[dict]) -> list[dict]:
    """depth 기반으로 parent/children 관계 계산

    Args:
        toc_numbered: Virtual Numbering이 적용된 TOC 리스트

    Returns:
        parent/children이 추가된 TOC 리스트
    """
    # ID → index 매핑
    id_to_idx = {entry["id"]: idx for idx, entry in enumerate(toc_numbered)}

    result = []
    parent_stack = []  # (id, depth) 스택

    for entry in toc_numbered:
        section_id = entry["id"]
        depth = entry["depth"]

        # 스택 정리: 현재 depth보다 같거나 깊은 항목 제거
        while parent_stack and parent_stack[-1][1] >= depth:
            parent_stack.pop()

        # 부모 ID 결정
        parent_id = parent_stack[-1][0] if parent_stack else None

        # 스택에 추가
        parent_stack.append((section_id, depth))

        result.append({
            **entry,
            "parent": parent_id,
            "children": [],  # 나중에 채움
        })

    # Children 채우기
    for i, entry in enumerate(result):
        parent_id = entry.get("parent")
        if parent_id and parent_id in id_to_idx:
            parent_idx = id_to_idx[parent_id]
            result[parent_idx]["children"].append(entry["id"])

    return result


def process_toc_raw(toc_raw: dict) -> list[dict]:
    """toc_raw를 처리하여 완전한 TOC 구조 생성 (Spec 4.0 준수)

    1. Spec 4.0 toc_raw.yaml 구조 처리
    2. Virtual Numbering 적용
    3. Parent/Children 계산

    Args:
        toc_raw: Spec 4.0 toc_raw.yaml 구조 (entries 포함)

    Returns:
        완전한 TOC 구조 (section_type, skip 제외)
    """
    # 1. Virtual Numbering
    toc_numbered = apply_virtual_numbering(toc_raw)

    # 2. Parent/Children 계산
    toc_with_relations = compute_parent_children(toc_numbered)

    return toc_with_relations


def classify_section_type_by_rules(title: str, parent_type: str = None) -> tuple[str, str, bool]:
    """규칙 기반 section_type 분류 (Spec 5032-5039 우선순위)

    우선순위:
        1. "Annex" → Annex
        2. "Liaison" → LS
        3. "Opening", "Closing", "Approval", "Highlights", "Minutes" → Procedural
        4. "UE Features", "UE feature" → UE_Features
        5. "Study", "SI" → Study
        6. "Maintenance", "Pre-Rel" → Maintenance
        7. "Release XX" (with number) → Release
        8. No keyword → inherit from parent

    Args:
        title: 섹션 제목
        parent_type: 부모 섹션의 section_type (상속용)

    Returns:
        (section_type, type_reason, skip)
    """
    title_lower = title.lower()

    # 우선순위 1: Annex
    annex_match = re.match(r'^annex\s*([a-z])', title_lower)
    if annex_match or title_lower.startswith("annex"):
        annex_letter = annex_match.group(1).upper() if annex_match else None

        # Skip 규칙: Annex A, D, E, F, G, H → skip
        if annex_letter in ("A", "D", "E", "F", "G", "H"):
            return ("Annex", f"Title starts with 'Annex {annex_letter}'", True)
        # Annex B, C → 처리 대상
        elif annex_letter in ("B", "C"):
            return ("Annex", f"Title starts with 'Annex {annex_letter}'", False)
        else:
            return ("Annex", "Title contains 'Annex'", False)

    # 우선순위 2: LS (Liaison Statements)
    if "liaison" in title_lower:
        return ("LS", "Title contains 'Liaison'", False)

    # 우선순위 3: Procedural
    procedural_keywords = ["opening", "closing", "approval", "highlights", "minutes"]
    for kw in procedural_keywords:
        if kw in title_lower:
            return ("Procedural", f"Title contains '{kw.capitalize()}'", True)

    # 우선순위 4: UE_Features
    if "ue feature" in title_lower or "ue features" in title_lower:
        return ("UE_Features", "Title contains 'UE Features'", False)

    # 우선순위 5: Study
    if "study" in title_lower:
        return ("Study", "Title contains 'Study'", False)
    # "SI" 체크: 단어 경계 확인 (MIMO → X, SI on → O)
    if re.search(r'\bSI\b', title):
        return ("Study", "Title contains 'SI'", False)

    # 우선순위 6: Maintenance
    if "maintenance" in title_lower or "pre-rel" in title_lower:
        return ("Maintenance", "Title contains 'Maintenance' or 'Pre-Rel'", False)

    # 우선순위 7: Release XX
    release_match = re.search(r'release\s*\d+', title_lower)
    if release_match:
        return ("Release", f"Title contains '{release_match.group(0).title()}'", False)

    # 우선순위 8: 상속
    if parent_type and parent_type != "unknown":
        return (parent_type, "Inherited from parent", False)

    # 분류 불가
    return ("unknown", "No matching keyword", False)


def apply_rule_based_classification(toc_with_relations: list[dict]) -> list[dict]:
    """규칙 기반 section_type 분류 적용 (상속 포함)

    Args:
        toc_with_relations: parent/children이 계산된 TOC 리스트

    Returns:
        section_type, type_reason, skip, skip_reason이 추가된 TOC 리스트
    """
    # ID → section_type 매핑 (상속용)
    id_to_type = {}

    result = []
    for entry in toc_with_relations:
        section_id = entry["id"]
        title = entry.get("title", "")
        parent_id = entry.get("parent")

        # 부모 타입 조회
        parent_type = id_to_type.get(parent_id) if parent_id else None

        # 규칙 기반 분류
        section_type, type_reason, skip = classify_section_type_by_rules(title, parent_type)

        # skip_reason 결정
        skip_reason = None
        if skip:
            if section_type == "Procedural":
                skip_reason = "Procedural section"
            elif section_type == "Annex":
                skip_reason = "Annex A, D, E, F, G, H are skipped"

        # 타입 저장 (자식이 상속받을 수 있도록)
        id_to_type[section_id] = section_type

        result.append({
            **entry,
            "section_type": section_type,
            "type_reason": type_reason,
            "skip": skip,
            "skip_reason": skip_reason,
        })

    return result


if __name__ == "__main__":
    # 테스트 (Spec 4.0 형식)
    import yaml

    test_toc_raw = {
        "entries": [
            {"text": "8 Maintenance on Release 18 14", "style": "TOC 1", "depth": 1, "page": 14, "anchor": "maintenance-on-release-18"},
            {"text": "8.1 Maintenance on Rel-18 work items 14", "style": "TOC 2", "depth": 2, "page": 14, "anchor": "maintenance-on-rel-18-work-items"},
            {"text": "MIMO 14", "style": "TOC 3", "depth": 3, "page": 14, "anchor": "mimo", "unnumbered": True},
            {"text": "MIMO (Alignment/editorial) 15", "style": "TOC 3", "depth": 3, "page": 15, "anchor": "mimo-alignmenteditorial", "unnumbered": True},
            {"text": "8.2 Other maintenance 16", "style": "TOC 2", "depth": 2, "page": 16, "anchor": "other-maintenance"},
            {"text": "9 Release 19 23", "style": "TOC 1", "depth": 1, "page": 23, "anchor": "release-19"},
        ]
    }

    result = process_toc_raw(test_toc_raw)
    print(yaml.dump(result, allow_unicode=True, default_flow_style=False))
