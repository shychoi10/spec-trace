#!/usr/bin/env python3
"""
Validate CQ Test Cases Against Parsed JSON Data (Without Neo4j).

Neo4j 없이 파싱된 JSON 데이터를 직접 쿼리하여 CQ 검증.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
PARSED_DIR = BASE_DIR / "ontology" / "output" / "parsed_reports" / "v2"
TEST_DATASET = BASE_DIR / "logs" / "phase-3" / "cq_test_dataset_100.json"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"


def load_all_data():
    """Load all parsed data into memory for querying."""
    data = {
        "meetings": [],
        "agreements": [],
        "conclusions": [],
        "working_assumptions": [],
        "session_notes": [],
        "fl_summaries": [],
        "moderator_summaries": [],
        "agenda_topics": defaultdict(dict),
        "companies": Counter()
    }

    for f in sorted(PARSED_DIR.glob("RAN1_*_v2.json")):
        with open(f) as fp:
            parsed = json.load(fp)
            meeting_id = parsed["meeting_id"]
            data["meetings"].append(meeting_id)

            # TOC
            for toc in parsed.get("toc_entries", []):
                agenda = toc.get("agenda_number", "")
                title = toc.get("title", "")
                if agenda and title:
                    data["agenda_topics"][meeting_id][agenda] = title

            # Agreements
            for agr in parsed["agreements"]:
                data["agreements"].append({
                    "meeting": meeting_id,
                    "id": agr["decision_id"],
                    "agenda": agr["agenda_item"],
                    "content": agr["content"],
                    "tdocs": agr.get("referenced_tdocs", [])
                })

            # Conclusions
            for conc in parsed["conclusions"]:
                data["conclusions"].append({
                    "meeting": meeting_id,
                    "id": conc["decision_id"],
                    "agenda": conc["agenda_item"],
                    "content": conc["content"]
                })

            # Working Assumptions
            for wa in parsed["working_assumptions"]:
                data["working_assumptions"].append({
                    "meeting": meeting_id,
                    "id": wa["decision_id"],
                    "agenda": wa["agenda_item"],
                    "content": wa["content"]
                })

            # Session Notes
            for sn in parsed["session_notes"]:
                data["session_notes"].append({
                    "meeting": meeting_id,
                    "tdoc": sn.get("tdoc_number", ""),
                    "title": sn.get("title", ""),
                    "agenda": sn.get("agenda_item", ""),
                    "company": sn.get("company", "")
                })
                if sn.get("company"):
                    data["companies"][sn.get("company")] += 1

            # FL Summaries
            for fl in parsed["fl_summaries"]:
                data["fl_summaries"].append({
                    "meeting": meeting_id,
                    "tdoc": fl.get("tdoc_number", ""),
                    "title": fl.get("title", ""),
                    "agenda": fl.get("agenda_item", ""),
                    "company": fl.get("company", "")
                })
                if fl.get("company"):
                    data["companies"][fl.get("company")] += 1

            # Moderator Summaries
            for ms in parsed["moderator_summaries"]:
                data["moderator_summaries"].append({
                    "meeting": meeting_id,
                    "tdoc": ms.get("tdoc_number", ""),
                    "title": ms.get("title", ""),
                    "agenda": ms.get("agenda_item", ""),
                    "company": ms.get("company", "")
                })
                if ms.get("company"):
                    data["companies"][ms.get("company")] += 1

    return data


def execute_cq(cq_type: str, params: dict, data: dict) -> dict:
    """Execute a CQ query against parsed data."""
    results = []

    # CQ1-1: 특정 회의의 Agreement
    if cq_type == "CQ1-1":
        meeting = params.get("meeting", "")
        results = [a for a in data["agreements"] if a["meeting"] == meeting]
        return {
            "count": len(results),
            "sample": [{"id": r["id"], "content": r["content"][:100]} for r in results[:5]]
        }

    # CQ1-2: 특정 회의의 Conclusion
    elif cq_type == "CQ1-2":
        meeting = params.get("meeting", "")
        results = [c for c in data["conclusions"] if c["meeting"] == meeting]
        return {
            "count": len(results),
            "sample": [{"id": r["id"], "content": r["content"][:100]} for r in results[:5]]
        }

    # CQ1-3: 특정 회의의 Working Assumption
    elif cq_type == "CQ1-3":
        meeting = params.get("meeting", "")
        results = [w for w in data["working_assumptions"] if w["meeting"] == meeting]
        return {
            "count": len(results),
            "sample": [{"id": r["id"], "content": r["content"][:100]} for r in results[:5]]
        }

    # CQ1-4: 회의 + 아젠다 조합 (prefix 매칭 지원: "8.5"로 검색 시 "8.5.1", "8.5.2" 등 포함)
    elif cq_type == "CQ1-4":
        meeting = params.get("meeting", "")
        agenda = params.get("agenda", "")
        all_resolutions = data["agreements"] + data["conclusions"] + data["working_assumptions"]
        # 정확히 일치하거나, 하위 아젠다인 경우 포함 (예: "8.5" -> "8.5", "8.5.1", "8.5.2" 등)
        results = [r for r in all_resolutions
                   if r["meeting"] == meeting and
                   (r["agenda"] == agenda or r["agenda"].startswith(agenda + "."))]
        return {
            "count": len(results),
            "sample": [{"id": r["id"], "agenda": r["agenda"], "type": "Resolution"} for r in results[:5]]
        }

    # CQ1-5: 키워드 검색
    elif cq_type == "CQ1-5":
        keyword = params.get("keyword", "").lower()
        all_resolutions = data["agreements"] + data["conclusions"] + data["working_assumptions"]
        results = [r for r in all_resolutions if keyword in r["content"].lower()]
        return {
            "count": len(results),
            "sample": [{"id": r["id"]} for r in results[:5]]
        }

    # CQ2-1: 특정 Resolution의 Tdoc 참조
    elif cq_type == "CQ2-1":
        resolution_id = params.get("resolution_id", "")
        for a in data["agreements"]:
            if a["id"] == resolution_id:
                return {
                    "count": len(a["tdocs"]),
                    "sample": [{"tdoc": t} for t in a["tdocs"][:10]]
                }
        return {"count": 0, "sample": []}

    # CQ2-2: Tdoc 참조 많은 Resolution
    elif cq_type == "CQ2-2":
        meeting = params.get("meeting")
        min_refs = params.get("min_refs", 5)

        if meeting:
            candidates = [a for a in data["agreements"] if a["meeting"] == meeting and len(a["tdocs"]) >= min_refs]
        else:
            candidates = [a for a in data["agreements"] if len(a["tdocs"]) >= min_refs]

        candidates.sort(key=lambda x: len(x["tdocs"]), reverse=True)
        return {
            "count": len(candidates),
            "sample": [{"id": r["id"], "tdoc_count": len(r["tdocs"])} for r in candidates[:10]]
        }

    # CQ3-1: 특정 회사의 FL Summary
    elif cq_type == "CQ3-1":
        company = params.get("company", "")
        results = [s for s in data["fl_summaries"] if company.lower() in s["company"].lower()]
        return {
            "count": len(results),
            "sample": [{"tdoc": r["tdoc"], "meeting": r["meeting"]} for r in results[:10]]
        }

    # CQ3-2: 회사별 Summary 순위
    elif cq_type == "CQ3-2":
        limit = params.get("limit", 10)
        company_counts = Counter()
        for s in data["fl_summaries"] + data["moderator_summaries"]:
            if s["company"] and s["company"] != "UNKNOWN":
                company_counts[s["company"]] += 1
        top = company_counts.most_common(limit)
        return {
            "count": len(top),
            "sample": [{"company": c, "summary_count": n} for c, n in top]
        }

    # CQ3-3: 두 회사 비교
    elif cq_type == "CQ3-3":
        c1 = params.get("company1", "")
        c2 = params.get("company2", "")
        all_summaries = data["fl_summaries"] + data["moderator_summaries"]

        count1 = len([s for s in all_summaries if c1.lower() in s["company"].lower()])
        count2 = len([s for s in all_summaries if c2.lower() in s["company"].lower()])

        return {
            "count": 2,
            "sample": [
                {"company": c1, "count": count1},
                {"company": c2, "count": count2}
            ]
        }

    # CQ4-1: 특정 회의의 Session Notes
    elif cq_type == "CQ4-1":
        meeting = params.get("meeting", "")
        results = [s for s in data["session_notes"] if s["meeting"] == meeting]
        return {
            "count": len(results),
            "sample": [{"tdoc": r["tdoc"], "agenda": r["agenda"]} for r in results[:10]]
        }

    # CQ4-2: 특정 회의의 FL Summary
    elif cq_type == "CQ4-2":
        meeting = params.get("meeting", "")
        results = [s for s in data["fl_summaries"] if s["meeting"] == meeting]
        return {
            "count": len(results),
            "sample": [{"tdoc": r["tdoc"], "title": r["title"][:50]} for r in results[:10]]
        }

    # CQ4-3: 특정 회의의 Moderator Summary
    elif cq_type == "CQ4-3":
        meeting = params.get("meeting", "")
        results = [s for s in data["moderator_summaries"] if s["meeting"] == meeting]
        return {
            "count": len(results),
            "sample": [{"tdoc": r["tdoc"], "title": r["title"][:50]} for r in results[:10]]
        }

    # CQ4-4: Ad-hoc Chair
    elif cq_type == "CQ4-4":
        meeting = params.get("meeting", "")
        results = [s for s in data["session_notes"] if s["meeting"] == meeting and s["company"]]
        return {
            "count": len(results),
            "sample": [{"tdoc": r["tdoc"], "company": r["company"]} for r in results[:10]]
        }

    # CQ6-1: 회의별 Resolution 추이
    elif cq_type == "CQ6-1":
        meeting_counts = Counter()
        all_resolutions = data["agreements"] + data["conclusions"] + data["working_assumptions"]
        for r in all_resolutions:
            meeting_counts[r["meeting"]] += 1

        sorted_meetings = sorted(meeting_counts.items(), key=lambda x: x[0])
        return {
            "count": len(sorted_meetings),
            "sample": [{"meeting": m, "resolutions": c} for m, c in sorted_meetings[:20]]
        }

    # CQ6-2: Resolution 유형별 분포
    elif cq_type == "CQ6-2":
        scope = params.get("scope")

        if scope:
            agr_count = len([a for a in data["agreements"] if a["meeting"] == scope])
            con_count = len([c for c in data["conclusions"] if c["meeting"] == scope])
            wa_count = len([w for w in data["working_assumptions"] if w["meeting"] == scope])
        else:
            agr_count = len(data["agreements"])
            con_count = len(data["conclusions"])
            wa_count = len(data["working_assumptions"])

        total = agr_count + con_count + wa_count
        return {
            "count": 3,
            "sample": [
                {"type": "Agreement", "count": agr_count, "percentage": round(100*agr_count/total, 1) if total > 0 else 0},
                {"type": "Conclusion", "count": con_count, "percentage": round(100*con_count/total, 1) if total > 0 else 0},
                {"type": "WorkingAssumption", "count": wa_count, "percentage": round(100*wa_count/total, 1) if total > 0 else 0}
            ]
        }

    # CQ6-3: 통계
    elif cq_type == "CQ6-3":
        stat_type = params.get("stat_type", "avg")

        meeting_counts = Counter()
        all_resolutions = data["agreements"] + data["conclusions"] + data["working_assumptions"]
        for r in all_resolutions:
            meeting_counts[r["meeting"]] += 1

        counts = list(meeting_counts.values())

        if stat_type == "avg":
            avg = round(sum(counts) / len(counts), 1) if counts else 0
            return {
                "count": 1,
                "sample": [{"avg_resolutions": avg, "min": min(counts) if counts else 0, "max": max(counts) if counts else 0}]
            }
        elif stat_type == "max":
            top = sorted(meeting_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            return {
                "count": len(top),
                "sample": [{"meeting": m, "resolutions": c} for m, c in top]
            }
        elif stat_type == "min":
            bottom = sorted(meeting_counts.items(), key=lambda x: x[1])[:5]
            return {
                "count": len(bottom),
                "sample": [{"meeting": m, "resolutions": c} for m, c in bottom]
            }
        elif stat_type == "ratio":
            agr = len(data["agreements"])
            con = len(data["conclusions"])
            wa = len(data["working_assumptions"])
            return {
                "count": 3,
                "sample": [
                    {"type": "Agreement", "count": agr},
                    {"type": "Conclusion", "count": con},
                    {"type": "WorkingAssumption", "count": wa}
                ]
            }
        elif stat_type == "ref_ratio":
            with_refs = len([a for a in data["agreements"] if a["tdocs"]])
            total = len(data["agreements"])
            return {
                "count": 1,
                "sample": [{"with_refs": with_refs, "total": total, "percentage": round(100*with_refs/total, 1) if total > 0 else 0}]
            }

    return {"count": 0, "sample": []}


def generate_answer(cq_type: str, question: str, result: dict) -> str:
    """Generate natural language answer from query result."""
    count = result.get("count", 0)
    sample = result.get("sample", [])

    if count == 0:
        return "해당 조건에 맞는 데이터가 없습니다."

    if "CQ1-1" in cq_type:
        if sample:
            return f"총 {count}개의 Agreement가 합의되었습니다. 예: '{sample[0].get('id', '')}' - \"{sample[0].get('content', '')[:60]}...\""
        return f"총 {count}개의 Agreement가 합의되었습니다."

    elif "CQ1-2" in cq_type:
        return f"총 {count}개의 Conclusion이 도출되었습니다."

    elif "CQ1-3" in cq_type:
        return f"총 {count}개의 Working Assumption이 설정되었습니다."

    elif "CQ1-4" in cq_type:
        return f"해당 회의/Agenda에서 총 {count}개의 Resolution이 있습니다."

    elif "CQ1-5" in cq_type:
        return f"관련 Resolution이 총 {count}개 발견되었습니다."

    elif "CQ2-1" in cq_type:
        return f"해당 Resolution이 참조한 Tdoc은 총 {count}개입니다."

    elif "CQ2-2" in cq_type:
        if sample:
            top = sample[0]
            return f"총 {count}개의 Resolution이 조건에 해당합니다. 1위: {top.get('id', '')}로 {top.get('tdoc_count', 0)}개의 Tdoc을 참조합니다."
        return f"총 {count}개의 Resolution이 조건에 해당합니다."

    elif "CQ3-1" in cq_type:
        return f"해당 회사의 FL Summary는 총 {count}개입니다."

    elif "CQ3-2" in cq_type:
        if sample:
            top = sample[0]
            return f"1위: {top.get('company', '')}로 {top.get('summary_count', 0)}개의 Summary를 작성했습니다."
        return f"총 {count}개 회사의 Summary 현황이 있습니다."

    elif "CQ3-3" in cq_type:
        if len(sample) >= 2:
            return f"비교 결과: {sample[0]['company']}는 {sample[0]['count']}개, {sample[1]['company']}는 {sample[1]['count']}개입니다."
        return "비교 데이터가 있습니다."

    elif "CQ4-1" in cq_type:
        return f"Session Notes는 총 {count}개입니다."

    elif "CQ4-2" in cq_type:
        return f"FL Summary는 총 {count}개입니다."

    elif "CQ4-3" in cq_type:
        return f"Moderator Summary는 총 {count}개입니다."

    elif "CQ4-4" in cq_type:
        if count == 0:
            return "해당 회의에서 Ad-hoc Chair 정보가 없습니다."
        return f"Ad-hoc Session Chair 정보가 {count}건 있습니다."

    elif "CQ6-1" in cq_type:
        if sample:
            return f"총 {count}개 회의의 Resolution 추이입니다. 예: {sample[0]['meeting']} - {sample[0]['resolutions']}개"
        return f"총 {count}개 회의의 추이 데이터입니다."

    elif "CQ6-2" in cq_type:
        if sample:
            s = sample[0]
            return f"Resolution 유형별 분포: {s['type']} {s['count']}개 ({s['percentage']}%)"
        return "Resolution 유형별 분포 데이터입니다."

    elif "CQ6-3" in cq_type:
        if sample:
            s = sample[0]
            if "avg_resolutions" in s:
                return f"회의당 평균 {s['avg_resolutions']}개, 최소 {s['min']}개, 최대 {s['max']}개입니다."
            elif "meeting" in s:
                return f"회의 {s['meeting']}에서 {s['resolutions']}개의 Resolution이 있습니다."
            elif "percentage" in s:
                return f"Tdoc을 참조하는 Agreement 비율: {s['percentage']}% ({s['with_refs']}/{s['total']})"
        return "통계 데이터입니다."

    return f"총 {count}개의 결과가 있습니다."


def main():
    print("=" * 70)
    print("CQ VALIDATION WITHOUT NEO4J")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")

    # Load data
    print("\n[1/4] Loading parsed data...")
    data = load_all_data()
    print(f"  - Meetings: {len(data['meetings'])}")
    print(f"  - Agreements: {len(data['agreements'])}")
    print(f"  - Conclusions: {len(data['conclusions'])}")
    print(f"  - Working Assumptions: {len(data['working_assumptions'])}")
    print(f"  - FL Summaries: {len(data['fl_summaries'])}")
    print(f"  - Moderator Summaries: {len(data['moderator_summaries'])}")
    print(f"  - Session Notes: {len(data['session_notes'])}")

    # Load test cases
    print("\n[2/4] Loading test dataset...")
    with open(TEST_DATASET) as f:
        test_data = json.load(f)
    test_cases = test_data["test_cases"]
    print(f"  - Test cases: {len(test_cases)}")

    # Execute queries
    print("\n[3/4] Executing CQ queries...")
    results = []
    passed = 0
    warned = 0
    failed = 0

    for tc in test_cases:
        cq_type = tc["cq_type"]
        params = tc["parameters"]
        question = tc["question"]

        result = execute_cq(cq_type, params, data)
        count = result.get("count", 0)

        if count > 0:
            status = "PASS"
            passed += 1
        elif cq_type in ["CQ4-3", "CQ4-4"]:  # Moderator Summary, Ad-hoc Chair may not exist in some meetings
            status = "WARN"
            warned += 1
        else:
            status = "FAIL"
            failed += 1

        answer = generate_answer(cq_type, question, result)

        results.append({
            "test_case_id": tc["id"],
            "cq_type": cq_type,
            "question": question,
            "parameters": params,
            "status": status,
            "result_count": count,
            "sample": result.get("sample", [])[:3],
            "natural_language_answer": answer
        })

    # Save results
    print("\n[4/4] Saving results...")

    # Validation results
    validation_output = {
        "generated_at": datetime.now().isoformat(),
        "version": "2.0-realistic",
        "metrics": {
            "total_tests": len(results),
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "pass_rate": round(100 * passed / len(results), 1),
            "pass_warn_rate": round(100 * (passed + warned) / len(results), 1)
        },
        "results": results
    }

    val_file = OUTPUT_DIR / "cq_validation_results_100.json"
    with open(val_file, 'w', encoding='utf-8') as f:
        json.dump(validation_output, f, ensure_ascii=False, indent=2)
    print(f"  - Validation results: {val_file}")

    # NL Answers
    nl_output = {
        "generated_at": datetime.now().isoformat(),
        "version": "2.0-realistic",
        "total_cases": len(results),
        "results": [{
            "test_case_id": r["test_case_id"],
            "cq_type": r["cq_type"],
            "question": r["question"],
            "status": r["status"],
            "result_count": r["result_count"],
            "sample": r["sample"],
            "natural_language_answer": r["natural_language_answer"]
        } for r in results]
    }

    nl_file = OUTPUT_DIR / "cq_nl_answers_100.json"
    with open(nl_file, 'w', encoding='utf-8') as f:
        json.dump(nl_output, f, ensure_ascii=False, indent=2)
    print(f"  - NL Answers: {nl_file}")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"  Total: {len(results)}")
    print(f"  Passed: {passed} ({round(100 * passed / len(results), 1)}%)")
    print(f"  Warned: {warned}")
    print(f"  Failed: {failed}")

    # By CQ type
    print("\n  By CQ Type:")
    cq_stats = defaultdict(lambda: {"pass": 0, "warn": 0, "fail": 0})
    for r in results:
        cq_stats[r["cq_type"]][r["status"].lower()] += 1

    for cq_type in sorted(cq_stats.keys()):
        stats = cq_stats[cq_type]
        status = "✅" if stats["fail"] == 0 else ("⚠️" if stats["pass"] > 0 else "❌")
        print(f"    {cq_type}: {status} (P:{stats['pass']} W:{stats['warn']} F:{stats['fail']})")

    # Sample Q&A
    print("\n" + "=" * 70)
    print("SAMPLE Q&A PAIRS")
    print("=" * 70)

    for r in results[:5]:
        print(f"\n[{r['test_case_id']}] {r['cq_type']} - {r['status']}")
        print(f"  Q: {r['question'][:70]}...")
        print(f"  A: {r['natural_language_answer']}")

    return results


if __name__ == "__main__":
    main()
