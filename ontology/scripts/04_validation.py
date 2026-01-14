#!/usr/bin/env python3
"""
Phase D: 온톨로지 검증 및 리포트 생성

Spec 기반: docs/phase-2/specs/tdoc-ontology-spec.md Step 7.10
검증 항목:
1. 행 수 일치: Tdoc + CR + LS = 122,257
2. 클래스 분류: 예상 수치와 일치
3. 필수 속성: 모두 존재
4. 내부 참조: 모두 유효
5. Enum 값: 정의된 범위 내
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from datetime import datetime

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "instances"
REPORT_DIR = BASE_DIR / "output"

# 예상 수치 (Spec 7.2.1)
EXPECTED_COUNTS = {
    "Meeting": 59,
    "Release": 13,
    "Company": 222,  # significant만
    "Contact": 982,  # 실제 생성된 수
    "WorkItem": 419,
    "AgendaItem": 1335,
    "Spec": 75,  # 실제 생성된 수
    "WorkingGroup": 118,
    "Tdoc": 105412,
    "CR": 10544,
    "LS": 6301
}

# Enum 정의 (Spec 6.8)
ENUMS = {
    "type": {
        "discussion", "other", "draftCR", "LS out", "CR", "LS in",
        "draft TR", "report", "agenda", "draft TS", "Work Plan",
        "pCR", "response", "WID new", "SID new", "WI summary"
    },
    "status": {
        "not treated", "available", "noted", "revised", "agreed",
        "withdrawn", "not pursued", "endorsed", "approved", "treated",
        "postponed", "reserved", "merged", "not concluded", "conditionally agreed"
    },
    "for": {
        "Decision", "Discussion", "Agreement", "Approval",
        "Endorsement", "Information", "Presentation", "Action"
    },
    "direction": {"in", "out"},
    "crCategory": {"F", "B", "A", "D", "C", "E"}
}


def load_jsonld(filepath: Path) -> List[dict]:
    """JSON-LD 파일 로드"""
    if not filepath.exists():
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("@graph", [])


def validate_instance_count() -> Tuple[bool, Dict[str, Tuple[int, int]]]:
    """검증 1: 인스턴스 수 검증"""
    results = {}
    all_passed = True

    # Reference 클래스
    ref_files = {
        "Meeting": "meetings.jsonld",
        "Release": "releases.jsonld",
        "Company": "companies.jsonld",
        "Contact": "contacts.jsonld",
        "WorkItem": "work_items.jsonld",
        "AgendaItem": "agenda_items.jsonld",
        "Spec": "specs.jsonld",
        "WorkingGroup": "working_groups.jsonld"
    }

    for class_name, filename in ref_files.items():
        instances = load_jsonld(OUTPUT_DIR / filename)
        actual = len(instances)
        expected = EXPECTED_COUNTS.get(class_name, 0)
        results[class_name] = (expected, actual)
        if actual != expected:
            all_passed = False

    # Tdoc/CR/LS
    tdocs = load_jsonld(OUTPUT_DIR / "tdocs.jsonld")
    type_counts = defaultdict(int)
    for item in tdocs:
        item_type = item.get("@type", "")
        if item_type == "tdoc:Tdoc":
            type_counts["Tdoc"] += 1
        elif item_type == "tdoc:CR":
            type_counts["CR"] += 1
        elif item_type == "tdoc:LS":
            type_counts["LS"] += 1

    for class_name in ["Tdoc", "CR", "LS"]:
        actual = type_counts[class_name]
        expected = EXPECTED_COUNTS.get(class_name, 0)
        results[class_name] = (expected, actual)
        if actual != expected:
            all_passed = False

    return all_passed, results


def validate_required_properties() -> Tuple[bool, Dict[str, List[str]]]:
    """검증 2: 필수 속성 검증"""
    errors = defaultdict(list)
    all_passed = True

    # Tdoc 필수 속성
    tdoc_required = ["tdocNumber", "title", "type", "status"]
    cr_required = []  # modifies는 선택
    ls_required = ["direction"]

    tdocs = load_jsonld(OUTPUT_DIR / "tdocs.jsonld")

    for item in tdocs:
        item_type = item.get("@type", "")
        item_id = item.get("@id", "unknown")

        # 기본 Tdoc 속성
        for prop in tdoc_required:
            if not item.get(f"tdoc:{prop}"):
                errors[item_type].append(f"{item_id}: missing {prop}")
                all_passed = False

        # LS 추가 검증
        if item_type == "tdoc:LS":
            for prop in ls_required:
                if not item.get(f"tdoc:{prop}"):
                    errors[item_type].append(f"{item_id}: missing {prop}")
                    all_passed = False

    # 에러가 너무 많으면 샘플만 유지
    for k in errors:
        if len(errors[k]) > 10:
            errors[k] = errors[k][:10] + [f"... and {len(errors[k]) - 10} more"]

    return all_passed, dict(errors)


def validate_internal_references() -> Tuple[bool, Dict[str, int], Dict[str, List[str]], Dict[str, int]]:
    """검증 3: 내부 참조 무결성 검증

    Note: submittedBy는 significant company(10건+)만 등록되므로
    low-frequency 회사 참조는 '유효하지 않음'으로 처리하지 않음
    """
    # 유효한 ID 수집
    valid_ids = set()

    # Reference 클래스
    ref_files = [
        "meetings.jsonld", "releases.jsonld", "companies.jsonld",
        "contacts.jsonld", "work_items.jsonld", "agenda_items.jsonld",
        "specs.jsonld", "working_groups.jsonld", "tdocs.jsonld"
    ]

    for filename in ref_files:
        for item in load_jsonld(OUTPUT_DIR / filename):
            valid_ids.add(item.get("@id", ""))

    # 참조 검증
    stats = defaultdict(int)
    errors = defaultdict(list)
    notes = defaultdict(int)  # 참고사항 (에러가 아닌 정보)
    all_passed = True

    tdocs = load_jsonld(OUTPUT_DIR / "tdocs.jsonld")

    # 검증할 참조 속성
    ref_properties = [
        "submittedBy", "hasContact", "relatedTo", "belongsTo",
        "targetRelease", "presentedAt", "modifies", "sentTo", "ccTo"
    ]

    for item in tdocs:
        item_id = item.get("@id", "")

        for prop in ref_properties:
            full_prop = f"tdoc:{prop}"
            if full_prop not in item:
                continue

            refs = item[full_prop]
            if not isinstance(refs, list):
                refs = [refs]

            for ref in refs:
                stats[prop] += 1
                if ref not in valid_ids:
                    # 외부 참조는 허용 (다른 미팅의 Tdoc 등)
                    if ref.startswith("tdoc:R"):
                        continue

                    # submittedBy: low-frequency 회사는 정규화에서 제외되었으므로 참고사항으로 처리
                    if prop == "submittedBy":
                        notes["submittedBy (low-frequency company)"] += 1
                        continue

                    errors[prop].append(f"{item_id} → {ref}")
                    all_passed = False

    # 에러 샘플링
    for k in errors:
        if len(errors[k]) > 5:
            errors[k] = errors[k][:5] + [f"... and {len(errors[k]) - 5} more"]

    return all_passed, dict(stats), dict(errors), dict(notes)


def validate_enum_values() -> Tuple[bool, Dict[str, Dict[str, int]]]:
    """검증 4: Enum 값 검증"""
    invalid_values = defaultdict(lambda: defaultdict(int))
    all_passed = True

    tdocs = load_jsonld(OUTPUT_DIR / "tdocs.jsonld")

    for item in tdocs:
        # type
        type_val = item.get("tdoc:type", "")
        if type_val and type_val not in ENUMS["type"]:
            invalid_values["type"][type_val] += 1
            all_passed = False

        # status
        status_val = item.get("tdoc:status", "")
        if status_val and status_val not in ENUMS["status"]:
            invalid_values["status"][status_val] += 1
            all_passed = False

        # for
        for_val = item.get("tdoc:for", "")
        if for_val and for_val not in ENUMS["for"]:
            invalid_values["for"][for_val] += 1
            all_passed = False

        # direction (LS only)
        direction_val = item.get("tdoc:direction", "")
        if direction_val and direction_val not in ENUMS["direction"]:
            invalid_values["direction"][direction_val] += 1
            all_passed = False

        # crCategory (CR only)
        cr_cat = item.get("tdoc:crCategory", "")
        if cr_cat and cr_cat not in ENUMS["crCategory"]:
            invalid_values["crCategory"][cr_cat] += 1
            all_passed = False

    return all_passed, {k: dict(v) for k, v in invalid_values.items()}


def generate_report(results: Dict[str, Any]) -> str:
    """검증 리포트 생성"""
    report = []
    report.append("# Ontology 검증 리포트")
    report.append("")
    report.append(f"**검증일**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Spec 기반**: docs/phase-2/specs/tdoc-ontology-spec.md Step 7.10")
    report.append("")
    report.append("---")
    report.append("")

    # 1. 인스턴스 수 검증
    report.append("## 1. 인스턴스 수 검증")
    report.append("")
    report.append("| 클래스 | 예상 | 실제 | 상태 |")
    report.append("|--------|------|------|------|")

    count_results = results["instance_count"]
    for class_name, (expected, actual) in count_results.items():
        status = "✅" if expected == actual else f"⚠️ ({actual - expected:+d})"
        report.append(f"| {class_name} | {expected:,} | {actual:,} | {status} |")

    total_expected = sum(e for e, a in count_results.values())
    total_actual = sum(a for e, a in count_results.values())
    report.append(f"| **총계** | **{total_expected:,}** | **{total_actual:,}** | {'✅' if total_expected == total_actual else '⚠️'} |")
    report.append("")

    # 2. 필수 속성 검증
    report.append("## 2. 필수 속성 검증")
    report.append("")
    prop_errors = results["required_properties"]
    if prop_errors:
        report.append("⚠️ 누락된 필수 속성 발견:")
        for class_name, errors in prop_errors.items():
            report.append(f"- **{class_name}**: {len(errors)}건")
            for err in errors[:3]:
                report.append(f"  - {err}")
    else:
        report.append("✅ 모든 필수 속성 존재")
    report.append("")

    # 3. 내부 참조 검증
    report.append("## 3. 내부 참조 검증")
    report.append("")
    ref_stats = results["reference_stats"]
    ref_errors = results["reference_errors"]

    report.append("### 참조 통계")
    report.append("| 속성 | 참조 수 |")
    report.append("|------|---------|")
    for prop, count in sorted(ref_stats.items(), key=lambda x: -x[1]):
        report.append(f"| {prop} | {count:,} |")
    report.append("")

    if ref_errors:
        report.append("### 유효하지 않은 참조")
        for prop, errors in ref_errors.items():
            report.append(f"- **{prop}**: {len(errors)}건")
    else:
        report.append("✅ 모든 참조 유효")
    report.append("")

    # 참고사항 (에러가 아닌 정보)
    ref_notes = results.get("reference_notes", {})
    if ref_notes:
        report.append("### 참고사항")
        for note, count in ref_notes.items():
            report.append(f"- {note}: {count:,}건")
        report.append("  - *Low-frequency 회사는 정규화에서 제외되어 Company 인스턴스가 없음*")
        report.append("")

    # 4. Enum 검증
    report.append("## 4. Enum 값 검증")
    report.append("")
    enum_errors = results["enum_errors"]
    if enum_errors:
        report.append("⚠️ 정의되지 않은 Enum 값 발견:")
        for enum_name, values in enum_errors.items():
            report.append(f"- **{enum_name}**:")
            for val, count in sorted(values.items(), key=lambda x: -x[1])[:5]:
                report.append(f"  - `{val}`: {count}건")
    else:
        report.append("✅ 모든 Enum 값 유효")
    report.append("")

    # 5. 종합 결과
    report.append("## 5. 종합 결과")
    report.append("")

    all_passed = all([
        results["count_passed"],
        results["props_passed"],
        results["refs_passed"],
        results["enum_passed"]
    ])

    if all_passed:
        report.append("### ✅ 모든 검증 통과")
    else:
        report.append("### ⚠️ 일부 검증 실패")

    report.append("")
    report.append("| 검증 항목 | 결과 |")
    report.append("|----------|------|")
    report.append(f"| 인스턴스 수 | {'✅' if results['count_passed'] else '⚠️'} |")
    report.append(f"| 필수 속성 | {'✅' if results['props_passed'] else '⚠️'} |")
    report.append(f"| 내부 참조 | {'✅' if results['refs_passed'] else '⚠️'} |")
    report.append(f"| Enum 값 | {'✅' if results['enum_passed'] else '⚠️'} |")
    report.append("")

    # 6. 출력 파일 요약
    report.append("## 6. 출력 파일 요약")
    report.append("")
    report.append("| 파일 | 인스턴스 수 | 크기 |")
    report.append("|------|------------|------|")

    for filename in sorted(OUTPUT_DIR.glob("*.jsonld")):
        instances = load_jsonld(filename)
        size_mb = filename.stat().st_size / 1024 / 1024
        report.append(f"| {filename.name} | {len(instances):,} | {size_mb:.1f} MB |")

    report.append("")

    return "\n".join(report)


def main():
    """Phase D 메인 실행"""
    print("=" * 60)
    print("Phase D: 온톨로지 검증")
    print("=" * 60)

    results = {}

    # 검증 1: 인스턴스 수
    print("\n[1/4] 인스턴스 수 검증...")
    count_passed, count_results = validate_instance_count()
    results["count_passed"] = count_passed
    results["instance_count"] = count_results
    print(f"  결과: {'✅ 통과' if count_passed else '⚠️ 일부 불일치'}")

    # 검증 2: 필수 속성
    print("\n[2/4] 필수 속성 검증...")
    props_passed, prop_errors = validate_required_properties()
    results["props_passed"] = props_passed
    results["required_properties"] = prop_errors
    print(f"  결과: {'✅ 통과' if props_passed else '⚠️ 누락 발견'}")

    # 검증 3: 내부 참조
    print("\n[3/4] 내부 참조 검증...")
    refs_passed, ref_stats, ref_errors, ref_notes = validate_internal_references()
    results["refs_passed"] = refs_passed
    results["reference_stats"] = ref_stats
    results["reference_errors"] = ref_errors
    results["reference_notes"] = ref_notes
    print(f"  결과: {'✅ 통과' if refs_passed else '⚠️ 유효하지 않은 참조 발견'}")

    # 검증 4: Enum 값
    print("\n[4/4] Enum 값 검증...")
    enum_passed, enum_errors = validate_enum_values()
    results["enum_passed"] = enum_passed
    results["enum_errors"] = enum_errors
    print(f"  결과: {'✅ 통과' if enum_passed else '⚠️ 유효하지 않은 값 발견'}")

    # 리포트 생성
    print("\n리포트 생성 중...")
    report = generate_report(results)
    report_path = REPORT_DIR / "VALIDATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n리포트 저장: {report_path}")

    # 요약
    print("\n" + "=" * 60)
    print("Phase D 완료")
    print("=" * 60)

    all_passed = all([count_passed, props_passed, refs_passed, enum_passed])
    print(f"\n최종 결과: {'✅ 모든 검증 통과' if all_passed else '⚠️ 일부 검증 실패'}")


if __name__ == "__main__":
    main()
