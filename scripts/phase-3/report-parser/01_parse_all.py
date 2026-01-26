#!/usr/bin/env python3
"""
Parse all 58 Final Reports with TOC-based agenda mapping.

Outputs:
- ontology/output/parsed_reports/*.json (58 files)
- ontology/output/parsed_reports/_summary_report.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from report_parser import parse_report, save_report


# Paths
INPUT_DIR = Path(__file__).parent.parent.parent.parent / "ontology" / "input" / "meetings" / "RAN1" / "Final_Report"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "ontology" / "output" / "parsed_reports"


def get_all_reports() -> list[Path]:
    """Get all Final Report files (DOCX and DOCM)."""
    docx_files = list(INPUT_DIR.glob("Final_Report_RAN1-*.docx"))
    docm_files = list(INPUT_DIR.glob("Final_Report_RAN1-*.docm"))
    return sorted(docx_files + docm_files, key=lambda p: p.stem)


def parse_single_report(docx_path: Path) -> dict:
    """Parse a single report and return summary stats."""
    try:
        report = parse_report(docx_path)

        # Save to output
        output_path = OUTPUT_DIR / f"{report.meeting_id.replace('#', '_')}_v2.json"
        save_report(report, output_path)

        return {
            "meeting_id": report.meeting_id,
            "status": "success",
            "toc_entries": len(report.toc_entries),
            "sections": len(report.sections),
            "agreements": len(report.agreements),
            "conclusions": len(report.conclusions),
            "working_assumptions": len(report.working_assumptions),
            "total_decisions": report.total_decisions,
            "session_notes": len(report.session_notes),
            "fl_summaries": len(report.fl_summaries),
            "moderator_summaries": len(report.moderator_summaries),
            "total_roles": report.total_roles,
            "agenda_format_valid": _check_agenda_format(report),
        }
    except Exception as e:
        return {
            "meeting_id": docx_path.stem,
            "status": "error",
            "error": str(e),
        }


def _check_agenda_format(report) -> bool:
    """Check if all agenda items are in valid format (no H1-xxx)."""
    import re
    valid_pattern = re.compile(r'^\d+(?:\.\d+)*$|^UNKNOWN$')

    for d in report.agreements + report.conclusions + report.working_assumptions:
        if not valid_pattern.match(d.agenda_item):
            return False
    return True


def main():
    """Main function to parse all reports."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get all reports
    reports = get_all_reports()
    print(f"Found {len(reports)} Final Reports")

    # Parse all reports
    results = []
    errors = []

    # Use ProcessPoolExecutor for parallelization
    max_workers = 4  # Moderate parallelization

    print(f"Parsing with {max_workers} workers...")
    start_time = datetime.now()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(parse_single_report, path): path for path in reports}

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)

            if result["status"] == "success":
                print(f"[{i}/{len(reports)}] {result['meeting_id']}: "
                      f"{result['total_decisions']} decisions, {result['total_roles']} roles")
            else:
                errors.append(result)
                print(f"[{i}/{len(reports)}] {result['meeting_id']}: ERROR - {result.get('error', 'Unknown')}")

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nCompleted in {elapsed:.1f}s")

    # Calculate totals
    success_results = [r for r in results if r["status"] == "success"]

    totals = {
        "total_meetings": len(success_results),
        "total_toc_entries": sum(r["toc_entries"] for r in success_results),
        "total_sections": sum(r["sections"] for r in success_results),
        "total_agreements": sum(r["agreements"] for r in success_results),
        "total_conclusions": sum(r["conclusions"] for r in success_results),
        "total_working_assumptions": sum(r["working_assumptions"] for r in success_results),
        "total_decisions": sum(r["total_decisions"] for r in success_results),
        "total_session_notes": sum(r["session_notes"] for r in success_results),
        "total_fl_summaries": sum(r["fl_summaries"] for r in success_results),
        "total_moderator_summaries": sum(r["moderator_summaries"] for r in success_results),
        "total_roles": sum(r["total_roles"] for r in success_results),
        "agenda_format_valid_count": sum(1 for r in success_results if r.get("agenda_format_valid", False)),
        "errors": len(errors),
    }

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Meetings parsed: {totals['total_meetings']}")
    print(f"  TOC entries: {totals['total_toc_entries']}")
    print(f"  Sections: {totals['total_sections']}")
    print(f"Decisions:")
    print(f"  Agreements: {totals['total_agreements']}")
    print(f"  Conclusions: {totals['total_conclusions']}")
    print(f"  Working Assumptions: {totals['total_working_assumptions']}")
    print(f"  Total: {totals['total_decisions']}")
    print(f"Roles:")
    print(f"  Session Notes: {totals['total_session_notes']}")
    print(f"  FL Summaries: {totals['total_fl_summaries']}")
    print(f"  Moderator Summaries: {totals['total_moderator_summaries']}")
    print(f"  Total: {totals['total_roles']}")
    print(f"Agenda format valid: {totals['agenda_format_valid_count']}/{totals['total_meetings']}")
    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors:
            print(f"  - {err['meeting_id']}: {err.get('error', 'Unknown')}")

    # Save summary report
    summary = {
        "parsed_at": datetime.now().isoformat(),
        "totals": totals,
        "results": results,
    }

    summary_path = OUTPUT_DIR / "_summary_report.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nSummary saved to {summary_path}")


if __name__ == "__main__":
    main()
