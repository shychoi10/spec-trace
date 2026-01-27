#!/usr/bin/env python3
"""
CQ 쿼리 관계명 버그 수정
- MADEAT → MADE_AT
- SUBMITTEDBY → SUBMITTED_BY
- PRESENTEDAT → PRESENTED_AT
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset.json"
OUTPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset_fixed.json"

# 수정 규칙
FIXES = {
    "MADEAT": "MADE_AT",
    "SUBMITTEDBY": "SUBMITTED_BY",
    "PRESENTEDAT": "PRESENTED_AT",
}


def fix_relationship_names(cypher: str) -> str:
    """관계명 버그 수정"""
    fixed = cypher
    for old, new in FIXES.items():
        # [:MADEAT] → [:MADE_AT] 형태만 수정
        fixed = re.sub(rf'\[:({old})\]', f'[:{new}]', fixed)
    return fixed


def main():
    print("=== CQ 쿼리 관계명 버그 수정 ===")

    # 데이터 로드
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data["questions"]
    print(f"총 CQ 수: {len(questions)}")

    # 수정 전 통계
    print("\n수정 전 통계:")
    for old in FIXES.keys():
        count = sum(1 for q in questions if old in q["cypher"])
        print(f"  {old}: {count}개")

    # 쿼리 수정
    modified = []
    for cq in questions:
        original = cq["cypher"]
        fixed = fix_relationship_names(original)
        modified.append({**cq, "cypher": fixed})

        if fixed != original:
            print(f"  수정: {cq['id']}")

    # 수정 후 통계
    print("\n수정 후 통계:")
    for old, new in FIXES.items():
        old_count = sum(1 for q in modified if old in q["cypher"])
        new_count = sum(1 for q in modified if new in q["cypher"])
        print(f"  {old}: {old_count}개 → {new}: {new_count}개")

    # 결과 저장
    data["questions"] = modified
    data["metadata"]["version"] = "6.0"
    data["metadata"]["relationship_names_fixed"] = True

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n저장: {OUTPUT_FILE}")

    # 샘플 출력
    print("\n=== 샘플 쿼리 (수정 전 → 후) ===")
    samples = ["CQ001", "CQ016", "CQ031"]
    original_questions = {q["id"]: q for q in questions}
    modified_questions = {q["id"]: q for q in modified}

    for sample_id in samples:
        if sample_id in original_questions:
            orig = original_questions[sample_id]["cypher"]
            mod = modified_questions[sample_id]["cypher"]
            print(f"\n[{sample_id}]")
            print(f"  전: ...{orig[40:100]}...")
            print(f"  후: ...{mod[40:100]}...")


if __name__ == "__main__":
    main()
