#!/usr/bin/env python3
"""
RAN1 Meeting Downloader with aria2c

aria2c_input.txt를 사용하여 누락된 파일 다운로드

Usage:
    python3 scripts/ran1-meetings/download_with_aria2c.py

Prerequisites:
    1. aria2c must be installed: sudo apt install -y aria2
    2. aria2c_input.txt must exist (run generate_download_list.py first)
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime


def main():
    ARIA2C_INPUT = "logs/ran1-meetings/aria2c_input.txt"
    DOWNLOAD_LOG = "logs/ran1-meetings/aria2c_download.log"

    print("="*80)
    print("RAN1 Meeting Downloader with aria2c")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Check if aria2c is installed
    try:
        result = subprocess.run(['which', 'aria2c'],
                              capture_output=True, text=True, check=True)
        aria2c_path = result.stdout.strip()
        print(f"\naria2c found: {aria2c_path}")
    except subprocess.CalledProcessError:
        print("\nERROR: aria2c not found!")
        print("\nPlease install aria2c first:")
        print("  sudo apt install -y aria2")
        return 1

    # Check if aria2c_input.txt exists
    if not Path(ARIA2C_INPUT).exists():
        print(f"\nERROR: {ARIA2C_INPUT} not found!")
        print("\nPlease generate download list first:")
        print("  python3 scripts/ran1-meetings/generate_download_list.py")
        return 1

    # Count files to download
    with open(ARIA2C_INPUT, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    url_count = sum(1 for line in lines if line.startswith('http'))

    if url_count == 0:
        print(f"\nNo files to download!")
        print(f"All files are already up to date.")
        return 0

    print(f"\nFiles to download: {url_count}")
    print(f"Input file: {ARIA2C_INPUT}")
    print(f"Log file: {DOWNLOAD_LOG}")
    print("\n" + "="*80)
    print("Starting aria2c download...")
    print("="*80 + "\n")

    # Build aria2c command
    cmd = [
        "aria2c",
        f"--input-file={ARIA2C_INPUT}",
        "--max-connection-per-server=16",
        "--split=5",
        "--max-concurrent-downloads=20",
        "--min-split-size=1M",
        "--continue=true",
        "--auto-file-renaming=false",
        "--allow-overwrite=false",
        "--max-tries=5",
        "--retry-wait=3",
        "--timeout=60",
        "--connect-timeout=30",
        "--console-log-level=notice",
        "--summary-interval=60",
        f"--log={DOWNLOAD_LOG}",
        "--log-level=info"
    ]

    # Execute aria2c
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*80)
        print("Download completed successfully!")
        print("="*80)
        print("\nNext step - Verify completion:")
        print("  python3 scripts/ran1-meetings/verify_status.py")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "="*80)
        print(f"ERROR: aria2c failed with exit code {e.returncode}")
        print("="*80)
        print(f"\nCheck log file for details: {DOWNLOAD_LOG}")
        return 1
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        print("You can resume by running this script again")
        print("aria2c will continue from where it left off")
        return 1


if __name__ == "__main__":
    exit(main())
