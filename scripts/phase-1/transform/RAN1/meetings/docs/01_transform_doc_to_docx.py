#!/usr/bin/env python3
"""
Phase-1 Step-6-1: Transform ALL Meetings (Docs + Report) - COMPLETE & ROBUST

FIXES:
1. Process both Docs AND Report folders (Report was missing!)
2. Robust timeout with process group kill (fixes 21-hour hang)
3. File-level resume (skip already converted files)
4. Automatic skip of problematic files with logging

CRITICAL BUG FIXED:
- Previous scripts only processed Docs, completely missed Report (58 files)
- LibreOffice timeout didn't work (process group kill now used)

BUG FIX (2025-01-13):
- Added 7 missing meetings to TARGET_MEETINGS: TSGR1_116b, 118b, 120b, 122b, 86, 88b, 90
- Added .docm support (macro-enabled Word documents, copy like .docx)
- 10 Report folders were missing due to incomplete TARGET_MEETINGS and .docm not supported
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

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/meetings/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/meetings/RAN1")
LOG_DIR = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/meetings/docs")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Target: ALL meetings (not just 32 with missing files)
# This ensures Report folders are also processed
TARGET_MEETINGS = [
    'TSGR1_100', 'TSGR1_100_e', 'TSGR1_100b_e',
    'TSGR1_101-e', 'TSGR1_102-e', 'TSGR1_103-e',
    'TSGR1_104-e', 'TSGR1_104b-e', 'TSGR1_105-e',
    'TSGR1_106-e', 'TSGR1_106b-e', 'TSGR1_107-e',
    'TSGR1_107b-e', 'TSGR1_108-e', 'TSGR1_109-e',
    'TSGR1_110', 'TSGR1_110b-e', 'TSGR1_111',
    'TSGR1_112', 'TSGR1_112b-e', 'TSGR1_113',
    'TSGR1_114', 'TSGR1_114b', 'TSGR1_115',
    'TSGR1_116', 'TSGR1_116b', 'TSGR1_117', 'TSGR1_118',
    'TSGR1_118b', 'TSGR1_119', 'TSGR1_120', 'TSGR1_120b',
    'TSGR1_121', 'TSGR1_122', 'TSGR1_122b',
    'TSGR1_84', 'TSGR1_84b', 'TSGR1_85',
    'TSGR1_86', 'TSGR1_86b', 'TSGR1_87', 'TSGR1_88',
    'TSGR1_88b', 'TSGR1_89', 'TSGR1_90', 'TSGR1_90b', 'TSGR1_91',
    'TSGR1_92', 'TSGR1_92b', 'TSGR1_93',
    'TSGR1_94', 'TSGR1_94b', 'TSGR1_95',
    'TSGR1_96', 'TSGR1_96b', 'TSGR1_97',
    'TSGR1_98', 'TSGR1_98b', 'TSGR1_99'
]

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_files': 0,
    'docx_copied': 0,
    'doc_converted': 0,
    'skipped_already_converted': 0,
    'errors': [],
    'conversion_errors': [],
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


def kill_all_soffice():
    """Kill all LibreOffice processes (cleanup after timeout)"""
    try:
        subprocess.run(['pkill', '-9', '-f', 'soffice.*headless'],
                      capture_output=True, timeout=5)
        time.sleep(0.5)
    except:
        pass


def convert_doc_to_docx_robust(doc_path: Path, output_dir: Path) -> bool:
    """
    Convert DOC to DOCX with ROBUST timeout handling

    CRITICAL FIX: Use process group kill to prevent 21-hour hangs
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # File-level resume: skip if already converted
        expected_output = output_dir / (doc_path.stem + '.docx')
        if expected_output.exists() and expected_output.stat().st_size > 0:
            stats['skipped_already_converted'] += 1
            return True

        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'docx',
            '--outdir', str(output_dir),
            str(doc_path)
        ]

        # Start in new process group (critical for timeout)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )

        try:
            stdout, stderr = process.communicate(timeout=30)

            if process.returncode == 0:
                if expected_output.exists():
                    return True
                else:
                    stats['conversion_errors'].append({
                        'file': str(doc_path),
                        'error': 'Output file not created'
                    })
                    return False
            else:
                stats['conversion_errors'].append({
                    'file': str(doc_path),
                    'error': stderr
                })
                return False

        except subprocess.TimeoutExpired:
            # Kill entire process group
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

            kill_all_soffice()

            stats['timeout_files'].append(str(doc_path))
            stats['conversion_errors'].append({
                'file': str(doc_path),
                'error': 'TIMEOUT (30s) - process group killed'
            })

            print(f"      ⚠️  TIMEOUT: {doc_path.name}")
            sys.stdout.flush()

            return False

    except Exception as e:
        stats['conversion_errors'].append({
            'file': str(doc_path),
            'error': str(e)
        })
        return False


def process_folder(folder_path: Path, meeting_name: str, folder_type: str):
    """
    Process a folder (Docs or Report) in a meeting

    Args:
        folder_path: Path to folder (e.g., TSGR1_84/Docs)
        meeting_name: Meeting name (e.g., TSGR1_84)
        folder_type: "Docs" or "Report"
    """
    if not folder_path.exists():
        return

    print(f"\n   📂 Processing: {folder_type}/")
    sys.stdout.flush()

    # Scan files (including .docm - macro-enabled Word documents)
    doc_files = list(folder_path.rglob("*.doc"))
    docx_files = list(folder_path.rglob("*.docx"))
    docm_files = list(folder_path.rglob("*.docm"))
    file_count = len(doc_files) + len(docx_files) + len(docm_files)

    if file_count == 0:
        print(f"      (empty)")
        return

    print(f"      Total: {file_count} ({len(doc_files)} DOC + {len(docx_files)} DOCX + {len(docm_files)} DOCM)")
    sys.stdout.flush()

    processed = 0
    copied = 0
    converted = 0
    skipped = 0

    # Process DOCX files (copy)
    for file_path in docx_files:
        stats['total_files'] += 1

        rel_path = file_path.relative_to(folder_path)
        output_path = DATA_TRANSFORMED / meeting_name / folder_type / rel_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / file_path.name

        if output_file.exists() and output_file.stat().st_size > 0:
            stats['docx_copied'] += 1
            stats['skipped_already_converted'] += 1
            copied += 1
            skipped += 1
            processed += 1
            continue

        try:
            shutil.copy2(file_path, output_file)
            stats['docx_copied'] += 1
            copied += 1
        except Exception as e:
            stats['errors'].append({
                'file': str(file_path),
                'error': f'Copy failed: {e}'
            })

        processed += 1

    # Process DOCM files (copy - macro-enabled Word, XML-based like DOCX)
    for file_path in docm_files:
        stats['total_files'] += 1

        rel_path = file_path.relative_to(folder_path)
        output_path = DATA_TRANSFORMED / meeting_name / folder_type / rel_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / file_path.name

        if output_file.exists() and output_file.stat().st_size > 0:
            stats['docx_copied'] += 1
            stats['skipped_already_converted'] += 1
            copied += 1
            skipped += 1
            processed += 1
            continue

        try:
            shutil.copy2(file_path, output_file)
            stats['docx_copied'] += 1
            copied += 1
        except Exception as e:
            stats['errors'].append({
                'file': str(file_path),
                'error': f'Copy failed: {e}'
            })

        processed += 1

    # Process DOC files (convert)
    for file_path in doc_files:
        stats['total_files'] += 1

        rel_path = file_path.relative_to(folder_path)
        output_path = DATA_TRANSFORMED / meeting_name / folder_type / rel_path.parent

        if convert_doc_to_docx_robust(file_path, output_path):
            stats['doc_converted'] += 1
            converted += 1
        else:
            pass

        processed += 1

        if processed % 100 == 0:
            print(f"      Progress: {processed}/{file_count} ({copied} copied, {converted} converted, {skipped} skipped)")
            sys.stdout.flush()

    print(f"      ✅ {folder_type}: {processed} files ({copied} copied, {converted} converted, {skipped} skipped)")
    sys.stdout.flush()


def process_meeting(meeting_path: Path):
    """Process both Docs and Report folders in a meeting"""
    meeting_name = meeting_path.name

    print(f"\n{'='*80}")
    print(f"📂 Processing: {meeting_name}")
    print(f"{'='*80}")
    sys.stdout.flush()

    # Process Docs folder
    docs_path = meeting_path / "Docs"
    process_folder(docs_path, meeting_name, "Docs")

    # Process Report folder (NEW - was missing!)
    report_path = meeting_path / "Report"
    process_folder(report_path, meeting_name, "Report")


def main():
    print("=" * 80)
    print("Phase-1 Step-6-1: Transform ALL Meetings (Docs + Report) - COMPLETE")
    print("=" * 80)
    print(f"Target: {len(TARGET_MEETINGS)} meetings (ALL)")
    print(f"Folders: Docs + Report (Report was missing before!)")
    print(f"Mode: Sequential with robust timeout")
    print(f"Resume: File-level (skip already converted)")
    print("=" * 80)
    sys.stdout.flush()

    # Check LibreOffice
    if not check_libreoffice():
        print("\n❌ LibreOffice required")
        return 1

    # Cleanup
    print("\n🧹 Cleaning up any stuck LibreOffice processes...")
    kill_all_soffice()
    sys.stdout.flush()

    DATA_TRANSFORMED.mkdir(parents=True, exist_ok=True)

    # Get meeting folders
    meeting_folders = sorted([
        DATA_EXTRACTED / meeting_name
        for meeting_name in TARGET_MEETINGS
        if (DATA_EXTRACTED / meeting_name).exists()
    ])

    print(f"\n📊 Found {len(meeting_folders)} meetings")
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"⏱️  Estimated: 10-15 minutes (most files already converted)")
    sys.stdout.flush()

    completed = 0
    total = len(meeting_folders)

    for meeting_path in meeting_folders:
        try:
            process_meeting(meeting_path)
            completed += 1

            if completed % 10 == 0:
                print(f"\n{'='*80}")
                print(f"✓ Progress: {completed}/{total} meetings ({completed/total*100:.1f}%)")
                print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*80}\n")
                sys.stdout.flush()

        except Exception as e:
            print(f"\n❌ Error processing {meeting_path.name}: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()

    # Save statistics
    stats['end_time'] = datetime.now().isoformat()
    stats['duration_seconds'] = (
        datetime.fromisoformat(stats['end_time']) -
        datetime.fromisoformat(stats['start_time'])
    ).total_seconds()

    stats_file = LOG_DIR / 'transform_complete_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("📊 TRANSFORMATION SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {stats['total_files']}")
    print(f"  DOCX copied: {stats['docx_copied']}")
    print(f"  DOC converted: {stats['doc_converted']}")
    print(f"  Skipped (already done): {stats['skipped_already_converted']}")
    print(f"  Errors: {len(stats['errors'])}")
    print(f"  Conversion errors: {len(stats['conversion_errors'])}")
    print(f"  ⚠️  Timeout files: {len(stats['timeout_files'])}")
    print(f"\nDuration: {stats['duration_seconds']:.1f}s ({stats['duration_seconds']/60:.1f}min)")
    print(f"⏰ Completed: {datetime.now().strftime('%H:%M:%S')}")
    print(f"\n💾 Stats: {stats_file}")
    print(f"📁 Output: {DATA_TRANSFORMED}")

    if stats['timeout_files']:
        print(f"\n⚠️  TIMEOUT FILES ({len(stats['timeout_files'])}):")
        for tf in stats['timeout_files'][:10]:
            print(f"   - {Path(tf).name}")
        if len(stats['timeout_files']) > 10:
            print(f"   ... +{len(stats['timeout_files'])-10} more")

    print("=" * 80)
    sys.stdout.flush()

    return 0 if len(stats['errors']) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
