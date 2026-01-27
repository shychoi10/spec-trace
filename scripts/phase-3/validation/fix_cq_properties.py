#!/usr/bin/env python3
"""
CQ 쿼리 속성명 버그 수정
- c.uri → c.id
- t.tdocId → t.tdocNumber
- t.decision → t.status
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset.json"
OUTPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset_fixed.json"

def fix_properties(cypher: str) -> str:
    """속성명 버그 수정"""
    # c.uri → c.id (Company node)
    cypher = cypher.replace("c.uri", "c.id")
    # t.tdocId → t.tdocNumber (Tdoc node)
    cypher = cypher.replace("t.tdocId", "t.tdocNumber")
    # t.decision → t.status
    cypher = cypher.replace("t.decision", "t.status")
    return cypher


def main():
    print("=== CQ 쿼리 속성명 버그 수정 ===")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data["questions"]
    print(f"총 CQ 수: {len(questions)}")

    # Count occurrences before
    uri_count = sum(1 for q in questions if "c.uri" in q["cypher"])
    tdocId_count = sum(1 for q in questions if "t.tdocId" in q["cypher"])
    decision_count = sum(1 for q in questions if "t.decision" in q["cypher"])

    print(f"\n수정 전:")
    print(f"  c.uri: {uri_count}개")
    print(f"  t.tdocId: {tdocId_count}개")
    print(f"  t.decision: {decision_count}개")

    # Fix
    modified = []
    for cq in questions:
        fixed_cypher = fix_properties(cq["cypher"])
        modified.append({**cq, "cypher": fixed_cypher})

    # Count occurrences after
    uri_count_after = sum(1 for q in modified if "c.uri" in q["cypher"])
    tdocId_count_after = sum(1 for q in modified if "t.tdocId" in q["cypher"])
    decision_count_after = sum(1 for q in modified if "t.decision" in q["cypher"])
    id_count = sum(1 for q in modified if "c.id" in q["cypher"])
    tdocNumber_count = sum(1 for q in modified if "t.tdocNumber" in q["cypher"])
    status_count = sum(1 for q in modified if "t.status" in q["cypher"])

    print(f"\n수정 후:")
    print(f"  c.uri → c.id: {uri_count_after} → {id_count}개")
    print(f"  t.tdocId → t.tdocNumber: {tdocId_count_after} → {tdocNumber_count}개")
    print(f"  t.decision → t.status: {decision_count_after} → {status_count}개")

    # Save
    data["questions"] = modified
    data["metadata"]["version"] = "7.0"
    data["metadata"]["property_names_fixed"] = True

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n저장: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
