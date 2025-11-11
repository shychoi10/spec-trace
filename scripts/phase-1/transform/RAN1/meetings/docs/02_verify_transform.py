#!/usr/bin/env python3
"""
Phase-1 Step-6-1: Verify Transform Completeness

Direct comparison between data_extracted and data_transformed:
- Count DOC/DOCX files in extracted
- Count DOCX files in transformed
- Verify: transformed_docx >= extracted_doc + extracted_docx
- Report missing files and folders
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/meetings/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/meetings/RAN1")
REPORT_FILE = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/meetings/docs/verification_report.json")

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'meetings_total': 0,
    'meetings_verified': 0,
    'extracted': {
        'docs_folders': 0,
        'report_folders': 0,
        'doc_files': 0,
        'docx_files': 0,
        'total_files': 0
    },
    'transformed': {
        'docs_folders': 0,
        'report_folders': 0,
        'docx_files': 0,
        'total_files': 0
    },
    'missing_folders': [],
    'file_count_mismatches': [],
    'meetings_with_issues': []
}


def count_files_in_folder(folder_path: Path):
    """
    Count DOC and DOCX files in a folder

    Returns:
        dict: {'doc': count, 'docx': count}
    """
    if not folder_path.exists():
        return {'doc': 0, 'docx': 0}

    doc_files = list(folder_path.rglob("*.doc"))
    # Filter out .docx from .doc count
    doc_files = [f for f in doc_files if f.suffix.lower() == '.doc']

    docx_files = list(folder_path.rglob("*.docx"))

    return {
        'doc': len(doc_files),
        'docx': len(docx_files)
    }


def verify_meeting(meeting_name: str):
    """
    Verify a single meeting's transformation

    Returns:
        dict: Verification results
    """
    extracted_path = DATA_EXTRACTED / meeting_name
    transformed_path = DATA_TRANSFORMED / meeting_name

    result = {
        'meeting': meeting_name,
        'extracted': {},
        'transformed': {},
        'issues': []
    }

    # Check Docs folder
    extracted_docs = extracted_path / "Docs"
    transformed_docs = transformed_path / "Docs"

    if extracted_docs.exists():
        stats['extracted']['docs_folders'] += 1
        extracted_counts = count_files_in_folder(extracted_docs)
        result['extracted']['docs'] = extracted_counts
        stats['extracted']['doc_files'] += extracted_counts['doc']
        stats['extracted']['docx_files'] += extracted_counts['docx']
        stats['extracted']['total_files'] += extracted_counts['doc'] + extracted_counts['docx']

        if transformed_docs.exists():
            stats['transformed']['docs_folders'] += 1
            transformed_counts = count_files_in_folder(transformed_docs)
            result['transformed']['docs'] = transformed_counts
            stats['transformed']['docx_files'] += transformed_counts['docx']
            stats['transformed']['total_files'] += transformed_counts['docx']

            # Verify: transformed should have doc + docx from extracted
            expected = extracted_counts['doc'] + extracted_counts['docx']
            actual = transformed_counts['docx']

            if actual < expected:
                issue = f"Docs: Expected {expected} DOCX, got {actual} (missing {expected-actual})"
                result['issues'].append(issue)
                stats['file_count_mismatches'].append({
                    'meeting': meeting_name,
                    'folder': 'Docs',
                    'expected': expected,
                    'actual': actual,
                    'missing': expected - actual
                })
        else:
            issue = "Docs: Transformed folder missing"
            result['issues'].append(issue)
            stats['missing_folders'].append(f"{meeting_name}/Docs")

    # Check Report folder
    extracted_report = extracted_path / "Report"
    transformed_report = transformed_path / "Report"

    if extracted_report.exists():
        stats['extracted']['report_folders'] += 1
        extracted_counts = count_files_in_folder(extracted_report)
        result['extracted']['report'] = extracted_counts
        stats['extracted']['doc_files'] += extracted_counts['doc']
        stats['extracted']['docx_files'] += extracted_counts['docx']
        stats['extracted']['total_files'] += extracted_counts['doc'] + extracted_counts['docx']

        if transformed_report.exists():
            stats['transformed']['report_folders'] += 1
            transformed_counts = count_files_in_folder(transformed_report)
            result['transformed']['report'] = transformed_counts
            stats['transformed']['docx_files'] += transformed_counts['docx']
            stats['transformed']['total_files'] += transformed_counts['docx']

            # Verify: transformed should have doc + docx from extracted
            expected = extracted_counts['doc'] + extracted_counts['docx']
            actual = transformed_counts['docx']

            if actual < expected:
                issue = f"Report: Expected {expected} DOCX, got {actual} (missing {expected-actual})"
                result['issues'].append(issue)
                stats['file_count_mismatches'].append({
                    'meeting': meeting_name,
                    'folder': 'Report',
                    'expected': expected,
                    'actual': actual,
                    'missing': expected - actual
                })
        else:
            issue = "Report: Transformed folder missing"
            result['issues'].append(issue)
            stats['missing_folders'].append(f"{meeting_name}/Report")

    return result


def main():
    print("=" * 80)
    print("Phase-1 Step-6-1: Transform Verification")
    print("=" * 80)
    print(f"Extracted:    {DATA_EXTRACTED}")
    print(f"Transformed:  {DATA_TRANSFORMED}")
    print(f"Started:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Get all meetings from extracted
    meeting_folders = sorted([
        d for d in DATA_EXTRACTED.iterdir()
        if d.is_dir() and d.name.startswith('TSGR1_')
    ])

    stats['meetings_total'] = len(meeting_folders)

    print(f"\nFound {len(meeting_folders)} meetings\n")

    # Verify each meeting
    all_results = []

    for meeting_path in meeting_folders:
        meeting_name = meeting_path.name
        result = verify_meeting(meeting_name)
        all_results.append(result)

        if result['issues']:
            stats['meetings_with_issues'].append(meeting_name)
            print(f"⚠️  {meeting_name}: {len(result['issues'])} issues")
            for issue in result['issues']:
                print(f"    - {issue}")
        else:
            stats['meetings_verified'] += 1

    # Calculate summary
    extracted_total = stats['extracted']['doc_files'] + stats['extracted']['docx_files']
    transformed_total = stats['transformed']['docx_files']
    missing_total = extracted_total - transformed_total

    # Save report
    stats['end_time'] = datetime.now().isoformat()
    stats['all_results'] = all_results

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Meetings total:     {stats['meetings_total']}")
    print(f"Meetings verified:  {stats['meetings_verified']} (✅ no issues)")
    print(f"Meetings w/ issues: {len(stats['meetings_with_issues'])} (⚠️)")
    print()
    print("EXTRACTED (data_extracted):")
    print(f"  Docs folders:   {stats['extracted']['docs_folders']}")
    print(f"  Report folders: {stats['extracted']['report_folders']}")
    print(f"  DOC files:      {stats['extracted']['doc_files']:,}")
    print(f"  DOCX files:     {stats['extracted']['docx_files']:,}")
    print(f"  TOTAL files:    {extracted_total:,}")
    print()
    print("TRANSFORMED (data_transformed):")
    print(f"  Docs folders:   {stats['transformed']['docs_folders']}")
    print(f"  Report folders: {stats['transformed']['report_folders']}")
    print(f"  DOCX files:     {transformed_total:,}")
    print()
    print("COMPARISON:")
    print(f"  Expected:       {extracted_total:,} (all DOC+DOCX from extracted)")
    print(f"  Actual:         {transformed_total:,}")
    print(f"  Missing:        {missing_total:,}")
    print(f"  Success rate:   {(transformed_total/extracted_total*100) if extracted_total > 0 else 0:.2f}%")
    print()

    if stats['missing_folders']:
        print(f"Missing folders: {len(stats['missing_folders'])}")
        for folder in stats['missing_folders'][:10]:
            print(f"  - {folder}")
        if len(stats['missing_folders']) > 10:
            print(f"  ... +{len(stats['missing_folders'])-10} more")
        print()

    if stats['file_count_mismatches']:
        print(f"File count mismatches: {len(stats['file_count_mismatches'])}")
        for mismatch in stats['file_count_mismatches'][:10]:
            print(f"  - {mismatch['meeting']}/{mismatch['folder']}: "
                  f"Expected {mismatch['expected']}, got {mismatch['actual']} "
                  f"(missing {mismatch['missing']})")
        if len(stats['file_count_mismatches']) > 10:
            print(f"  ... +{len(stats['file_count_mismatches'])-10} more")
        print()

    print(f"Report saved: {REPORT_FILE}")
    print("=" * 80)

    return 0 if len(stats['meetings_with_issues']) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
