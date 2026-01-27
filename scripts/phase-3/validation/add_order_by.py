#!/usr/bin/env python3
"""
CQ 쿼리에 ORDER BY 추가 - Spec 정렬 기준 적용
Phase-3 Spec 기반: Meeting DESC (최신 먼저), Sequence ASC
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset.json"
OUTPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset_sorted.json"

# 카테고리별 정렬 규칙
# Note: Resolution 노드에 sequence 속성이 없으므로 Meeting 번호로만 정렬
SORT_RULES = {
    "기술_진화": {
        "order_by": "ORDER BY m.meetingNumberInt DESC",
        "need_meeting": True,
        "resolution_alias": "a"  # Agreement
    },
    "스펙_영향": {
        "order_by": "ORDER BY m.meetingNumberInt DESC",
        "need_meeting": True,
        "resolution_alias": "a"
    },
    "미결_이슈": {
        "order_by": "ORDER BY m.meetingNumberInt DESC",
        "need_meeting": True,
        "resolution_alias": None  # 다양함 (a, w, c)
    },
    "회의_결정": {
        "order_by": "ORDER BY m.meetingNumberInt DESC",
        "need_meeting": False,  # 이미 있음
        "resolution_alias": "a"
    },
    "기술_비교": {
        "order_by": "ORDER BY m.meetingNumberInt ASC",  # 시계열
        "need_meeting": True,
        "resolution_alias": "a"
    },
    "회사_기여": {
        "order_by": None,  # 쿼리별 개별 처리
        "need_meeting": False,
        "resolution_alias": None
    },
    "복합_검색": {
        "order_by": None,  # 쿼리별 개별 처리
        "need_meeting": False,
        "resolution_alias": None
    }
}


def get_resolution_alias(cypher: str) -> str:
    """쿼리에서 Resolution 타입의 alias 추출"""
    # Agreement, Conclusion, WorkingAssumption 매칭
    match = re.search(r'\((\w+):(Agreement|Conclusion|WorkingAssumption)\)', cypher)
    if match:
        return match.group(1)
    return None


def has_meeting_relation(cypher: str) -> bool:
    """쿼리에 Meeting 관계가 있는지 확인"""
    return ':MADEAT]->(m:Meeting)' in cypher or ':PRESENTEDAT]->(m:Meeting)' in cypher


def has_order_by(cypher: str) -> bool:
    """쿼리에 ORDER BY가 있는지 확인"""
    return 'ORDER BY' in cypher.upper()


def is_count_query(cypher: str) -> bool:
    """집계 쿼리인지 확인"""
    return 'count(' in cypher.lower()


def add_meeting_relation(cypher: str, alias: str) -> str:
    """Meeting 관계 추가"""
    if has_meeting_relation(cypher):
        return cypher

    # Resolution 타입 찾기
    pattern = rf'\(({alias}):(Agreement|Conclusion|WorkingAssumption)\)'
    match = re.search(pattern, cypher)

    if match:
        original = match.group(0)
        # MATCH 절에 Meeting 관계 추가
        new_match = f"{original}-[:MADEAT]->(m:Meeting)"
        cypher = cypher.replace(original, new_match)

    return cypher


def add_order_by_clause(cypher: str, order_by: str, alias: str) -> str:
    """ORDER BY 절 추가"""
    if has_order_by(cypher):
        return cypher

    # LIMIT 앞에 ORDER BY 삽입
    if 'LIMIT' in cypher.upper():
        # LIMIT 찾기
        limit_match = re.search(r'\s+LIMIT\s+\d+', cypher, re.IGNORECASE)
        if limit_match:
            limit_pos = limit_match.start()
            cypher = cypher[:limit_pos] + f" {order_by}" + cypher[limit_pos:]
    else:
        # LIMIT 없으면 끝에 추가
        cypher = cypher.strip() + f" {order_by}"

    return cypher


def process_query(cq: dict) -> dict:
    """개별 CQ 쿼리 처리"""
    category = cq["category"]
    cypher = cq["cypher"]
    cq_id = cq["id"]

    # 집계 쿼리는 건너뛰기
    if is_count_query(cypher):
        return cq

    # 이미 ORDER BY 있으면 건너뛰기
    if has_order_by(cypher):
        return cq

    rule = SORT_RULES.get(category, {})

    # 정렬 규칙 없는 카테고리 (회사_기여, 복합_검색)
    if rule.get("order_by") is None:
        # Resolution 쿼리인 경우에만 처리
        alias = get_resolution_alias(cypher)
        if alias:
            # Meeting 관계 추가 필요 여부
            if not has_meeting_relation(cypher):
                cypher = add_meeting_relation(cypher, alias)
            # ORDER BY 추가 (Meeting 번호만 - sequence 속성 없음)
            order_by = "ORDER BY m.meetingNumberInt DESC"
            cypher = add_order_by_clause(cypher, order_by, alias)
        return {**cq, "cypher": cypher}

    # Resolution alias 찾기
    alias = rule.get("resolution_alias") or get_resolution_alias(cypher)

    if not alias:
        return cq

    # Meeting 관계 추가 필요 여부
    if rule.get("need_meeting") and not has_meeting_relation(cypher):
        cypher = add_meeting_relation(cypher, alias)

    # ORDER BY 추가
    cypher = add_order_by_clause(cypher, rule["order_by"], alias)

    return {**cq, "cypher": cypher}


def main():
    print("=== CQ 쿼리 ORDER BY 추가 ===")

    # 데이터 로드
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data["questions"]
    print(f"총 CQ 수: {len(questions)}")

    # 카테고리별 통계
    categories = {}
    for q in questions:
        cat = q["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\n카테고리별 분포:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}개")

    # 쿼리 처리
    modified_count = 0
    processed = []

    for cq in questions:
        original = cq["cypher"]
        processed_cq = process_query(cq)
        processed.append(processed_cq)

        if processed_cq["cypher"] != original:
            modified_count += 1
            print(f"  수정: {cq['id']} ({cq['category']})")

    print(f"\n수정된 쿼리: {modified_count}개")

    # 결과 저장
    data["questions"] = processed
    data["metadata"]["version"] = "5.1"
    data["metadata"]["sort_added"] = True

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n저장: {OUTPUT_FILE}")

    # 샘플 출력
    print("\n=== 샘플 쿼리 (수정 전 → 후) ===")
    samples = ["CQ001", "CQ056", "CQ071"]
    for sample_id in samples:
        original = next((q for q in questions if q["id"] == sample_id), None)
        modified = next((q for q in processed if q["id"] == sample_id), None)
        if original and modified:
            print(f"\n[{sample_id}] {original['category']}")
            print(f"  전: {original['cypher'][:100]}...")
            print(f"  후: {modified['cypher'][:100]}...")


if __name__ == "__main__":
    main()
