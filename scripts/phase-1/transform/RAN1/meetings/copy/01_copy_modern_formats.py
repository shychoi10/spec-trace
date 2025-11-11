#!/usr/bin/env python3
"""
Phase-1 Step-6-1: Copy Modern Format Files (PPTX, XLSX)
Copy already-modern format files to data_transformed without conversion
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/meetings/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/meetings/RAN1")
LOG_DIR = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/meetings/copy")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_files': 0,
    'pptx_copied': 0,
    'xlsx_copied': 0,
    'copy_errors': [],
    'skipped_already_exists': 0
}


def copy_file_if_not_exists(src_path: Path, dst_path: Path, file_type: str) -> bool:
    """
    Copy file to destination if it doesn't already exist

    Args:
        src_path: Source file path
        dst_path: Destination file path (full path including filename)
        file_type: 'pptx' or 'xlsx'

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if already exists
        if dst_path.exists() and dst_path.stat().st_size > 0:
            stats['skipped_already_exists'] += 1
            return True

        # Create parent directory
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(src_path, dst_path)

        # Track by type
        if file_type == 'pptx':
            stats['pptx_copied'] += 1
        elif file_type == 'xlsx':
            stats['xlsx_copied'] += 1

        return True

    except Exception as e:
        stats['copy_errors'].append({
            'file': str(src_path),
            'error': str(e)
        })
        return False


def process_meeting_modern_files(meeting_path: Path):
    """
    Process all PPTX and XLSX files in a meeting's Docs folder

    Args:
        meeting_path: Path to meeting folder (e.g., TSGR1_84)
    """
    docs_path = meeting_path / "Docs"

    if not docs_path.exists():
        return

    meeting_name = meeting_path.name

    # Find all PPTX and XLSX files recursively
    pptx_files = list(docs_path.rglob("*.pptx"))
    xlsx_files = list(docs_path.rglob("*.xlsx"))

    total_files = len(pptx_files) + len(xlsx_files)

    if total_files == 0:
        return

    print(f"\n📂 Processing: {meeting_name}/Docs")
    print(f"   PPTX files: {len(pptx_files)}")
    print(f"   XLSX files: {len(xlsx_files)}")

    copied = 0

    # Process PPTX files
    for pptx_path in pptx_files:
        stats['total_files'] += 1

        # Get relative path from Docs folder
        rel_path = pptx_path.relative_to(docs_path)

        # Determine output path (same structure in data_transformed)
        dst_path = DATA_TRANSFORMED / meeting_name / "Docs" / rel_path

        copy_file_if_not_exists(pptx_path, dst_path, 'pptx')
        copied += 1

        if copied % 50 == 0:
            print(f"   Progress: {copied}/{total_files} files")

    # Process XLSX files
    for xlsx_path in xlsx_files:
        stats['total_files'] += 1

        # Get relative path from Docs folder
        rel_path = xlsx_path.relative_to(docs_path)

        # Determine output path (same structure in data_transformed)
        dst_path = DATA_TRANSFORMED / meeting_name / "Docs" / rel_path

        copy_file_if_not_exists(xlsx_path, dst_path, 'xlsx')
        copied += 1

        if copied % 50 == 0:
            print(f"   Progress: {copied}/{total_files} files")

    print(f"   ✅ Completed: {meeting_name}")


def main():
    print("=" * 80)
    print("Phase-1 Step-6-1: Copy Modern Format Files (PPTX, XLSX)")
    print("=" * 80)

    # Create output directory
    DATA_TRANSFORMED.mkdir(parents=True, exist_ok=True)

    # Get all meeting folders
    meeting_folders = sorted([
        d for d in DATA_EXTRACTED.iterdir()
        if d.is_dir() and d.name.startswith('TSGR1_')
    ])

    print(f"\n📊 Found {len(meeting_folders)} meeting folders")

    # First, count total files
    total_pptx_count = 0
    total_xlsx_count = 0
    for meeting_path in meeting_folders:
        docs_path = meeting_path / "Docs"
        if docs_path.exists():
            total_pptx_count += len(list(docs_path.rglob("*.pptx")))
            total_xlsx_count += len(list(docs_path.rglob("*.xlsx")))

    print(f"📊 Total files to copy:")
    print(f"   PPTX: {total_pptx_count}")
    print(f"   XLSX: {total_xlsx_count}")
    print(f"   Total: {total_pptx_count + total_xlsx_count}")

    # Process each meeting
    for meeting_path in meeting_folders:
        process_meeting_modern_files(meeting_path)

    # Save statistics
    stats['end_time'] = datetime.now().isoformat()
    stats['duration_seconds'] = (
        datetime.fromisoformat(stats['end_time']) -
        datetime.fromisoformat(stats['start_time'])
    ).total_seconds()

    stats_file = LOG_DIR / 'copy_modern_formats_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("📊 COPY SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {stats['total_files']}")
    print(f"  PPTX copied: {stats['pptx_copied']}")
    print(f"  XLSX copied: {stats['xlsx_copied']}")
    print(f"  Already exists (skipped): {stats['skipped_already_exists']}")
    print(f"  Copy errors: {len(stats['copy_errors'])}")
    print(f"\nDuration: {stats['duration_seconds']:.1f} seconds")
    print(f"\n💾 Statistics saved: {stats_file}")
    print(f"📁 Output directory: {DATA_TRANSFORMED}")
    print("=" * 80)

    # Print errors if any
    if stats['copy_errors']:
        print(f"\n⚠️  Copy Errors ({len(stats['copy_errors'])}):")
        for error in stats['copy_errors'][:10]:  # Show first 10
            print(f"  - {error['file']}")
            print(f"    Error: {error['error']}")
        if len(stats['copy_errors']) > 10:
            print(f"  ... and {len(stats['copy_errors']) - 10} more errors")

    # Return exit code
    return 0 if len(stats['copy_errors']) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
