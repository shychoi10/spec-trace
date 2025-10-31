#!/usr/bin/env python3
"""
3GPP RAN1 NR Physical Layer Specifications Downloader

5개 NR 물리계층 spec(38.211-215)의 최신 버전을 다운로드

Usage:
    python3 scripts/phase-1/specs/RAN1/download_latest_specs.py
"""

import os
import re
import csv
import sys
import zipfile
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup


# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data/data_raw/specs/RAN1"
LOGS_DIR = PROJECT_ROOT / "logs/phase-1/specs/RAN1"
METADATA_FILE = DATA_DIR / "metadata/download_status.csv"
LOG_FILE = LOGS_DIR / "download.log"

# Target specifications
SPECS = {
    "38.211": "Physical channels and modulation",
    "38.212": "Multiplexing and channel coding",
    "38.213": "Physical layer procedures for control",
    "38.214": "Physical layer procedures for data",
    "38.215": "Physical layer measurements"
}

FTP_BASE = "https://www.3gpp.org/ftp/specs/archive/38_series"

# HTTP Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def log(message, level="INFO"):
    """로그 메시지 출력 및 파일 저장"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')


def get_latest_version(spec_num):
    """
    FTP 서버에서 해당 spec의 최신 버전 코드 반환

    Args:
        spec_num: Spec 번호 (예: "38.211")

    Returns:
        최신 버전 코드 (예: "j10") 또는 None
    """
    url = f"{FTP_BASE}/{spec_num}/"
    log(f"Fetching version list from {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        # 파일명 패턴: 38211-XXX.zip
        spec_id = spec_num.replace(".", "")
        pattern = f"{spec_id}-([a-z0-9]{{3}})\\.zip"

        versions = re.findall(pattern, response.text)

        if not versions:
            log(f"No versions found for spec {spec_num}", "ERROR")
            return None

        # 알파벳 정렬 후 마지막 = 최신
        latest = sorted(versions)[-1]
        log(f"Found {len(versions)} versions, latest: {latest}")
        return latest

    except Exception as e:
        log(f"Error fetching version list for {spec_num}: {e}", "ERROR")
        return None


def download_spec(spec_num, version):
    """
    Spec 파일 다운로드

    Args:
        spec_num: Spec 번호 (예: "38.211")
        version: 버전 코드 (예: "j10")

    Returns:
        (success: bool, file_size_kb: int)
    """
    spec_id = spec_num.replace(".", "")
    filename = f"{spec_id}-{version}.zip"
    url = f"{FTP_BASE}/{spec_num}/{filename}"

    output_dir = DATA_DIR / spec_num
    output_path = output_dir / filename

    # 이미 존재하면 스킵
    if output_path.exists():
        file_size = output_path.stat().st_size // 1024
        log(f"✓ {filename} already exists ({file_size} KB)")
        return (True, file_size)

    log(f"Downloading {filename} from {url}")

    try:
        # 다운로드
        response = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

        print()  # New line after progress

        file_size = output_path.stat().st_size

        # 파일 크기 검증
        if file_size == 0:
            log(f"✗ {filename} download failed (0 bytes)", "ERROR")
            output_path.unlink()
            return (False, 0)

        # ZIP 파일 무결성 검증
        try:
            with zipfile.ZipFile(output_path, 'r') as zf:
                if zf.testzip() is not None:
                    log(f"✗ {filename} ZIP integrity check failed", "ERROR")
                    output_path.unlink()
                    return (False, 0)
        except zipfile.BadZipFile:
            log(f"✗ {filename} is not a valid ZIP file", "ERROR")
            output_path.unlink()
            return (False, 0)

        file_size_kb = file_size // 1024
        log(f"✓ {filename} downloaded successfully ({file_size_kb} KB)")
        return (True, file_size_kb)

    except Exception as e:
        log(f"✗ Error downloading {filename}: {e}", "ERROR")
        if output_path.exists():
            output_path.unlink()
        return (False, 0)


def save_metadata(download_results):
    """
    다운로드 결과를 metadata CSV에 저장

    Args:
        download_results: [(spec_num, version, success, file_size_kb), ...]
    """
    log("Saving metadata to download_status.csv")

    with open(METADATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Spec', 'Version', 'Download_Date', 'File_Size_KB', 'Status'])

        for spec_num, version, success, file_size_kb in download_results:
            status = "Downloaded" if success else "Failed"
            download_date = datetime.now().strftime("%Y-%m-%d")
            writer.writerow([spec_num, version or "N/A", download_date, file_size_kb, status])

    log(f"✓ Metadata saved to {METADATA_FILE}")


def print_summary(download_results):
    """다운로드 결과 요약 출력"""
    print("\n" + "="*80)
    print("Download Summary")
    print("="*80)

    total_specs = len(download_results)
    successful = sum(1 for _, _, success, _ in download_results if success)
    failed = total_specs - successful
    total_size_kb = sum(size for _, _, success, size in download_results if success)

    print(f"\nTotal Specs: {total_specs}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total Size: {total_size_kb / 1024:.2f} MB")

    print("\nPer-Spec Results:")
    print("-" * 80)
    print(f"{'Spec':<12} {'Version':<10} {'Size (KB)':<12} {'Status':<15}")
    print("-" * 80)

    for spec_num, version, success, file_size_kb in download_results:
        status = "✓ Downloaded" if success else "✗ Failed"
        version_str = version or "N/A"
        print(f"{spec_num:<12} {version_str:<10} {file_size_kb:<12} {status:<15}")

    print("="*80)

    if failed > 0:
        log(f"\n⚠ {failed} spec(s) failed to download. Check logs for details.", "WARNING")
    else:
        log("\n✓ All specs downloaded successfully!")


def main():
    """메인 실행 함수"""
    print("="*80)
    print("3GPP RAN1 NR Physical Layer Specifications Downloader")
    print("="*80)
    print(f"Target: 5 specs (38.211-215)")
    print(f"Strategy: Auto-detect and download latest version")
    print(f"Output: {DATA_DIR}")
    print("="*80)
    print()

    # 로그 파일 초기화
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Download started at {datetime.now()}\n\n")

    log("Starting download process")

    download_results = []

    for spec_num, title in SPECS.items():
        print(f"\n[{spec_num}] {title}")
        print("-" * 80)

        # 최신 버전 감지
        version = get_latest_version(spec_num)

        if version is None:
            log(f"Failed to detect latest version for {spec_num}", "ERROR")
            download_results.append((spec_num, None, False, 0))
            continue

        # 다운로드
        success, file_size_kb = download_spec(spec_num, version)
        download_results.append((spec_num, version, success, file_size_kb))

    # 메타데이터 저장
    save_metadata(download_results)

    # 결과 요약
    print_summary(download_results)

    log("Download process completed")

    # 실패가 있으면 exit code 1 반환
    failed_count = sum(1 for _, _, success, _ in download_results if not success)
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
