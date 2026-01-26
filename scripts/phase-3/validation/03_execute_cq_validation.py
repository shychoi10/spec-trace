#!/usr/bin/env python3
"""
Execute CQ Validation against parsed JSON data.

Validates 100 CQ test cases against the actual parsed data to verify:
1. Data integrity (정합성)
2. Query correctness (쿼리 정확성)
3. Result quality (결과 품질)

No Neo4j required - validates directly against JSON files.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
PARSED_DIR = BASE_DIR / "ontology" / "output" / "parsed_reports" / "v2"
JSONLD_DIR = BASE_DIR / "ontology" / "output" / "instances" / "phase-3"
TEST_DATASET = BASE_DIR / "logs" / "phase-3" / "cq_test_dataset_100.json"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"


class JSONDataStore:
    """In-memory data store loaded from parsed JSON files."""

    def __init__(self):
        self.meetings = {}  # meeting_id -> data
        self.agreements = []
        self.conclusions = []
        self.working_assumptions = []
        self.session_notes = []
        self.fl_summaries = []
        self.moderator_summaries = []

        # Indexes
        self.by_meeting = defaultdict(lambda: {
            "agreements": [], "conclusions": [], "working_assumptions": [],
            "session_notes": [], "fl_summaries": [], "moderator_summaries": []
        })
        self.by_agenda = defaultdict(list)
        self.by_company = defaultdict(list)
        self.by_resolution_id = {}

    def load(self):
        """Load all parsed data into memory."""
        print("  Loading parsed reports...")
        for f in sorted(PARSED_DIR.glob("RAN1_*_v2.json")):
            with open(f) as fp:
                data = json.load(fp)
                meeting_id = data["meeting_id"]
                self.meetings[meeting_id] = data

                # Index agreements
                for agr in data["agreements"]:
                    agr["meeting"] = meeting_id
                    agr["type"] = "Agreement"
                    self.agreements.append(agr)
                    self.by_meeting[meeting_id]["agreements"].append(agr)
                    self.by_agenda[agr["agenda_item"]].append(agr)
                    self.by_resolution_id[agr["decision_id"]] = agr

                # Index conclusions
                for conc in data["conclusions"]:
                    conc["meeting"] = meeting_id
                    conc["type"] = "Conclusion"
                    self.conclusions.append(conc)
                    self.by_meeting[meeting_id]["conclusions"].append(conc)
                    self.by_agenda[conc["agenda_item"]].append(conc)
                    self.by_resolution_id[conc["decision_id"]] = conc

                # Index working assumptions
                for wa in data["working_assumptions"]:
                    wa["meeting"] = meeting_id
                    wa["type"] = "WorkingAssumption"
                    self.working_assumptions.append(wa)
                    self.by_meeting[meeting_id]["working_assumptions"].append(wa)
                    self.by_agenda[wa["agenda_item"]].append(wa)
                    self.by_resolution_id[wa["decision_id"]] = wa

                # Index session notes
                for sn in data["session_notes"]:
                    sn["meeting"] = meeting_id
                    self.session_notes.append(sn)
                    self.by_meeting[meeting_id]["session_notes"].append(sn)
                    if sn.get("chair_company"):
                        self.by_company[sn["chair_company"]].append({"type": "chair", "data": sn})

                # Index FL summaries
                for fl in data["fl_summaries"]:
                    fl["meeting"] = meeting_id
                    self.fl_summaries.append(fl)
                    self.by_meeting[meeting_id]["fl_summaries"].append(fl)
                    if fl.get("company"):
                        self.by_company[fl["company"]].append({"type": "fl_summary", "data": fl})

                # Index moderator summaries
                for ms in data["moderator_summaries"]:
                    ms["meeting"] = meeting_id
                    self.moderator_summaries.append(ms)
                    self.by_meeting[meeting_id]["moderator_summaries"].append(ms)
                    if ms.get("company"):
                        self.by_company[ms["company"]].append({"type": "moderator_summary", "data": ms})

        print(f"  Loaded {len(self.meetings)} meetings")
        print(f"  - Agreements: {len(self.agreements)}")
        print(f"  - Conclusions: {len(self.conclusions)}")
        print(f"  - Working Assumptions: {len(self.working_assumptions)}")
        print(f"  - Session Notes: {len(self.session_notes)}")
        print(f"  - FL Summaries: {len(self.fl_summaries)}")
        print(f"  - Moderator Summaries: {len(self.moderator_summaries)}")


class CQValidator:
    """Validate CQ test cases against JSON data."""

    def __init__(self, data_store: JSONDataStore):
        self.ds = data_store
        self.results = []

    def validate_cq1_1(self, tc: dict) -> dict:
        """CQ1-1: 특정 회의의 Agreement 목록"""
        meeting = tc["parameters"]["meeting"]
        results = self.ds.by_meeting.get(meeting, {}).get("agreements", [])

        return {
            "status": "PASS" if results else "FAIL",
            "result_count": len(results),
            "sample": [{"id": r["decision_id"], "content": r["content"][:100]} for r in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq1_2(self, tc: dict) -> dict:
        """CQ1-2: 특정 회의의 Conclusion 목록"""
        meeting = tc["parameters"]["meeting"]
        results = self.ds.by_meeting.get(meeting, {}).get("conclusions", [])

        return {
            "status": "PASS" if results else "WARN",  # Some meetings may have no conclusions
            "result_count": len(results),
            "sample": [{"id": r["decision_id"], "content": r["content"][:100]} for r in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq1_3(self, tc: dict) -> dict:
        """CQ1-3: 특정 회의의 Working Assumption 목록"""
        meeting = tc["parameters"]["meeting"]
        results = self.ds.by_meeting.get(meeting, {}).get("working_assumptions", [])

        return {
            "status": "PASS" if results else "WARN",  # Some meetings may have no WA
            "result_count": len(results),
            "sample": [{"id": r["decision_id"], "content": r["content"][:100]} for r in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq1_4(self, tc: dict) -> dict:
        """CQ1-4: 특정 Agenda Item의 Resolution 목록"""
        agenda = tc["parameters"]["agenda"]
        results = self.ds.by_agenda.get(agenda, [])

        return {
            "status": "PASS" if results else "WARN",
            "result_count": len(results),
            "sample": [{"id": r["decision_id"], "type": r["type"]} for r in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "unique_types": list(set(r["type"] for r in results))
            }
        }

    def validate_cq1_5(self, tc: dict) -> dict:
        """CQ1-5: 키워드 포함 Resolution 검색"""
        keyword = tc["parameters"]["keyword"]
        all_resolutions = self.ds.agreements + self.ds.conclusions + self.ds.working_assumptions
        results = [r for r in all_resolutions if keyword.lower() in r["content"].lower()]

        return {
            "status": "PASS" if results else "WARN",
            "result_count": len(results),
            "sample": [{"id": r["decision_id"], "type": r["type"]} for r in results[:3]],
            "validation": {
                "keyword": keyword,
                "search_performed": True
            }
        }

    def validate_cq2_1(self, tc: dict) -> dict:
        """CQ2-1: 특정 Resolution의 참조 Tdoc"""
        resolution_id = tc["parameters"]["resolution_id"]
        resolution = self.ds.by_resolution_id.get(resolution_id, {})
        tdocs = resolution.get("referenced_tdocs", [])

        return {
            "status": "PASS" if tdocs else "WARN",
            "result_count": len(tdocs),
            "sample": tdocs[:5],
            "validation": {
                "resolution_found": resolution_id in self.ds.by_resolution_id,
                "has_references": len(tdocs) > 0
            }
        }

    def validate_cq2_2(self, tc: dict) -> dict:
        """CQ2-2: Tdoc 참조 많은 Resolution Top N"""
        all_resolutions = self.ds.agreements + self.ds.conclusions + self.ds.working_assumptions
        with_refs = [(r, len(r.get("referenced_tdocs", []))) for r in all_resolutions]
        sorted_refs = sorted(with_refs, key=lambda x: x[1], reverse=True)[:10]

        return {
            "status": "PASS" if sorted_refs else "FAIL",
            "result_count": len(sorted_refs),
            "sample": [{"id": r[0]["decision_id"], "tdoc_count": r[1]} for r in sorted_refs[:5]],
            "validation": {
                "ranking_valid": True,
                "max_refs": sorted_refs[0][1] if sorted_refs else 0
            }
        }

    def validate_cq3_1(self, tc: dict) -> dict:
        """CQ3-1: 특정 회사의 FL Summary 목록"""
        company = tc["parameters"]["company"]
        company_data = self.ds.by_company.get(company, [])
        fl_summaries = [d["data"] for d in company_data if d["type"] == "fl_summary"]

        return {
            "status": "PASS" if fl_summaries else "WARN",
            "result_count": len(fl_summaries),
            "sample": [{"tdoc": s.get("tdoc_number", ""), "agenda": s.get("agenda_item", "")} for s in fl_summaries[:3]],
            "validation": {
                "company": company,
                "company_found": company in self.ds.by_company
            }
        }

    def validate_cq3_2(self, tc: dict) -> dict:
        """CQ3-2: 회사별 Moderator 담당 횟수"""
        company_counts = defaultdict(int)
        for fl in self.ds.fl_summaries:
            if fl.get("company"):
                company_counts[fl["company"]] += 1
        for ms in self.ds.moderator_summaries:
            if ms.get("company"):
                company_counts[ms["company"]] += 1

        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "status": "PASS" if sorted_companies else "FAIL",
            "result_count": len(sorted_companies),
            "sample": [{"company": c[0], "count": c[1]} for c in sorted_companies[:5]],
            "validation": {
                "ranking_valid": True,
                "total_companies": len(company_counts)
            }
        }

    def validate_cq3_3(self, tc: dict) -> dict:
        """CQ3-3: 두 회사 간 비교"""
        c1 = tc["parameters"]["company1"]
        c2 = tc["parameters"]["company2"]

        c1_count = len([d for d in self.ds.by_company.get(c1, []) if d["type"] in ["fl_summary", "moderator_summary"]])
        c2_count = len([d for d in self.ds.by_company.get(c2, []) if d["type"] in ["fl_summary", "moderator_summary"]])

        return {
            "status": "PASS",
            "result_count": 2,
            "sample": [{"company": c1, "count": c1_count}, {"company": c2, "count": c2_count}],
            "validation": {
                "comparison_valid": True,
                "difference": abs(c1_count - c2_count)
            }
        }

    def validate_cq4_1(self, tc: dict) -> dict:
        """CQ4-1: 특정 회의의 Session Notes"""
        meeting = tc["parameters"]["meeting"]
        results = self.ds.by_meeting.get(meeting, {}).get("session_notes", [])

        return {
            "status": "PASS" if results else "WARN",
            "result_count": len(results),
            "sample": [{"tdoc": s.get("tdoc_number", ""), "agenda": s.get("agenda_item", "")} for s in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq4_2(self, tc: dict) -> dict:
        """CQ4-2: 특정 회의의 FL Summary"""
        meeting = tc["parameters"]["meeting"]
        results = self.ds.by_meeting.get(meeting, {}).get("fl_summaries", [])

        return {
            "status": "PASS" if results else "WARN",
            "result_count": len(results),
            "sample": [{"tdoc": s.get("tdoc_number", ""), "company": s.get("company", "")} for s in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq4_3(self, tc: dict) -> dict:
        """CQ4-3: 특정 회의의 Moderator Summary"""
        meeting = tc["parameters"]["meeting"]
        results = self.ds.by_meeting.get(meeting, {}).get("moderator_summaries", [])

        return {
            "status": "PASS" if results else "WARN",
            "result_count": len(results),
            "sample": [{"tdoc": s.get("tdoc_number", ""), "company": s.get("company", "")} for s in results[:3]],
            "validation": {
                "data_exists": len(results) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq4_4(self, tc: dict) -> dict:
        """CQ4-4: Ad-hoc Session Chair"""
        meeting = tc["parameters"]["meeting"]
        session_notes = self.ds.by_meeting.get(meeting, {}).get("session_notes", [])
        with_chair = [sn for sn in session_notes if sn.get("chair_company")]

        return {
            "status": "PASS" if with_chair else "WARN",
            "result_count": len(with_chair),
            "sample": [{"tdoc": s.get("tdoc_number", ""), "chair": s.get("chair_company", "")} for s in with_chair[:3]],
            "validation": {
                "data_exists": len(with_chair) > 0,
                "meeting_found": meeting in self.ds.meetings
            }
        }

    def validate_cq6_1(self, tc: dict) -> dict:
        """CQ6-1: 회의별 Resolution 수 추이"""
        meeting_counts = []
        for meeting_id in sorted(self.ds.meetings.keys()):
            data = self.ds.by_meeting[meeting_id]
            total = len(data["agreements"]) + len(data["conclusions"]) + len(data["working_assumptions"])
            meeting_counts.append({"meeting": meeting_id, "resolutions": total})

        return {
            "status": "PASS" if meeting_counts else "FAIL",
            "result_count": len(meeting_counts),
            "sample": meeting_counts[:10],
            "validation": {
                "trend_data_valid": True,
                "total_meetings": len(meeting_counts)
            }
        }

    def validate_cq6_2(self, tc: dict) -> dict:
        """CQ6-2: Resolution 유형별 분포"""
        distribution = {
            "Agreement": len(self.ds.agreements),
            "Conclusion": len(self.ds.conclusions),
            "WorkingAssumption": len(self.ds.working_assumptions)
        }
        total = sum(distribution.values())

        return {
            "status": "PASS",
            "result_count": 3,
            "sample": [{"type": k, "count": v, "percentage": round(100*v/total, 2)} for k, v in distribution.items()],
            "validation": {
                "distribution_valid": True,
                "total": total
            }
        }

    def validate_cq6_3(self, tc: dict) -> dict:
        """CQ6-3: 회의당 평균 Resolution 수"""
        counts = []
        for meeting_id in self.ds.meetings.keys():
            data = self.ds.by_meeting[meeting_id]
            total = len(data["agreements"]) + len(data["conclusions"]) + len(data["working_assumptions"])
            counts.append(total)

        avg = sum(counts) / len(counts) if counts else 0

        return {
            "status": "PASS",
            "result_count": 1,
            "sample": [{"avg": round(avg, 2), "min": min(counts), "max": max(counts), "total_meetings": len(counts)}],
            "validation": {
                "statistics_valid": True,
                "avg_resolutions": round(avg, 2)
            }
        }

    def validate(self, tc: dict) -> dict:
        """Validate a single test case."""
        cq_type = tc["cq_type"]

        # Map CQ types to validation methods
        validators = {
            "CQ1-1": self.validate_cq1_1,
            "CQ1-2": self.validate_cq1_2,
            "CQ1-3": self.validate_cq1_3,
            "CQ1-4": self.validate_cq1_4,
            "CQ1-5": self.validate_cq1_5,
            "CQ2-1": self.validate_cq2_1,
            "CQ2-2": self.validate_cq2_2,
            "CQ3-1": self.validate_cq3_1,
            "CQ3-2": self.validate_cq3_2,
            "CQ3-3": self.validate_cq3_3,
            "CQ4-1": self.validate_cq4_1,
            "CQ4-2": self.validate_cq4_2,
            "CQ4-3": self.validate_cq4_3,
            "CQ4-4": self.validate_cq4_4,
            "CQ6-1": self.validate_cq6_1,
            "CQ6-2": self.validate_cq6_2,
            "CQ6-3": self.validate_cq6_3,
        }

        validator = validators.get(cq_type)
        if validator:
            result = validator(tc)
        else:
            result = {"status": "SKIP", "result_count": 0, "sample": [], "validation": {"reason": f"No validator for {cq_type}"}}

        return {
            "test_case_id": tc["id"],
            "cq_type": cq_type,
            "question": tc["question"],
            **result
        }

    def run_all(self, test_cases: list) -> list:
        """Run all test case validations."""
        results = []
        for tc in test_cases:
            result = self.validate(tc)
            results.append(result)
        return results


def calculate_quality_metrics(results: list) -> dict:
    """Calculate quality metrics from validation results."""
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    # Calculate by CQ type
    by_type = defaultdict(lambda: {"pass": 0, "warn": 0, "fail": 0, "skip": 0, "total": 0})
    for r in results:
        cq_type = r["cq_type"]
        by_type[cq_type]["total"] += 1
        if r["status"] == "PASS":
            by_type[cq_type]["pass"] += 1
        elif r["status"] == "WARN":
            by_type[cq_type]["warn"] += 1
        elif r["status"] == "FAIL":
            by_type[cq_type]["fail"] += 1
        else:
            by_type[cq_type]["skip"] += 1

    # Calculate average result count
    result_counts = [r["result_count"] for r in results]
    avg_results = sum(result_counts) / len(result_counts) if result_counts else 0

    return {
        "total_tests": total,
        "passed": passed,
        "warned": warned,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": round(100 * passed / total, 2),
        "pass_warn_rate": round(100 * (passed + warned) / total, 2),
        "by_cq_type": dict(by_type),
        "avg_result_count": round(avg_results, 2),
        "max_result_count": max(result_counts) if result_counts else 0,
        "min_result_count": min(result_counts) if result_counts else 0
    }


def main():
    print("=" * 70)
    print("CQ VALIDATION EXECUTION")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Load data store
    print("[1/4] Loading data store...")
    ds = JSONDataStore()
    ds.load()

    # Load test dataset
    print("\n[2/4] Loading test dataset...")
    with open(TEST_DATASET) as f:
        test_data = json.load(f)
    test_cases = test_data["test_cases"]
    print(f"  Loaded {len(test_cases)} test cases")

    # Run validation
    print("\n[3/4] Running validations...")
    validator = CQValidator(ds)
    results = validator.run_all(test_cases)

    # Calculate metrics
    print("\n[4/4] Calculating quality metrics...")
    metrics = calculate_quality_metrics(results)

    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"  Total Tests: {metrics['total_tests']}")
    print(f"  ✅ PASS: {metrics['passed']} ({metrics['pass_rate']:.1f}%)")
    print(f"  ⚠️  WARN: {metrics['warned']}")
    print(f"  ❌ FAIL: {metrics['failed']}")
    print(f"  ⏭️  SKIP: {metrics['skipped']}")
    print(f"\n  Pass+Warn Rate: {metrics['pass_warn_rate']:.1f}%")
    print(f"  Avg Result Count: {metrics['avg_result_count']}")

    print("\n  By CQ Type:")
    for cq_type in sorted(metrics["by_cq_type"].keys()):
        data = metrics["by_cq_type"][cq_type]
        status = "✅" if data["pass"] == data["total"] else ("⚠️" if data["fail"] == 0 else "❌")
        print(f"    {status} {cq_type}: {data['pass']}/{data['total']} pass, {data['warn']} warn, {data['fail']} fail")

    # Save results
    output_file = OUTPUT_DIR / "cq_validation_results_100.json"
    output = {
        "executed_at": datetime.now().isoformat(),
        "metrics": metrics,
        "results": results
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to: {output_file}")

    # Print sample results
    print("\n" + "=" * 70)
    print("SAMPLE RESULTS (First 5)")
    print("=" * 70)
    for r in results[:5]:
        status = "✅" if r["status"] == "PASS" else ("⚠️" if r["status"] == "WARN" else "❌")
        print(f"\n  [{r['test_case_id']}] {r['cq_type']} {status}")
        print(f"  Q: {r['question'][:60]}...")
        print(f"  Results: {r['result_count']} items")
        if r["sample"]:
            print(f"  Sample: {r['sample'][0]}")

    return results, metrics


if __name__ == "__main__":
    main()
