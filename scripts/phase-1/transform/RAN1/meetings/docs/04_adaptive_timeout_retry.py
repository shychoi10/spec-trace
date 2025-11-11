#!/usr/bin/env python3
"""
Phase-1 Step-6: Adaptive Timeout Retry for 13 TIMEOUT Files

Strategy:
- Size-based adaptive timeout (60s - 600s)
- Pattern-based additional timeout (draft CR, with change marks, spec)
- Parallel processing (4 workers)
- Expected success rate: 70-85% (9-11 files)

Timeout Logic:
- <0.5 MB: 60s
- 0.5-4 MB: 120s
- 4-10 MB: 300s (5min)
- ≥10 MB: 600s (10min)
- +60s if "draft CR"
- +120s if "with change marks"
- +60s if starts with "36" or "38" (spec)
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

# 13 TIMEOUT files from previous retry
TIMEOUT_FILES = [
    # TSGR1_91 (6 files)
    "TSGR1_91/Docs/R1-1721060/R1-1721060-draft CR36213 EPDCCH SSC10.doc",
    "TSGR1_91/Docs/R1-1721329/R1-1721329 36213-e40_s06-s09_stti_fa2.doc",
    "TSGR1_91/Docs/R1-1721341/R1-1721341 38211-130 (with change marks).doc",
    "TSGR1_91/Docs/R1-1721099/R1-1721099.doc",
    "TSGR1_91/Docs/R1-1721064/R1-1721064-draft CR36213 EPDCCH SSC10.doc",
    "TSGR1_91/Docs/R1-1721071/36213-e40_s06-s09_FECOMP_f2.doc",
    # TSGR1_92 (7 files)
    "TSGR1_92/Docs/R1-1801691/R1-1801691-draft CR36213-symPUSCH-UpPts-r14 PHICH Assignment .doc",
    "TSGR1_92/Docs/R1-1801692/R1-1801692-draft CR36211-symPUSCH-UpPts-r14 PHICH Assignment.doc",
    "TSGR1_92/Docs/R1-1803543/R1-1803543 CR 38.211 after RAN1_92.doc",
    "TSGR1_92/Docs/R1-1802986/R1-1802986.doc",
    "TSGR1_92/Docs/R1-1803185/R1-1803185.doc",
    "TSGR1_92/Docs/R1-1803186/R1-1803186.doc",
    "TSGR1_92/Docs/R1-1803179/R1-1803179.doc",
]

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_files': len(TIMEOUT_FILES),
    'success': 0,
    'failed': 0,
    'still_timeout': 0,
    'results': []
}


def calculate_adaptive_timeout(file_path: Path) -> int:
    """
    Calculate adaptive timeout based on file size and filename patterns

    Returns:
        timeout in seconds
    """
    size_mb = file_path.stat().st_size / (1024 * 1024)
    filename = file_path.name.lower()

    # Size-based base timeout
    if size_mb < 0.5:
        timeout = 60
    elif size_mb < 4:
        timeout = 120
    elif size_mb < 10:
        timeout = 300  # 5 minutes
    else:
        timeout = 600  # 10 minutes

    # Pattern-based additional timeout
    if "draft cr" in filename:
        timeout += 60  # Track changes possibility

    if "with change marks" in filename:
        timeout += 120  # Explicit track changes

    # Spec documents (starts with 36 or 38)
    basename = file_path.stem.split()[0] if ' ' in file_path.stem else file_path.stem
    if basename.startswith(('36', '38')):
        timeout += 60

    return timeout


def convert_doc_to_docx_adaptive(doc_path: Path, output_dir: Path) -> dict:
    """
    Convert DOC to DOCX with adaptive timeout

    Returns:
        dict with conversion results
    """
    result = {
        'filename': doc_path.name,
        'input': str(doc_path),
        'output': str(output_dir / (doc_path.stem + '.docx')),
        'size_mb': doc_path.stat().st_size / (1024 * 1024),
        'success': False
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

        # Calculate adaptive timeout
        timeout = calculate_adaptive_timeout(doc_path)
        result['timeout_used'] = timeout

        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'docx',
            '--outdir', str(output_dir),
            str(doc_path)
        ]

        print(f"  🔄 Converting: {doc_path.name}")
        print(f"     Size: {result['size_mb']:.2f} MB | Timeout: {timeout}s ({timeout//60}m {timeout%60}s)")

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
            stdout, stderr = process.communicate(timeout=timeout)
            elapsed = time.time() - start_time
            result['elapsed_seconds'] = elapsed

            if process.returncode == 0:
                if expected_output.exists():
                    output_size_mb = expected_output.stat().st_size / (1024 * 1024)
                    result['success'] = True
                    result['output_size_mb'] = output_size_mb
                    print(f"     ✅ Success! ({elapsed:.1f}s / {timeout}s) → {output_size_mb:.2f} MB")
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
            result['error'] = f'TIMEOUT ({timeout}s) - process killed'
            result['timeout_occurred'] = True
            print(f"     ⏱️  TIMEOUT ({timeout}s) - killed after {elapsed:.1f}s")
            return result

    except Exception as e:
        result['error'] = f"Exception: {str(e)}"
        print(f"     ❌ Exception: {str(e)}")
        return result


def process_file(file_rel_path: str) -> dict:
    """Process a single TIMEOUT file"""
    doc_path = DATA_EXTRACTED / file_rel_path

    # Calculate output path
    rel_parts = Path(file_rel_path).parts
    output_dir = DATA_TRANSFORMED / Path(*rel_parts[:-1])

    return convert_doc_to_docx_adaptive(doc_path, output_dir)


def main():
    print("="*80)
    print("Phase-1 Step-6: Adaptive Timeout Retry for 13 TIMEOUT Files")
    print("="*80)
    print()
    print(f"📂 Input:  {DATA_EXTRACTED}")
    print(f"📂 Output: {DATA_TRANSFORMED}")
    print(f"📋 Files:  {len(TIMEOUT_FILES)}")
    print()

    print("📊 Adaptive Timeout Strategy:")
    print("  • <0.5 MB:   60s  (1 min)")
    print("  • 0.5-4 MB:  120s (2 min)")
    print("  • 4-10 MB:   300s (5 min)")
    print("  • ≥10 MB:    600s (10 min)")
    print("  • +60s  if 'draft CR'")
    print("  • +120s if 'with change marks'")
    print("  • +60s  if spec (36xxx/38xxx)")
    print()

    # Analyze file sizes first
    print("🔍 Pre-flight Analysis:")
    print()
    for i, file_rel_path in enumerate(TIMEOUT_FILES, 1):
        doc_path = DATA_EXTRACTED / file_rel_path
        size_mb = doc_path.stat().st_size / (1024 * 1024)
        timeout = calculate_adaptive_timeout(doc_path)
        print(f"  {i:2d}. {doc_path.name[:60]}")
        print(f"      Size: {size_mb:.2f} MB → Timeout: {timeout}s ({timeout//60}m {timeout%60}s)")

    print()
    input("Press ENTER to start conversion (or Ctrl+C to cancel)...")
    print()

    # Process files in parallel
    print("🔄 Processing files (4 workers)...")
    print()

    start_time = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_file, file_path): file_path for file_path in TIMEOUT_FILES}

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
            print(f"\n  [{completed}/{len(TIMEOUT_FILES)}] Progress: {completed*100//len(TIMEOUT_FILES)}%")
            print("  " + "="*70)

    elapsed_total = time.time() - start_time

    # Summary
    print()
    print("="*80)
    print("📊 Adaptive Timeout Retry Summary")
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
                print(f"    Time: {result['elapsed_seconds']:.1f}s / {result['timeout_used']}s")
        print()

    if stats['still_timeout'] > 0:
        print("⏱️  Still TIMEOUT:")
        for result in stats['results']:
            if result.get('timeout_occurred'):
                print(f"  • {result['filename']}")
                print(f"    Size: {result['size_mb']:.2f} MB | Timeout: {result['timeout_used']}s")
        print()
        print(f"💡 Recommendation: Run 2nd retry with 10min (600s) timeout for {stats['still_timeout']} files")

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
    stats_file = LOG_DIR / 'adaptive_retry_report.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"📄 Stats saved: {stats_file}")
    print()

    # Final verification
    print("="*80)
    print("🔍 Final Verification")
    print("="*80)

    still_doc = []
    for file_rel_path in TIMEOUT_FILES:
        doc_path = DATA_EXTRACTED / file_rel_path
        rel_parts = Path(file_rel_path).parts
        docx_path = DATA_TRANSFORMED / Path(*rel_parts[:-1]) / (doc_path.stem + '.docx')

        if not docx_path.exists():
            still_doc.append(doc_path.name)

    print(f"Remaining unconverted: {len(still_doc)}/{len(TIMEOUT_FILES)}")

    if len(still_doc) == 0:
        print()
        print("🎉 SUCCESS: All 13 files converted!")
        print()
        print("="*80)
        print("✅ Adaptive Timeout Retry Complete!")
        print("="*80)
    else:
        print()
        print("Files still not converted:")
        for filename in still_doc:
            print(f"  • {filename}")
        print()
        print("="*80)
        print("⚠️  Partial Success - 2nd retry recommended")
        print("="*80)


if __name__ == "__main__":
    main()
