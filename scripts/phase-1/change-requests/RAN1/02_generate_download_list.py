#!/usr/bin/env python3
"""
aria2c 다운로드 리스트 생성기 (TSG only)

cr_list.csv에서 TSG Portal URL을 읽어서 FTP URL을 추출하고 aria2c 입력 파일 생성

Usage:
    python3 scripts/phase-1/change-requests/RAN1/02_generate_download_list.py
"""

import csv
import re
import time
import requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


# Release별 매핑 정보
RELEASES = ["Rel-15", "Rel-16", "Rel-17", "Rel-18", "Rel-19"]

# HTTP Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def extract_ftp_url_from_portal(portal_url):
    """
    Portal URL에서 JavaScript의 FTP URL 추출

    Args:
        portal_url: Portal download page URL

    Returns:
        FTP URL or empty string
    """
    if not portal_url or portal_url == '-':
        return ''

    try:
        response = requests.get(portal_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # JavaScript에서 FTP URL 추출: window.location.href='...'
        match = re.search(r"window\.location\.href='(https://www\.3gpp\.org/ftp/[^']+)'", response.text)
        if match:
            return match.group(1)

    except Exception as e:
        # 에러는 조용히 무시 (로그는 나중에)
        pass

    return ''


def extract_ftp_url_with_retry(tsg_tdoc, tsg_tdoc_url, max_retries=3):
    """
    FTP URL 추출 (재시도 포함)

    Returns:
        dict with tsg_tdoc, tsg_tdoc_url, tsg_ftp_url
    """
    for attempt in range(max_retries):
        ftp_url = extract_ftp_url_from_portal(tsg_tdoc_url)
        if ftp_url:
            return {
                'tsg_tdoc': tsg_tdoc,
                'tsg_tdoc_url': tsg_tdoc_url,
                'tsg_ftp_url': ftp_url
            }
        if attempt < max_retries - 1:
            time.sleep(1)  # 재시도 전 대기

    # 실패한 경우
    return {
        'tsg_tdoc': tsg_tdoc,
        'tsg_tdoc_url': tsg_tdoc_url,
        'tsg_ftp_url': ''
    }


def generate_aria2c_input(release_name, max_workers=30):
    """
    특정 Release의 cr_list.csv를 읽어서 TSG Portal URL에서 FTP URL을 병렬 추출

    Args:
        release_name: Release 이름 (예: "Rel-15")
        max_workers: 병렬 처리 워커 수

    Returns:
        tsg_urls - TSG 다운로드 URL 리스트
    """
    print(f"\n[{release_name}]")

    # cr_list.csv 읽기
    csv_path = Path(f"data/data_raw/change-requests/RAN1/{release_name}/metadata/cr_list.csv")

    if not csv_path.exists():
        print(f"  ✗ {csv_path} not found - run 01_crawl_portal.py first")
        return []

    # TSG TDoc URL 수집 (release 내 중복 제거)
    seen_tdocs = {}  # tsg_tdoc -> tsg_tdoc_url
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            tsg_tdoc = row.get('tsg_tdoc', '').strip()
            tsg_tdoc_url = row.get('tsg_tdoc_url', '').strip()

            if tsg_tdoc and tsg_tdoc != '-' and tsg_tdoc_url:
                # 이미 본 TSG TDoc이면 스킵 (같은 release 내 중복)
                if tsg_tdoc not in seen_tdocs:
                    seen_tdocs[tsg_tdoc] = tsg_tdoc_url

    tsg_tasks = list(seen_tdocs.items())

    if not tsg_tasks:
        print(f"  ✗ No TSG TDocs found")
        return []

    print(f"  TSG TDocs to process: {len(tsg_tasks)}")
    print(f"  Extracting FTP URLs in parallel (workers={max_workers})...")

    # 병렬로 FTP URL 추출
    tsg_results = []
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 모든 작업 제출
        futures = {
            executor.submit(extract_ftp_url_with_retry, tdoc, url): (tdoc, url)
            for tdoc, url in tsg_tasks
        }

        # 완료되는 순서대로 처리
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()

            if result['tsg_ftp_url']:
                tsg_results.append(result)
                success_count += 1
            else:
                fail_count += 1
                print(f"    ⚠ Failed to extract FTP URL: {result['tsg_tdoc']}")

            # 진행 상황 표시 (매 50개마다)
            if i % 50 == 0:
                print(f"    Progress: {i}/{len(tsg_tasks)} ({success_count} success, {fail_count} failed)")

    print(f"  ✓ Extraction complete: {success_count} success, {fail_count} failed")

    # aria2c 입력 형식으로 변환
    tsg_urls = []
    for result in tsg_results:
        tsg_urls.append({
            'url': result['tsg_ftp_url'],
            'filename': f"{result['tsg_tdoc']}.zip",
            'output_dir': f"data/data_raw/change-requests/RAN1/{release_name}/TSG"
        })

    return tsg_urls


def write_aria2c_input_file(urls, output_path):
    """
    aria2c 입력 파일 작성

    Format:
        URL
          dir=/path/to/output/dir
          out=filename.zip
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in urls:
            f.write(f"{item['url']}\n")
            f.write(f"  dir={item['output_dir']}\n")
            f.write(f"  out={item['filename']}\n")

    print(f"  ✓ Saved to {output_path}")


def main():
    print("="*80)
    print("aria2c Download List Generator (TSG only)")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    all_tsg_urls = []

    # Release별 병렬 URL 추출 (5개 프로세스)
    print(f"\nParallel URL extraction for {len(RELEASES)} releases...")

    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(generate_aria2c_input, release, 30): release
                   for release in RELEASES}

        for future in as_completed(futures):
            release = futures[future]
            try:
                tsg_urls = future.result()
                all_tsg_urls.extend(tsg_urls)
                print(f"  ✓ {release} completed ({len(tsg_urls)} URLs)")
            except Exception as e:
                print(f"  ✗ {release} failed: {e}")

    print(f"\n{'='*80}")
    print(f"Total TSG TDocs to download: {len(all_tsg_urls)}")
    print(f"{'='*80}")

    # aria2c 입력 파일 저장
    logs_dir = Path("logs/phase-1/change-requests/RAN1")

    if all_tsg_urls:
        write_aria2c_input_file(
            all_tsg_urls,
            logs_dir / "aria2c_input_tsg.txt"
        )
    else:
        print("\n✗ No TSG URLs to download")
        return 1

    print(f"\n✓ Download list generated successfully!")
    print(f"\nNext step:")
    print(f"  python3 scripts/phase-1/change-requests/RAN1/03_download_with_aria2c.py")

    return 0


if __name__ == "__main__":
    exit(main())
