#!/usr/bin/env python3
"""
Phase-1 Step-6: Transform Specs DOC to DOCX

Simple script to convert 1 DOC file (38201-j00.doc) to DOCX
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from datetime import datetime
import json
import time

# Configuration
DATA_EXTRACTED = Path("/home/sihyeon/workspace/spec-trace/data/data_extracted/specs/RAN1")
DATA_TRANSFORMED = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/specs/RAN1")
LOG_DIR = Path("/home/sihyeon/workspace/spec-trace/logs/phase-1/transform/RAN1/specs")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Statistics
stats = {
    'start_time': datetime.now().isoformat(),
    'total_files': 0,
    'docx_copied': 0,
    'doc_converted': 0,
    'errors': []
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


def convert_doc_to_docx(doc_path: Path, output_dir: Path) -> bool:
    """Convert DOC to DOCX with timeout handling"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if already converted
        expected_output = output_dir / (doc_path.stem + '.docx')
        if expected_output.exists() and expected_output.stat().st_size > 0:
            print(f"  ⏭️  Already converted: {expected_output.name}")
            return True

        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'docx',
            '--outdir', str(output_dir),
            str(doc_path)
        ]

        print(f"  🔄 Converting: {doc_path.name} → {expected_output.name}")

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
                if expected_output.exists():
                    size_kb = expected_output.stat().st_size / 1024
                    print(f"  ✅ Success: {expected_output.name} ({size_kb:.1f} KB)")
                    return True
                else:
                    error_msg = f"Output file not created: {expected_output}"
                    print(f"  ❌ {error_msg}")
                    stats['errors'].append({'file': str(doc_path), 'error': error_msg})
                    return False
            else:
                error_msg = stderr.strip() if stderr else "Unknown error"
                print(f"  ❌ Conversion failed: {error_msg}")
                stats['errors'].append({'file': str(doc_path), 'error': error_msg})
                return False

        except subprocess.TimeoutExpired:
            # Kill process group
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass
            process.kill()
            process.wait()

            error_msg = "Timeout (60s)"
            print(f"  ⏱️  {error_msg}: {doc_path.name}")
            stats['errors'].append({'file': str(doc_path), 'error': error_msg})
            return False

    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"  ❌ {error_msg}")
        stats['errors'].append({'file': str(doc_path), 'error': error_msg})
        return False


def main():
    print("="*70)
    print("Phase-1 Step-6: Transform Specs DOC to DOCX")
    print("="*70)
    print()

    # Check LibreOffice
    if not check_libreoffice():
        print("❌ LibreOffice is required. Install with: sudo apt-get install libreoffice")
        sys.exit(1)

    print()
    print(f"📂 Input:  {DATA_EXTRACTED}")
    print(f"📂 Output: {DATA_TRANSFORMED}")
    print()

    # Process all spec folders
    for spec_folder in sorted(DATA_EXTRACTED.iterdir()):
        if not spec_folder.is_dir() or spec_folder.name == 'metadata':
            continue

        print(f"\n📋 Processing: {spec_folder.name}")
        output_dir = DATA_TRANSFORMED / spec_folder.name

        # Process all files in spec folder
        for file_path in sorted(spec_folder.iterdir()):
            if not file_path.is_file():
                continue

            stats['total_files'] += 1

            if file_path.suffix.lower() == '.docx':
                # Copy DOCX as-is
                output_file = output_dir / file_path.name
                output_dir.mkdir(parents=True, exist_ok=True)

                if not output_file.exists():
                    import shutil
                    shutil.copy2(file_path, output_file)
                    size_kb = output_file.stat().st_size / 1024
                    print(f"  📄 Copied DOCX: {file_path.name} ({size_kb:.1f} KB)")
                    stats['docx_copied'] += 1
                else:
                    print(f"  ⏭️  Already exists: {file_path.name}")
                    stats['docx_copied'] += 1

            elif file_path.suffix.lower() == '.doc':
                # Convert DOC to DOCX
                if convert_doc_to_docx(file_path, output_dir):
                    stats['doc_converted'] += 1

            else:
                print(f"  ⏭️  Skipped (not DOC/DOCX): {file_path.name}")

    # Summary
    print()
    print("="*70)
    print("📊 Transform Summary")
    print("="*70)
    print(f"Total files:     {stats['total_files']}")
    print(f"DOCX copied:     {stats['docx_copied']}")
    print(f"DOC converted:   {stats['doc_converted']}")
    print(f"Errors:          {len(stats['errors'])}")
    print()

    if stats['errors']:
        print("❌ Errors:")
        for error in stats['errors']:
            print(f"  - {error['file']}: {error['error']}")
        print()

    # Save stats
    stats['end_time'] = datetime.now().isoformat()
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
        for doc_file in DATA_TRANSFORMED.rglob('*.doc'):
            print(f"  - {doc_file}")

    print()
    print("="*70)
    print("✅ Specs Transform Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
