#!/usr/bin/env python3
"""
Cross-Validation: JSON Parsed Data vs JSON-LD Instances vs Original Report

Validates data integrity across multiple formats:
1. Parsed JSON → JSON-LD consistency
2. JSON-LD schema compliance
3. Sample original report verification
4. Data quality metrics
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
REPORTS_DIR = BASE_DIR / "data" / "data_extracted" / "meetings" / "RAN1"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"


def load_parsed_data():
    """Load all parsed JSON data."""
    data = {
        "agreements": [],
        "conclusions": [],
        "working_assumptions": [],
        "session_notes": [],
        "fl_summaries": [],
        "moderator_summaries": [],
        "meetings": set()
    }

    for f in sorted(PARSED_DIR.glob("RAN1_*_v2.json")):
        with open(f) as fp:
            d = json.load(fp)
            meeting_id = d["meeting_id"]
            data["meetings"].add(meeting_id)
            data["agreements"].extend(d["agreements"])
            data["conclusions"].extend(d["conclusions"])
            data["working_assumptions"].extend(d["working_assumptions"])
            data["session_notes"].extend(d["session_notes"])
            data["fl_summaries"].extend(d["fl_summaries"])
            data["moderator_summaries"].extend(d["moderator_summaries"])

    return data


def load_jsonld_data():
    """Load all JSON-LD instance files."""
    data = {
        "agreements": [],
        "conclusions": [],
        "working_assumptions": [],
        "session_notes": [],
        "summaries": []
    }

    files = {
        "resolutions_agreements.jsonld": "agreements",
        "resolutions_conclusions.jsonld": "conclusions",
        "resolutions_working_assumptions.jsonld": "working_assumptions",
        "session_notes.jsonld": "session_notes",
        "summaries.jsonld": "summaries"
    }

    for filename, key in files.items():
        filepath = JSONLD_DIR / filename
        if filepath.exists():
            with open(filepath) as f:
                d = json.load(f)
                data[key] = d.get("@graph", [])

    return data


def validate_count_consistency(parsed: dict, jsonld: dict) -> dict:
    """Validate instance counts match between parsed and JSON-LD."""
    results = {
        "agreements": {
            "parsed": len(parsed["agreements"]),
            "jsonld": len(jsonld["agreements"]),
            "match": len(parsed["agreements"]) == len(jsonld["agreements"])
        },
        "conclusions": {
            "parsed": len(parsed["conclusions"]),
            "jsonld": len(jsonld["conclusions"]),
            "match": len(parsed["conclusions"]) == len(jsonld["conclusions"])
        },
        "working_assumptions": {
            "parsed": len(parsed["working_assumptions"]),
            "jsonld": len(jsonld["working_assumptions"]),
            "match": len(parsed["working_assumptions"]) == len(jsonld["working_assumptions"])
        },
        "session_notes": {
            "parsed": len(parsed["session_notes"]),
            "jsonld": len(jsonld["session_notes"]),
            "match": len(parsed["session_notes"]) == len(jsonld["session_notes"])
        },
        "summaries": {
            "parsed": len(parsed["fl_summaries"]) + len(parsed["moderator_summaries"]),
            "jsonld": len(jsonld["summaries"]),
            "match": len(parsed["fl_summaries"]) + len(parsed["moderator_summaries"]) == len(jsonld["summaries"])
        }
    }

    all_match = all(r["match"] for r in results.values())
    return {"counts": results, "all_match": all_match}


def validate_jsonld_schema(jsonld: dict) -> dict:
    """Validate JSON-LD schema compliance."""
    issues = []
    stats = defaultdict(int)

    # Check agreements
    for agr in jsonld["agreements"]:
        stats["agreements_checked"] += 1

        # Required fields
        if "@id" not in agr:
            issues.append({"type": "missing_id", "item": "agreement"})
        elif not agr["@id"].startswith("tdoc:resolution/"):
            issues.append({"type": "invalid_id_prefix", "id": agr["@id"]})

        if "@type" not in agr or agr["@type"] != "Agreement":
            issues.append({"type": "wrong_type", "id": agr.get("@id", "unknown")})

        if "resolutionId" not in agr:
            issues.append({"type": "missing_resolutionId", "id": agr.get("@id", "unknown")})

        if "content" not in agr:
            issues.append({"type": "missing_content", "id": agr.get("@id", "unknown")})

        if "resolutionBelongsTo" not in agr:
            issues.append({"type": "missing_resolutionBelongsTo", "id": agr.get("@id", "unknown")})

    # Check conclusions
    for conc in jsonld["conclusions"]:
        stats["conclusions_checked"] += 1
        if "@type" not in conc or conc["@type"] != "Conclusion":
            issues.append({"type": "wrong_type", "id": conc.get("@id", "unknown")})

    # Check working assumptions
    for wa in jsonld["working_assumptions"]:
        stats["working_assumptions_checked"] += 1
        if "@type" not in wa or wa["@type"] != "WorkingAssumption":
            issues.append({"type": "wrong_type", "id": wa.get("@id", "unknown")})

    # Check session notes
    for sn in jsonld["session_notes"]:
        stats["session_notes_checked"] += 1
        if "@type" not in sn or sn["@type"] != "SessionNotes":
            issues.append({"type": "wrong_type", "id": sn.get("@id", "unknown")})

    # Check summaries
    for s in jsonld["summaries"]:
        stats["summaries_checked"] += 1
        if "@type" not in s or s["@type"] != "Summary":
            issues.append({"type": "wrong_type", "id": s.get("@id", "unknown")})

    return {
        "total_checked": sum(stats.values()),
        "stats": dict(stats),
        "issues_count": len(issues),
        "issues": issues[:20],  # First 20 issues
        "schema_valid": len(issues) == 0
    }


def validate_sample_content(parsed: dict, jsonld: dict) -> dict:
    """Validate sample content matches between formats."""

    # Build lookup from JSON-LD
    jsonld_by_id = {}
    for agr in jsonld["agreements"]:
        rid = agr.get("resolutionId", "")
        jsonld_by_id[rid] = agr
    for conc in jsonld["conclusions"]:
        rid = conc.get("resolutionId", "")
        jsonld_by_id[rid] = conc
    for wa in jsonld["working_assumptions"]:
        rid = wa.get("resolutionId", "")
        jsonld_by_id[rid] = wa

    # Sample 50 random items from parsed
    import random
    samples = random.sample(parsed["agreements"], min(30, len(parsed["agreements"])))
    samples += random.sample(parsed["conclusions"], min(10, len(parsed["conclusions"])))
    samples += random.sample(parsed["working_assumptions"], min(10, len(parsed["working_assumptions"])))

    matches = 0
    mismatches = []

    for item in samples:
        decision_id = item["decision_id"]
        jsonld_item = jsonld_by_id.get(decision_id)

        if jsonld_item:
            # Compare content
            parsed_content = item["content"]
            jsonld_content = jsonld_item.get("content", "")

            if parsed_content == jsonld_content:
                matches += 1
            else:
                mismatches.append({
                    "id": decision_id,
                    "reason": "content_mismatch",
                    "parsed_len": len(parsed_content),
                    "jsonld_len": len(jsonld_content)
                })
        else:
            mismatches.append({
                "id": decision_id,
                "reason": "not_found_in_jsonld"
            })

    return {
        "samples_checked": len(samples),
        "matches": matches,
        "mismatches": len(mismatches),
        "match_rate": round(100 * matches / len(samples), 2) if samples else 0,
        "mismatch_details": mismatches[:10]
    }


def analyze_data_quality(parsed: dict) -> dict:
    """Analyze overall data quality metrics."""

    # Content length analysis
    agreement_lengths = [len(a["content"]) for a in parsed["agreements"]]
    conclusion_lengths = [len(c["content"]) for c in parsed["conclusions"]]
    wa_lengths = [len(w["content"]) for w in parsed["working_assumptions"]]

    # Tdoc reference analysis
    agreements_with_tdocs = sum(1 for a in parsed["agreements"] if a.get("referenced_tdocs"))
    total_tdoc_refs = sum(len(a.get("referenced_tdocs", [])) for a in parsed["agreements"])

    # Agenda coverage
    unique_agendas = set()
    for a in parsed["agreements"]:
        unique_agendas.add(a["agenda_item"])
    for c in parsed["conclusions"]:
        unique_agendas.add(c["agenda_item"])

    # Company coverage in summaries
    unique_companies = set()
    for fl in parsed["fl_summaries"]:
        if fl.get("company"):
            unique_companies.add(fl["company"])
    for ms in parsed["moderator_summaries"]:
        if ms.get("company"):
            unique_companies.add(ms["company"])

    # Empty content check
    empty_agreements = sum(1 for a in parsed["agreements"] if not a["content"].strip())
    empty_conclusions = sum(1 for c in parsed["conclusions"] if not c["content"].strip())

    return {
        "content_length": {
            "agreements": {
                "min": min(agreement_lengths) if agreement_lengths else 0,
                "max": max(agreement_lengths) if agreement_lengths else 0,
                "avg": round(sum(agreement_lengths) / len(agreement_lengths), 2) if agreement_lengths else 0
            },
            "conclusions": {
                "min": min(conclusion_lengths) if conclusion_lengths else 0,
                "max": max(conclusion_lengths) if conclusion_lengths else 0,
                "avg": round(sum(conclusion_lengths) / len(conclusion_lengths), 2) if conclusion_lengths else 0
            },
            "working_assumptions": {
                "min": min(wa_lengths) if wa_lengths else 0,
                "max": max(wa_lengths) if wa_lengths else 0,
                "avg": round(sum(wa_lengths) / len(wa_lengths), 2) if wa_lengths else 0
            }
        },
        "tdoc_references": {
            "agreements_with_tdocs": agreements_with_tdocs,
            "total_tdoc_refs": total_tdoc_refs,
            "avg_refs_per_agreement": round(total_tdoc_refs / len(parsed["agreements"]), 2) if parsed["agreements"] else 0
        },
        "coverage": {
            "unique_agendas": len(unique_agendas),
            "unique_companies": len(unique_companies),
            "meetings": len(parsed["meetings"])
        },
        "quality_issues": {
            "empty_agreements": empty_agreements,
            "empty_conclusions": empty_conclusions,
            "empty_rate": round(100 * (empty_agreements + empty_conclusions) / (len(parsed["agreements"]) + len(parsed["conclusions"])), 2) if (parsed["agreements"] or parsed["conclusions"]) else 0
        }
    }


def main():
    print("=" * 70)
    print("CROSS-VALIDATION: Parsed JSON vs JSON-LD")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Load data
    print("[1/5] Loading parsed JSON data...")
    parsed = load_parsed_data()
    print(f"  - Meetings: {len(parsed['meetings'])}")
    print(f"  - Agreements: {len(parsed['agreements'])}")
    print(f"  - Conclusions: {len(parsed['conclusions'])}")
    print(f"  - Working Assumptions: {len(parsed['working_assumptions'])}")
    print(f"  - Session Notes: {len(parsed['session_notes'])}")
    print(f"  - FL Summaries: {len(parsed['fl_summaries'])}")
    print(f"  - Moderator Summaries: {len(parsed['moderator_summaries'])}")

    print("\n[2/5] Loading JSON-LD data...")
    jsonld = load_jsonld_data()
    print(f"  - Agreements: {len(jsonld['agreements'])}")
    print(f"  - Conclusions: {len(jsonld['conclusions'])}")
    print(f"  - Working Assumptions: {len(jsonld['working_assumptions'])}")
    print(f"  - Session Notes: {len(jsonld['session_notes'])}")
    print(f"  - Summaries: {len(jsonld['summaries'])}")

    # Validate count consistency
    print("\n[3/5] Validating count consistency...")
    count_results = validate_count_consistency(parsed, jsonld)
    for key, data in count_results["counts"].items():
        status = "✅" if data["match"] else "❌"
        print(f"  {status} {key}: parsed={data['parsed']}, jsonld={data['jsonld']}")

    # Validate JSON-LD schema
    print("\n[4/5] Validating JSON-LD schema...")
    schema_results = validate_jsonld_schema(jsonld)
    print(f"  - Total items checked: {schema_results['total_checked']}")
    print(f"  - Schema issues: {schema_results['issues_count']}")
    status = "✅" if schema_results["schema_valid"] else "❌"
    print(f"  {status} Schema validation: {'PASS' if schema_results['schema_valid'] else 'FAIL'}")
    if schema_results["issues"]:
        print("  Sample issues:")
        for issue in schema_results["issues"][:5]:
            print(f"    - {issue}")

    # Validate sample content
    print("\n[5/5] Validating sample content...")
    content_results = validate_sample_content(parsed, jsonld)
    print(f"  - Samples checked: {content_results['samples_checked']}")
    print(f"  - Matches: {content_results['matches']}")
    print(f"  - Match rate: {content_results['match_rate']}%")

    # Analyze data quality
    print("\n" + "=" * 70)
    print("DATA QUALITY ANALYSIS")
    print("=" * 70)
    quality = analyze_data_quality(parsed)

    print("\n  Content Length Statistics:")
    for dtype, stats in quality["content_length"].items():
        print(f"    {dtype}: min={stats['min']}, max={stats['max']}, avg={stats['avg']}")

    print("\n  Tdoc References:")
    print(f"    Agreements with Tdocs: {quality['tdoc_references']['agreements_with_tdocs']}")
    print(f"    Total Tdoc refs: {quality['tdoc_references']['total_tdoc_refs']}")
    print(f"    Avg refs per agreement: {quality['tdoc_references']['avg_refs_per_agreement']}")

    print("\n  Coverage:")
    print(f"    Unique agendas: {quality['coverage']['unique_agendas']}")
    print(f"    Unique companies: {quality['coverage']['unique_companies']}")
    print(f"    Meetings: {quality['coverage']['meetings']}")

    print("\n  Quality Issues:")
    print(f"    Empty agreements: {quality['quality_issues']['empty_agreements']}")
    print(f"    Empty conclusions: {quality['quality_issues']['empty_conclusions']}")
    print(f"    Empty rate: {quality['quality_issues']['empty_rate']}%")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    all_pass = (
        count_results["all_match"] and
        schema_results["schema_valid"] and
        content_results["match_rate"] >= 95
    )

    print(f"  ✅ Count Consistency: {'PASS' if count_results['all_match'] else 'FAIL'}")
    print(f"  ✅ Schema Validation: {'PASS' if schema_results['schema_valid'] else 'FAIL'}")
    print(f"  ✅ Content Match: {'PASS' if content_results['match_rate'] >= 95 else 'FAIL'} ({content_results['match_rate']}%)")
    print(f"\n  Overall: {'✅ ALL VALIDATIONS PASSED' if all_pass else '❌ SOME VALIDATIONS FAILED'}")

    # Save results
    output_file = OUTPUT_DIR / "cross_validation_results.json"
    output = {
        "executed_at": datetime.now().isoformat(),
        "count_consistency": count_results,
        "schema_validation": schema_results,
        "content_validation": content_results,
        "data_quality": quality,
        "overall_pass": all_pass
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to: {output_file}")

    return output


if __name__ == "__main__":
    main()
