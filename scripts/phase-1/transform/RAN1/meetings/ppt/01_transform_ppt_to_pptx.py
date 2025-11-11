#!/usr/bin/env python3
"""
Phase-1 Step-6-1: Transform PPT to PPTX
Convert legacy PPT files to PPTX format for unified parsing
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/meetings/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/meetings/RAN1")
LOG_DIR = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/meetings/ppt")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_ppt_files': 0,
    'ppt_converted': 0,
    'conversion_errors': [],
    'skipped_already_converted': 0
}


def check_libreoffice():
    """Check if LibreOffice is available"""
    try:
        result = subprocess.run(['which', 'soffice'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ LibreOffice found: {result.stdout.strip()}")
            return True
        else:
            print("❌ LibreOffice not found")
            return False
    except Exception as e:
        print(f"❌ Error checking LibreOffice: {e}")
        return False


def convert_ppt_to_pptx(ppt_path: Path, output_dir: Path) -> bool:
    """
    Convert PPT to PPTX using LibreOffice headless

    Args:
        ppt_path: Path to PPT file
        output_dir: Output directory for PPTX

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if already converted (Resume support)
        expected_output = output_dir / (ppt_path.stem + '.pptx')
        if expected_output.exists() and expected_output.stat().st_size > 0:
            stats['skipped_already_converted'] += 1
            return True  # Already converted, skip

        # Run LibreOffice conversion
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pptx',
            '--outdir', str(output_dir),
            str(ppt_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout per file (PPT can be large)
        )

        if result.returncode == 0:
            # Check if output file was created
            if expected_output.exists():
                return True
            else:
                stats['conversion_errors'].append({
                    'file': str(ppt_path),
                    'error': 'Output file not created'
                })
                return False
        else:
            stats['conversion_errors'].append({
                'file': str(ppt_path),
                'error': result.stderr
            })
            return False

    except subprocess.TimeoutExpired as e:
        # Force kill the process
        try:
            if hasattr(e, 'process') and e.process:
                e.process.kill()
                # Also kill any child LibreOffice processes
                subprocess.run(['pkill', '-9', '-f', 'soffice.*headless'],
                             capture_output=True, timeout=5)
        except:
            pass

        stats['conversion_errors'].append({
            'file': str(ppt_path),
            'error': 'Timeout (60s) - process killed'
        })
        return False
    except Exception as e:
        stats['conversion_errors'].append({
            'file': str(ppt_path),
            'error': str(e)
        })
        return False


def process_meeting_ppt_files(meeting_path: Path):
    """
    Process all PPT files in a meeting's Docs folder

    Args:
        meeting_path: Path to meeting folder (e.g., TSGR1_84)
    """
    docs_path = meeting_path / "Docs"

    if not docs_path.exists():
        return

    meeting_name = meeting_path.name

    # Find all PPT files recursively
    ppt_files = list(docs_path.rglob("*.ppt"))

    if not ppt_files:
        return

    print(f"\n📂 Processing: {meeting_name}/Docs")
    print(f"   PPT files: {len(ppt_files)}")

    for idx, ppt_path in enumerate(ppt_files, 1):
        stats['total_ppt_files'] += 1

        # Get relative path from Docs folder
        rel_path = ppt_path.relative_to(docs_path)

        # Determine output path (same structure in data_transformed)
        output_path = DATA_TRANSFORMED / meeting_name / "Docs" / rel_path.parent

        # Convert PPT to PPTX
        if convert_ppt_to_pptx(ppt_path, output_path):
            stats['ppt_converted'] += 1
        else:
            # Conversion failed, but error already logged
            pass

        if idx % 10 == 0 or idx == len(ppt_files):
            print(f"   Progress: {idx}/{len(ppt_files)} files")

    print(f"   ✅ Completed: {meeting_name}")


def main():
    print("=" * 80)
    print("Phase-1 Step-6-1: Transform PPT to PPTX")
    print("=" * 80)

    # Check LibreOffice
    if not check_libreoffice():
        print("\n❌ LibreOffice is required for PPT conversion")
        print("Install with: sudo apt install libreoffice")
        return 1

    # Create output directory
    DATA_TRANSFORMED.mkdir(parents=True, exist_ok=True)

    # Get all meeting folders
    meeting_folders = sorted([
        d for d in DATA_EXTRACTED.iterdir()
        if d.is_dir() and d.name.startswith('TSGR1_')
    ])

    print(f"\n📊 Found {len(meeting_folders)} meeting folders")

    # First, count total PPT files
    total_ppt_count = 0
    for meeting_path in meeting_folders:
        docs_path = meeting_path / "Docs"
        if docs_path.exists():
            total_ppt_count += len(list(docs_path.rglob("*.ppt")))

    print(f"📊 Total PPT files to convert: {total_ppt_count}")

    # Process each meeting
    for meeting_path in meeting_folders:
        process_meeting_ppt_files(meeting_path)

    # Save statistics
    stats['end_time'] = datetime.now().isoformat()
    stats['duration_seconds'] = (
        datetime.fromisoformat(stats['end_time']) -
        datetime.fromisoformat(stats['start_time'])
    ).total_seconds()

    stats_file = LOG_DIR / 'transform_ppt_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("📊 PPT TRANSFORMATION SUMMARY")
    print("=" * 80)
    print(f"Total PPT files: {stats['total_ppt_files']}")
    print(f"  Successfully converted: {stats['ppt_converted']}")
    print(f"  Already converted (skipped): {stats['skipped_already_converted']}")
    print(f"  Conversion errors: {len(stats['conversion_errors'])}")
    print(f"\nDuration: {stats['duration_seconds']:.1f} seconds")
    print(f"\n💾 Statistics saved: {stats_file}")
    print(f"📁 Output directory: {DATA_TRANSFORMED}")
    print("=" * 80)

    # Print errors if any
    if stats['conversion_errors']:
        print(f"\n⚠️  Conversion Errors ({len(stats['conversion_errors'])}):")
        for error in stats['conversion_errors'][:10]:  # Show first 10
            print(f"  - {error['file']}")
            print(f"    Error: {error['error']}")
        if len(stats['conversion_errors']) > 10:
            print(f"  ... and {len(stats['conversion_errors']) - 10} more errors")

    # Return exit code
    return 0 if len(stats['conversion_errors']) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
