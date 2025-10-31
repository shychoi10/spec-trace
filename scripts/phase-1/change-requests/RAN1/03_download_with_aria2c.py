#!/usr/bin/env python3
"""
aria2c를 사용한 Change Request TSG TDoc 다운로드

aria2c_input_tsg.txt 파일을 사용하여 TSG TDoc 다운로드

Usage:
    python3 scripts/phase-1/change-requests/RAN1/03_download_with_aria2c.py
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime


def check_aria2c():
    """aria2c 설치 여부 확인"""
    try:
        result = subprocess.run(['which', 'aria2c'],
                              capture_output=True, text=True, check=True)
        aria2c_path = result.stdout.strip()
        print(f"✓ aria2c found: {aria2c_path}")
        return True
    except subprocess.CalledProcessError:
        print("✗ aria2c not found!")
        print("\nPlease install aria2c first:")
        print("  sudo apt install -y aria2")
        return False


def count_files_to_download(input_file):
    """다운로드할 파일 수 카운트"""
    if not Path(input_file).exists():
        return 0

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    return sum(1 for line in lines if line.startswith('http'))


def download_with_aria2c(input_file, log_file, desc):
    """aria2c로 파일 다운로드"""
    print(f"\n{'='*80}")
    print(f"{desc}")
    print(f"{'='*80}")

    if not Path(input_file).exists():
        print(f"✗ Input file not found: {input_file}")
        print("  Run 02_generate_download_list.py first")
        return False

    file_count = count_files_to_download(input_file)

    if file_count == 0:
        print(f"✓ No files to download (already up to date)")
        return True

    print(f"Files to download: {file_count}")
    print(f"Input file: {input_file}")
    print(f"Log file: {log_file}")
    print(f"\n{'='*80}")
    print(f"Starting download...")
    print(f"{'='*80}\n")

    # aria2c 명령 구성
    cmd = [
        "aria2c",
        f"--input-file={input_file}",
        "--max-connection-per-server=16",
        "--split=5",
        "--max-concurrent-downloads=20",
        "--min-split-size=1M",
        "--continue=true",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--max-tries=5",
        "--retry-wait=3",
        "--timeout=60",
        "--connect-timeout=30",
        "--console-log-level=notice",
        "--summary-interval=60",
        f"--log={log_file}",
        "--log-level=info"
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n{'='*80}")
        print(f"✓ {desc} completed successfully!")
        print(f"{'='*80}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n{'='*80}")
        print(f"✗ Download failed with exit code {e.returncode}")
        print(f"{'='*80}")
        print(f"\nCheck log file for details: {log_file}")
        return False

    except KeyboardInterrupt:
        print(f"\n\n⚠ Download interrupted by user")
        print(f"You can resume by running this script again")
        print(f"aria2c will continue from where it left off")
        return False


def main():
    print("="*80)
    print("RAN1 Change Request TSG TDoc Downloader with aria2c")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # aria2c 확인
    if not check_aria2c():
        return 1

    # 입력 파일 경로
    logs_dir = Path("logs/phase-1/change-requests/RAN1")
    tsg_input = logs_dir / "aria2c_input_tsg.txt"
    tsg_log = logs_dir / "aria2c_download_tsg.log"

    # 출력 디렉토리 생성
    for release in ["Rel-15", "Rel-16", "Rel-17", "Rel-18", "Rel-19"]:
        Path(f"data/data_raw/change-requests/RAN1/{release}/TSG").mkdir(parents=True, exist_ok=True)

    # TSG TDoc 다운로드
    success_tsg = download_with_aria2c(
        tsg_input,
        tsg_log,
        "TSG TDoc Download"
    )

    # 결과 요약
    print(f"\n{'='*80}")
    print(f"Download Summary")
    print(f"{'='*80}")
    print(f"TSG TDocs: {'✓ Success' if success_tsg else '✗ Failed'}")
    print(f"{'='*80}")

    if success_tsg:
        print(f"\n✓ All downloads completed successfully!")
        print(f"\nNext step - Verify downloads:")
        print(f"  python3 scripts/phase-1/change-requests/RAN1/04_verify_downloads.py")
        return 0
    else:
        print(f"\n⚠ Download failed. Check log for details:")
        print(f"  {tsg_log}")
        return 1


if __name__ == "__main__":
    exit(main())
