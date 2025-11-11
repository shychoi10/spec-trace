#!/usr/bin/env python3
"""
Phase-1 Step-4: Verify Extraction Completeness

Direct comparison between data_raw (ZIPs) and data_extracted (extracted folders)
Considers Step-5 cleanup: Report/Archive folders were intentionally removed

Logic:
1. Scan all ZIPs in data_raw
2. Check corresponding folders in data_extracted
3. Account for Step-5 cleanup (Report/Archive removal)
4. Identify true extraction failures vs intentional cleanup
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_RAW = Path("/home/sihyeon/workspace/spec-trace/data/data_raw/meetings/RAN1")
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/meetings/RAN1")
REPORT_FILE = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/meetings/RAN1/extraction_verification.json")

# Step-5 cleanup: These meetings had Report/Archive removed (46 meetings)
CLEANUP_CATEGORY_A_D = [
    # Category A (43 meetings): Final exists, Archive deleted
    'TSGR1_100_e', 'TSGR1_100b_e', 'TSGR1_101-e', 'TSGR1_102-e', 'TSGR1_103-e',
    'TSGR1_104-e', 'TSGR1_104b-e', 'TSGR1_105-e', 'TSGR1_106-e', 'TSGR1_106b-e',
    'TSGR1_107-e', 'TSGR1_107b-e', 'TSGR1_108-e', 'TSGR1_109-e', 'TSGR1_110',
    'TSGR1_110b-e', 'TSGR1_111', 'TSGR1_112', 'TSGR1_112b-e', 'TSGR1_113',
    'TSGR1_114', 'TSGR1_114b', 'TSGR1_115', 'TSGR1_116', 'TSGR1_117',
    'TSGR1_118', 'TSGR1_119', 'TSGR1_120', 'TSGR1_121', 'TSGR1_122',
    'TSGR1_84', 'TSGR1_84b', 'TSGR1_85', 'TSGR1_86b', 'TSGR1_87',
    'TSGR1_88', 'TSGR1_89', 'TSGR1_90b', 'TSGR1_91', 'TSGR1_92',
    'TSGR1_92b', 'TSGR1_93', 'TSGR1_94b',
    # Category D (3 meetings): Final missing, Draft v030 as current, Archive deleted
    'TSGR1_96', 'TSGR1_98', 'TSGR1_99'
]

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_zips': 0,
    'extracted_folders': 0,
    'missing_folders': 0,
    'empty_folders': 0,
    'intentional_cleanup': 0,
    'true_failures': 0,
    'missing_details': [],
    'empty_details': []
}


def is_intentional_cleanup(zip_path: Path) -> bool:
    """
    Check if missing folder is due to Step-5 cleanup (Report/Archive removal)

    Returns:
        True if this is intentional cleanup, False if it's a true extraction failure
    """
    parts = zip_path.parts

    # Find meeting name and check if it's in Report/Archive
    meeting_idx = -1
    for i, part in enumerate(parts):
        if part.startswith('TSGR1_'):
            meeting_idx = i
            break

    if meeting_idx == -1:
        return False

    meeting_name = parts[meeting_idx]

    # Check if this meeting had Archive cleanup
    if meeting_name not in CLEANUP_CATEGORY_A_D:
        return False

    # Check if path contains Report (not Docs)
    if 'Report' not in parts:
        return False

    # Check if the ZIP name suggests it's from Archive
    # Archive folder names: Draft_Minutes_v010, v020, v030, etc.
    zip_name = zip_path.stem

    # Common Archive patterns:
    # - Draft_Minutes_*
    # - *_v010, *_v020, etc.
    if 'Draft' in zip_name or any(f'_v0{i}0' in zip_name for i in range(1, 10)):
        return True

    return False


def check_extraction(zip_path: Path) -> dict:
    """
    Check if a ZIP was properly extracted

    Returns:
        dict: {'status': 'success'|'missing'|'empty', 'reason': str}
    """
    # Calculate expected extracted folder path
    rel_path = zip_path.relative_to(DATA_RAW)

    # ZIP: TSGR1_XXX/Docs/R1-YYYYYYY.zip
    # Folder: TSGR1_XXX/Docs/R1-YYYYYYY/
    expected_folder = DATA_EXTRACTED / rel_path.parent / zip_path.stem

    if not expected_folder.exists():
        # Check if this is intentional cleanup
        if is_intentional_cleanup(zip_path):
            return {
                'status': 'intentional_cleanup',
                'reason': 'Step-5 cleanup: Report/Archive removed'
            }
        else:
            return {
                'status': 'missing',
                'reason': 'Folder not found'
            }

    # Check if folder is empty
    if not any(expected_folder.iterdir()):
        return {
            'status': 'empty',
            'reason': 'Folder exists but empty'
        }

    return {
        'status': 'success',
        'reason': 'Extracted successfully'
    }


def main():
    print("=" * 80)
    print("Phase-1 Step-4: Extraction Verification")
    print("=" * 80)
    print(f"Raw (ZIPs):      {DATA_RAW}")
    print(f"Extracted:       {DATA_EXTRACTED}")
    print(f"Started:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    print("Step-5 Cleanup Consideration:")
    print(f"  - {len(CLEANUP_CATEGORY_A_D)} meetings had Report/Archive removed")
    print(f"  - These missing folders are INTENTIONAL, not extraction failures")
    print("=" * 80)

    # Scan all ZIPs
    print("\nScanning ZIPs in data_raw...")
    zip_files = sorted(DATA_RAW.rglob("*.zip"))
    stats['total_zips'] = len(zip_files)

    print(f"Found {len(zip_files):,} ZIP files\n")

    # Check each ZIP
    print("Verifying extraction...")

    for i, zip_path in enumerate(zip_files):
        result = check_extraction(zip_path)

        if result['status'] == 'success':
            stats['extracted_folders'] += 1
        elif result['status'] == 'intentional_cleanup':
            stats['intentional_cleanup'] += 1
        elif result['status'] == 'missing':
            stats['missing_folders'] += 1
            stats['true_failures'] += 1
            stats['missing_details'].append({
                'zip': str(zip_path.relative_to(DATA_RAW)),
                'reason': result['reason']
            })
        elif result['status'] == 'empty':
            stats['empty_folders'] += 1
            stats['true_failures'] += 1
            stats['empty_details'].append({
                'zip': str(zip_path.relative_to(DATA_RAW)),
                'reason': result['reason']
            })

        # Progress
        if (i + 1) % 10000 == 0:
            print(f"  Progress: {i+1:,}/{len(zip_files):,} ({(i+1)/len(zip_files)*100:.1f}%)")

    # Calculate rates
    true_success = stats['extracted_folders']
    true_failure = stats['true_failures']
    success_rate = (true_success / stats['total_zips'] * 100) if stats['total_zips'] > 0 else 0

    # Save report
    stats['end_time'] = datetime.now().isoformat()
    stats['success_rate'] = f"{success_rate:.2f}%"

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total ZIPs:           {stats['total_zips']:,}")
    print()
    print("Extraction Results:")
    print(f"  ✅ Success:          {stats['extracted_folders']:,}")
    print(f"  🗑️  Intentional cleanup: {stats['intentional_cleanup']:,} (Step-5 Report/Archive)")
    print(f"  ❌ Missing:          {stats['missing_folders']:,}")
    print(f"  ⚠️  Empty:            {stats['empty_folders']:,}")
    print()
    print("True Failures:")
    print(f"  Total failures:     {true_failure:,}")
    print(f"  Success rate:       {success_rate:.2f}%")
    print()

    if stats['missing_details']:
        print(f"Missing folders (first 10 of {len(stats['missing_details'])}):")
        for detail in stats['missing_details'][:10]:
            print(f"  - {detail['zip']}")
        if len(stats['missing_details']) > 10:
            print(f"  ... +{len(stats['missing_details'])-10} more")
        print()

    if stats['empty_details']:
        print(f"Empty folders (first 10 of {len(stats['empty_details'])}):")
        for detail in stats['empty_details'][:10]:
            print(f"  - {detail['zip']}")
        if len(stats['empty_details']) > 10:
            print(f"  ... +{len(stats['empty_details'])-10} more")
        print()

    print(f"Report saved: {REPORT_FILE}")
    print("=" * 80)

    return 0 if true_failure == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
