#!/usr/bin/env python3
"""
Phase-1 Step-6: Transform Change Requests DOC to DOCX

Convert 514 DOC files (19.6%) to DOCX across 5 Releases (Rel-15 to Rel-19)
Total: 2,622 files, 238 MB

Strategy:
- Parallel processing (8 workers) for faster conversion
- File-level resume (skip already converted files)
- 60s timeout per file
- Copy DOCX as-is, convert DOC to DOCX
"""

import os
import sys
import shutil
import subprocess
import signal
from pathlib import Path
from datetime import datetime
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/change-requests/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/change-requests/RAN1")
LOG_DIR = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/change-requests")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Target Releases
RELEASES = ['Rel-15', 'Rel-16', 'Rel-17', 'Rel-18', 'Rel-19']

# Statistics (thread-safe via separate tracking)
stats = {
    'start_time': datetime.now().isoformat(),
    'total_files': 0,
    'docx_copied': 0,
    'doc_converted': 0,
    'skipped_already_converted': 0,
    'errors': [],
    'timeout_files': []
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


def convert_doc_to_docx(doc_path: Path, output_file: Path) -> dict:
    """
    Convert DOC to DOCX with timeout handling

    Returns:
        dict: {'success': bool, 'file': str, 'error': str (if failed)}
    """
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if already converted
        if output_file.exists() and output_file.stat().st_size > 0:
            return {'success': True, 'file': str(doc_path), 'skipped': True}

        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'docx',
            '--outdir', str(output_file.parent),
            str(doc_path)
        ]

        # Start with process group
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )

        try:
            stdout, stderr = process.communicate(timeout=60)

            if process.returncode == 0:
                if output_file.exists():
                    return {'success': True, 'file': str(doc_path)}
                else:
                    return {
                        'success': False,
                        'file': str(doc_path),
                        'error': 'Output file not created'
                    }
            else:
                return {
                    'success': False,
                    'file': str(doc_path),
                    'error': stderr.strip() if stderr else 'Unknown error'
                }

        except subprocess.TimeoutExpired:
            # Kill process group
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass
            process.kill()
            process.wait()

            return {
                'success': False,
                'file': str(doc_path),
                'error': 'Timeout (60s)',
                'timeout': True
            }

    except Exception as e:
        return {
            'success': False,
            'file': str(doc_path),
            'error': f"Exception: {str(e)}"
        }


def copy_docx(docx_path: Path, output_file: Path) -> dict:
    """
    Copy DOCX as-is

    Returns:
        dict: {'success': bool, 'file': str, 'copied': bool}
    """
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if not output_file.exists():
            shutil.copy2(docx_path, output_file)
            return {'success': True, 'file': str(docx_path), 'copied': True}
        else:
            return {'success': True, 'file': str(docx_path), 'skipped': True}

    except Exception as e:
        return {
            'success': False,
            'file': str(docx_path),
            'error': f"Copy error: {str(e)}"
        }


def process_file(file_info: tuple) -> dict:
    """
    Process a single file (DOC or DOCX)

    Args:
        file_info: (file_path, output_file, file_type)

    Returns:
        dict: Processing result
    """
    file_path, output_file, file_type = file_info

    if file_type == 'docx':
        return copy_docx(file_path, output_file)
    elif file_type == 'doc':
        return convert_doc_to_docx(file_path, output_file)
    else:
        return {
            'success': False,
            'file': str(file_path),
            'error': f"Unknown file type: {file_type}"
        }


def main():
    print("="*70)
    print("Phase-1 Step-6: Transform Change Requests DOC to DOCX")
    print("="*70)
    print()

    # Check LibreOffice
    if not check_libreoffice():
        print("❌ LibreOffice is required. Install with: sudo apt-get install libreoffice")
        sys.exit(1)

    print()
    print(f"📂 Input:  {DATA_EXTRACTED}")
    print(f"📂 Output: {DATA_TRANSFORMED}")
    print(f"📋 Releases: {', '.join(RELEASES)}")
    print()

    # Collect all files to process
    files_to_process = []

    for release in RELEASES:
        release_dir = DATA_EXTRACTED / release
        if not release_dir.exists():
            print(f"⚠️  Release not found: {release}")
            continue

        for file_path in sorted(release_dir.rglob('*')):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in ['.doc', '.docx']:
                continue

            # Calculate relative path and output location
            rel_path = file_path.relative_to(DATA_EXTRACTED)

            if suffix == '.doc':
                # Convert DOC to DOCX
                output_file = DATA_TRANSFORMED / rel_path.parent / (file_path.stem + '.docx')
                files_to_process.append((file_path, output_file, 'doc'))
            else:
                # Copy DOCX as-is
                output_file = DATA_TRANSFORMED / rel_path
                files_to_process.append((file_path, output_file, 'docx'))

    stats['total_files'] = len(files_to_process)

    print(f"📊 Total files to process: {stats['total_files']}")
    print()

    # Process files in parallel
    print("🔄 Processing files (8 workers)...")
    print()

    start_time = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_file, file_info): file_info for file_info in files_to_process}

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            if result['success']:
                if result.get('skipped'):
                    stats['skipped_already_converted'] += 1
                elif result.get('copied'):
                    stats['docx_copied'] += 1
                else:
                    stats['doc_converted'] += 1
            else:
                if result.get('timeout'):
                    stats['timeout_files'].append({
                        'file': result['file'],
                        'error': result['error']
                    })
                else:
                    stats['errors'].append({
                        'file': result['file'],
                        'error': result['error']
                    })

            # Progress update every 50 files
            if completed % 50 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = (stats['total_files'] - completed) / rate if rate > 0 else 0
                print(f"  Progress: {completed}/{stats['total_files']} "
                      f"({completed*100//stats['total_files']}%) | "
                      f"Rate: {rate:.1f} files/s | "
                      f"ETA: {remaining/60:.1f} min")

    elapsed_total = time.time() - start_time

    print()
    print("="*70)
    print("📊 Transform Summary")
    print("="*70)
    print(f"Total files:           {stats['total_files']}")
    print(f"DOCX copied:           {stats['docx_copied']}")
    print(f"DOC converted:         {stats['doc_converted']}")
    print(f"Already converted:     {stats['skipped_already_converted']}")
    print(f"Errors:                {len(stats['errors'])}")
    print(f"Timeouts:              {len(stats['timeout_files'])}")
    print(f"Processing time:       {elapsed_total/60:.1f} minutes")
    print(f"Average rate:          {stats['total_files']/elapsed_total:.1f} files/s")
    print()

    if stats['timeout_files']:
        print("⏱️  Timeout files:")
        for item in stats['timeout_files'][:10]:  # Show first 10
            print(f"  - {Path(item['file']).name}")
        if len(stats['timeout_files']) > 10:
            print(f"  ... and {len(stats['timeout_files']) - 10} more")
        print()

    if stats['errors']:
        print("❌ Errors:")
        for item in stats['errors'][:10]:  # Show first 10
            print(f"  - {Path(item['file']).name}: {item['error']}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")
        print()

    # Save stats
    stats['end_time'] = datetime.now().isoformat()
    stats['elapsed_minutes'] = elapsed_total / 60
    stats_file = LOG_DIR / 'transform_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"📄 Stats saved: {stats_file}")
    print()

    # Verification
    print("="*70)
    print("🔍 Verification")
    print("="*70)

    doc_count = sum(1 for _ in DATA_TRANSFORMED.rglob('*.doc'))
    docx_count = sum(1 for _ in DATA_TRANSFORMED.rglob('*.docx'))

    print(f"Remaining DOC:   {doc_count}")
    print(f"Total DOCX:      {docx_count}")
    print()

    if doc_count == 0:
        print("✅ SUCCESS: All DOC files converted to DOCX!")
    else:
        print(f"⚠️  WARNING: {doc_count} DOC files remain")
        print()
        print("Remaining DOC files:")
        for doc_file in list(DATA_TRANSFORMED.rglob('*.doc'))[:10]:
            print(f"  - {doc_file.relative_to(DATA_TRANSFORMED)}")
        if doc_count > 10:
            print(f"  ... and {doc_count - 10} more")

    print()
    print("="*70)
    print("✅ Change Requests Transform Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
