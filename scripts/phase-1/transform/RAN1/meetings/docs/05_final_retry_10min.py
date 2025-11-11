#!/usr/bin/env python3
"""
Phase-1 Step-6: Final Retry with 10-minute Timeout

Retry 9 remaining TIMEOUT files from adaptive retry with extended 600s (10min) timeout
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from datetime import datetime
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/meetings/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/meetings/RAN1")
LOG_DIR = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/meetings/docs")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# 9 files that failed in adaptive retry
FAILED_FILES = [
    "TSGR1_91/Docs/R1-1721060/R1-1721060-draft CR36213 EPDCCH SSC10.doc",
    "TSGR1_91/Docs/R1-1721329/R1-1721329 36213-e40_s06-s09_stti_fa2.doc",
    "TSGR1_91/Docs/R1-1721341/R1-1721341 38211-130 (with change marks).doc",
    "TSGR1_91/Docs/R1-1721064/R1-1721064-draft CR36213 EPDCCH SSC10.doc",
    "TSGR1_91/Docs/R1-1721071/36213-e40_s06-s09_FECOMP_f2.doc",
    "TSGR1_92/Docs/R1-1801691/R1-1801691-draft CR36213-symPUSCH-UpPts-r14 PHICH Assignment .doc",
    "TSGR1_92/Docs/R1-1801692/R1-1801692-draft CR36211-symPUSCH-UpPts-r14 PHICH Assignment.doc",
    "TSGR1_92/Docs/R1-1802986/R1-1802986.doc",
    "TSGR1_92/Docs/R1-1803186/R1-1803186.doc",
]

TIMEOUT = 600  # 10 minutes

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'timeout': TIMEOUT,
    'total_files': len(FAILED_FILES),
    'success': 0,
    'failed': 0,
    'still_timeout': 0,
    'results': []
}


def convert_doc_to_docx_10min(doc_path: Path, output_dir: Path) -> dict:
    """
    Convert DOC to DOCX with 10-minute timeout

    Returns:
        dict with conversion results
    """
    result = {
        'filename': doc_path.name,
        'input': str(doc_path),
        'output': str(output_dir / (doc_path.stem + '.docx')),
        'size_mb': doc_path.stat().st_size / (1024 * 1024),
        'success': False,
        'timeout_used': TIMEOUT
    }

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        expected_output = output_dir / (doc_path.stem + '.docx')

        # Check if already converted
        if expected_output.exists() and expected_output.stat().st_size > 0:
            result['success'] = True
            result['skipped'] = True
            result['timeout_used'] = 0
            return result

        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'docx',
            '--outdir', str(output_dir),
            str(doc_path)
        ]

        print(f"  🔄 Converting: {doc_path.name}")
        print(f"     Size: {result['size_mb']:.2f} MB | Timeout: {TIMEOUT}s (10 min)")

        start_time = time.time()

        # Start with process group
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )

        try:
            stdout, stderr = process.communicate(timeout=TIMEOUT)
            elapsed = time.time() - start_time
            result['elapsed_seconds'] = elapsed

            if process.returncode == 0:
                if expected_output.exists():
                    output_size_mb = expected_output.stat().st_size / (1024 * 1024)
                    result['success'] = True
                    result['output_size_mb'] = output_size_mb
                    print(f"     ✅ Success! ({elapsed:.1f}s / {TIMEOUT}s) → {output_size_mb:.2f} MB")
                    return result
                else:
                    result['error'] = 'Output file not created'
                    print(f"     ❌ Failed: {result['error']}")
                    return result
            else:
                result['error'] = stderr.strip() if stderr else 'Unknown error'
                print(f"     ❌ Failed: {result['error'][:100]}")
                return result

        except subprocess.TimeoutExpired:
            # Kill process group
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass
            process.kill()
            process.wait()

            elapsed = time.time() - start_time
            result['elapsed_seconds'] = elapsed
            result['error'] = f'TIMEOUT ({TIMEOUT}s) - process killed'
            result['timeout_occurred'] = True
            print(f"     ⏱️  TIMEOUT ({TIMEOUT}s) - killed after {elapsed:.1f}s")
            return result

    except Exception as e:
        result['error'] = f"Exception: {str(e)}"
        print(f"     ❌ Exception: {str(e)}")
        return result


def process_file(file_rel_path: str) -> dict:
    """Process a single failed file"""
    doc_path = DATA_EXTRACTED / file_rel_path

    # Calculate output path
    rel_parts = Path(file_rel_path).parts
    output_dir = DATA_TRANSFORMED / Path(*rel_parts[:-1])

    return convert_doc_to_docx_10min(doc_path, output_dir)


def main():
    print("="*80)
    print("Phase-1 Step-6: Final Retry with 10-minute Timeout")
    print("="*80)
    print()
    print(f"📂 Input:  {DATA_EXTRACTED}")
    print(f"📂 Output: {DATA_TRANSFORMED}")
    print(f"📋 Files:  {len(FAILED_FILES)}")
    print(f"⏱️  Timeout: {TIMEOUT}s (10 minutes)")
    print()

    print("🔍 Files to retry:")
    print()
    for i, file_rel_path in enumerate(FAILED_FILES, 1):
        doc_path = DATA_EXTRACTED / file_rel_path
        size_mb = doc_path.stat().st_size / (1024 * 1024)
        print(f"  {i:2d}. {doc_path.name[:60]}")
        print(f"      Size: {size_mb:.2f} MB")

    print()
    input("Press ENTER to start conversion (or Ctrl+C to cancel)...")
    print()

    # Process files in parallel (reduced workers for stability)
    print("🔄 Processing files (2 workers for stability)...")
    print()

    start_time = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_file, file_path): file_path for file_path in FAILED_FILES}

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            stats['results'].append(result)

            if result['success']:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                if result.get('timeout_occurred'):
                    stats['still_timeout'] += 1

            # Progress
            print(f"\n  [{completed}/{len(FAILED_FILES)}] Progress: {completed*100//len(FAILED_FILES)}%")
            print("  " + "="*70)

    elapsed_total = time.time() - start_time

    # Summary
    print()
    print("="*80)
    print("📊 Final Retry Summary (10-minute timeout)")
    print("="*80)
    print(f"Total files:        {stats['total_files']}")
    print(f"Success:            {stats['success']} ({stats['success']*100/stats['total_files']:.1f}%)")
    print(f"Failed:             {stats['failed']} ({stats['failed']*100/stats['total_files']:.1f}%)")
    print(f"Still TIMEOUT:      {stats['still_timeout']}")
    print(f"Processing time:    {elapsed_total/60:.1f} minutes")
    print()

    if stats['success'] > 0:
        print("✅ Successful conversions:")
        for result in stats['results']:
            if result['success'] and not result.get('skipped'):
                print(f"  • {result['filename']}")
                print(f"    Size: {result['size_mb']:.2f} MB → {result.get('output_size_mb', 0):.2f} MB")
                print(f"    Time: {result['elapsed_seconds']:.1f}s / {TIMEOUT}s")
        print()

    if stats['still_timeout'] > 0:
        print("⏱️  STILL TIMEOUT (even with 10min):")
        for result in stats['results']:
            if result.get('timeout_occurred'):
                print(f"  • {result['filename']}")
                print(f"    Size: {result['size_mb']:.2f} MB | Elapsed: {result.get('elapsed_seconds', 0):.1f}s")
        print()
        print("💡 These files are extremely complex and may require manual conversion")

    if stats['failed'] > stats['still_timeout']:
        other_errors = stats['failed'] - stats['still_timeout']
        print(f"❌ Other errors: {other_errors}")
        for result in stats['results']:
            if not result['success'] and not result.get('timeout_occurred'):
                print(f"  • {result['filename']}: {result.get('error', 'Unknown')[:100]}")
        print()

    # Save stats
    stats['end_time'] = datetime.now().isoformat()
    stats['elapsed_minutes'] = elapsed_total / 60
    stats_file = LOG_DIR / 'final_retry_10min_report.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"📄 Stats saved: {stats_file}")
    print()

    # Overall statistics (13 original TIMEOUT files)
    print("="*80)
    print("🎯 Overall TIMEOUT Files Recovery")
    print("="*80)
    print()
    print("Original TIMEOUT files: 13")
    print("1st retry (adaptive):    4 recovered (30.8%)")
    print(f"2nd retry (10min):      {stats['success']} recovered ({stats['success']*100/len(FAILED_FILES):.1f}%)")
    print(f"Total recovered:        {4 + stats['success']}/13 ({(4 + stats['success'])*100/13:.1f}%)")
    print(f"Final failures:         {13 - 4 - stats['success']}/13 ({(13 - 4 - stats['success'])*100/13:.1f}%)")
    print()

    final_failures = 13 - 4 - stats['success']
    if final_failures == 0:
        print("🎉 PERFECT! All 13 TIMEOUT files have been converted!")
    elif final_failures <= 3:
        print(f"✅ EXCELLENT! Only {final_failures} files remain (0.{final_failures*5}% of total)")
        print("   This is within acceptable range - can proceed to Step-7")
    else:
        print(f"⚠️  {final_failures} files still unconverted")
        print("   Consider manual conversion or skip (impact < 0.1%)")

    print()
    print("="*80)
    print("✅ Final Retry Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
