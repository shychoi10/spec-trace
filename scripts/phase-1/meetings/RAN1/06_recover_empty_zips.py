#!/usr/bin/env python3
"""
Phase-1 Step-4 Sub-step 4: Recover Empty ZIPs with 7zip

Target: 88 empty folders (ZIP extracted but empty)
Method: Try 7zip extraction (better at handling corrupted ZIPs)
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path("/home/sihyeon/workspace/spec-trace")
VERIFICATION_REPORT = PROJECT_ROOT / "logs/phase-1/meetings/RAN1/extraction_verification.json"
DATA_RAW = PROJECT_ROOT / "data/data_raw/meetings/RAN1"
DATA_EXTRACTED = PROJECT_ROOT / "data/data_extracted/meetings/RAN1"
RECOVERY_REPORT = PROJECT_ROOT / "logs/phase-1/meetings/RAN1/empty_zip_recovery_report.json"
RECOVERY_LOG = PROJECT_ROOT / "logs/phase-1/meetings/RAN1/empty_zip_recovery.log"

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_attempts': 0,
    'success': 0,
    'failed': 0,
    'recovered_files': 0,
    'success_details': [],
    'failed_details': []
}


def recover_with_7zip(zip_path: Path, output_dir: Path) -> dict:
    """
    Try to recover ZIP with 7zip

    Returns:
        dict: {'success': bool, 'files': int, 'error': str}
    """
    try:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Try 7zip extraction
        cmd = [
            '7z',
            'x',  # Extract with full paths
            str(zip_path),
            f'-o{output_dir}',
            '-y'  # Assume Yes on all queries
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Check extracted files
            extracted_files = list(output_dir.rglob('*'))
            file_count = len([f for f in extracted_files if f.is_file()])

            if file_count > 0:
                return {
                    'success': True,
                    'files': file_count,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'files': 0,
                    'error': '7zip succeeded but no files extracted'
                }
        else:
            return {
                'success': False,
                'files': 0,
                'error': f'7zip failed: {result.stderr[:200]}'
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'files': 0,
            'error': 'Timeout (60s)'
        }
    except Exception as e:
        return {
            'success': False,
            'files': 0,
            'error': f'Exception: {str(e)}'
        }


def main():
    print("=" * 80)
    print("Phase-1 Step-4 Sub-step 4: Empty ZIP Recovery")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Load verification report
    with open(VERIFICATION_REPORT, 'r') as f:
        verification = json.load(f)

    empty_details = verification.get('empty_details', [])
    stats['total_attempts'] = len(empty_details)

    print(f"\nTarget: {len(empty_details)} empty ZIPs")
    print("Method: 7zip extraction\n")

    # Open log file
    with open(RECOVERY_LOG, 'w') as log:
        log.write(f"Empty ZIP Recovery Log\n")
        log.write(f"Started: {datetime.now().isoformat()}\n")
        log.write("=" * 80 + "\n\n")

        # Process each empty ZIP
        for i, detail in enumerate(empty_details, 1):
            zip_rel_path = detail['zip']
            zip_path = DATA_RAW / zip_rel_path

            # Calculate output directory
            # zip_rel_path: TSGR1_XXX/Docs/R1-YYYYYYY.zip
            # output: TSGR1_XXX/Docs/R1-YYYYYYY/
            parts = Path(zip_rel_path).parts
            output_rel = Path(*parts[:-1]) / Path(zip_rel_path).stem
            output_dir = DATA_EXTRACTED / output_rel

            print(f"[{i}/{len(empty_details)}] Processing: {Path(zip_rel_path).name}")
            log.write(f"[{i}/{len(empty_details)}] {zip_rel_path}\n")

            # Try recovery
            result = recover_with_7zip(zip_path, output_dir)

            if result['success']:
                stats['success'] += 1
                stats['recovered_files'] += result['files']
                stats['success_details'].append({
                    'zip': zip_rel_path,
                    'files': result['files']
                })
                print(f"  ✅ Success: {result['files']} files recovered")
                log.write(f"  SUCCESS: {result['files']} files\n")
            else:
                stats['failed'] += 1
                stats['failed_details'].append({
                    'zip': zip_rel_path,
                    'error': result['error']
                })
                print(f"  ❌ Failed: {result['error'][:60]}")
                log.write(f"  FAILED: {result['error']}\n")

            log.write("\n")

            # Progress
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(empty_details)} ({i/len(empty_details)*100:.1f}%)")
                print(f"  Current stats: {stats['success']} success, {stats['failed']} failed\n")

    # Save report
    stats['end_time'] = datetime.now().isoformat()
    stats['duration_seconds'] = (
        datetime.fromisoformat(stats['end_time']) -
        datetime.fromisoformat(stats['start_time'])
    ).total_seconds()

    with open(RECOVERY_REPORT, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("RECOVERY SUMMARY")
    print("=" * 80)
    print(f"Total attempts:     {stats['total_attempts']}")
    print(f"  ✅ Success:        {stats['success']}")
    print(f"  ❌ Failed:         {stats['failed']}")
    print(f"\nRecovered files:    {stats['recovered_files']}")
    print(f"Success rate:       {stats['success']/stats['total_attempts']*100:.1f}%")
    print(f"\nDuration:           {stats['duration_seconds']:.1f}s ({stats['duration_seconds']/60:.1f}min)")
    print(f"\nReport saved:       {RECOVERY_REPORT}")
    print(f"Log saved:          {RECOVERY_LOG}")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
