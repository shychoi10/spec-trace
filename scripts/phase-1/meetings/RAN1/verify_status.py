#!/usr/bin/env python3
"""
3GPP RAN1 다운로드 상태 정밀 체크
- FTP 서버와 로컬 파일 상세 비교
- 미팅별 Docs/Report 파일 개수 확인
- 누락/부분 다운로드 미팅 식별
"""

import os
import re
import urllib.request
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime


class FTPDirectoryParser(HTMLParser):
    """FTP 디렉토리 리스팅 HTML 파서"""
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)


def fetch_directory_listing(url):
    """FTP 디렉토리의 파일 목록 가져오기"""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            html = response.read().decode('utf-8')

        parser = FTPDirectoryParser()
        parser.feed(html)

        base_url = url.rstrip('/')
        items = []

        for link in parser.links:
            if link.startswith(base_url + '/'):
                item = link[len(base_url)+1:]
                if '?' not in item and item:
                    items.append(item)

        return items
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return []


def is_likely_file(item_name):
    """파일인지 확인 (확장자 기반)"""
    file_extensions = [
        '.zip', '.doc', '.docx', '.pdf', '.txt', '.xls', '.xlsx',
        '.ppt', '.pptx', '.htm', '.html', '.xml', '.csv', '.gz',
        '.tar', '.rar', '.7z', '.msg', '.eml', '.xlsm'
    ]
    return any(item_name.lower().endswith(ext) for ext in file_extensions)


def count_files_in_ftp_folder(folder_url, depth=0, max_depth=3):
    """FTP 폴더의 파일 개수 재귀적으로 세기"""
    if depth > max_depth:
        return 0

    items = fetch_directory_listing(folder_url)
    file_count = 0

    for item in items:
        is_folder = item.endswith('/')

        if is_folder:
            subfolder_name = item.rstrip('/')
            subfolder_url = urljoin(folder_url, item)
            file_count += count_files_in_ftp_folder(subfolder_url, depth + 1, max_depth)
        else:
            if is_likely_file(item):
                file_count += 1
            else:
                # 확장자 없으면 폴더 가능성
                test_url = urljoin(folder_url, item + '/')
                test_items = fetch_directory_listing(test_url)
                if test_items:
                    file_count += count_files_in_ftp_folder(test_url, depth + 1, max_depth)
                else:
                    file_count += 1

    return file_count


def get_ftp_meeting_info(base_url, meeting_name):
    """FTP 서버에서 특정 미팅의 Docs/Report 파일 개수 가져오기"""
    meeting_url = urljoin(base_url, f"{meeting_name}/")

    info = {
        'meeting': meeting_name,
        'docs_count': 0,
        'report_count': 0,
        'docs_exists': False,
        'report_exists': False,
        'error': None
    }

    # Docs 폴더 체크
    docs_url = urljoin(meeting_url, "Docs/")
    try:
        print(f"  Checking Docs...")
        info['docs_count'] = count_files_in_ftp_folder(docs_url)
        info['docs_exists'] = True
    except Exception as e:
        info['error'] = f"Docs error: {e}"

    # Report 폴더 체크
    report_url = urljoin(meeting_url, "Report/")
    try:
        print(f"  Checking Report...")
        info['report_count'] = count_files_in_ftp_folder(report_url)
        info['report_exists'] = True
    except Exception as e:
        if not info['error']:
            info['error'] = f"Report error: {e}"

    return info


def get_local_meeting_info(local_dir, meeting_name):
    """로컬에서 특정 미팅의 Docs/Report 파일 개수 가져오기"""
    meeting_path = Path(local_dir) / meeting_name

    info = {
        'meeting': meeting_name,
        'docs_count': 0,
        'report_count': 0,
        'docs_exists': False,
        'report_exists': False,
        'has_zero_byte_files': False
    }

    if not meeting_path.exists():
        return info

    # Docs 폴더
    docs_path = meeting_path / "Docs"
    if docs_path.exists():
        info['docs_exists'] = True
        files = list(docs_path.rglob("*"))
        info['docs_count'] = len([f for f in files if f.is_file()])

        # 0 바이트 파일 체크
        zero_byte_files = [f for f in files if f.is_file() and f.stat().st_size == 0]
        if zero_byte_files:
            info['has_zero_byte_files'] = True

    # Report 폴더
    report_path = meeting_path / "Report"
    if report_path.exists():
        info['report_exists'] = True
        files = list(report_path.rglob("*"))
        info['report_count'] = len([f for f in files if f.is_file()])

        # 0 바이트 파일 체크
        zero_byte_files = [f for f in files if f.is_file() and f.stat().st_size == 0]
        if zero_byte_files:
            info['has_zero_byte_files'] = True

    return info


def is_target_meeting(meeting_name):
    """타겟 미팅인지 확인 (TSGR1_84 ~ TSGR1_122)"""
    match = re.match(r'TSGR1_(\d+)', meeting_name)
    if match:
        meeting_num = int(match.group(1))
        return 84 <= meeting_num <= 122
    return False


def main():
    BASE_URL = "https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/"
    LOCAL_DIR = "data/data_raw/meetings/RAN1"
    LOG_FILE = "logs/phase-1/status_detailed.log"

    # 로그 파일 초기화
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("3GPP RAN1 Download Status Check")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"FTP: {BASE_URL}")
    print(f"Local: {LOCAL_DIR}")
    print("="*80)

    # FTP에서 미팅 목록 가져오기
    print("\n[1/3] Fetching meeting list from FTP...")
    items = fetch_directory_listing(BASE_URL)
    meetings = [item.rstrip('/') for item in items if item.startswith('TSGR1_')]
    target_meetings = sorted([m for m in meetings if is_target_meeting(m)])

    print(f"Total target meetings: {len(target_meetings)}")

    # 각 미팅별 상세 체크
    print("\n[2/3] Checking each meeting...")

    results = []

    for i, meeting in enumerate(target_meetings, 1):
        print(f"\n[{i}/{len(target_meetings)}] {meeting}")

        # FTP 정보
        ftp_info = get_ftp_meeting_info(BASE_URL, meeting)

        # 로컬 정보
        local_info = get_local_meeting_info(LOCAL_DIR, meeting)

        # 결과 저장
        result = {
            'meeting': meeting,
            'ftp_docs': ftp_info['docs_count'],
            'ftp_report': ftp_info['report_count'],
            'local_docs': local_info['docs_count'],
            'local_report': local_info['report_count'],
            'local_exists': local_info['docs_exists'] or local_info['report_exists'],
            'is_complete': False,
            'is_partial': False,
            'is_missing': False,
            'has_zero_byte': local_info['has_zero_byte_files']
        }

        # 상태 판단
        if not result['local_exists']:
            result['is_missing'] = True
            status = "MISSING"
        elif (result['local_docs'] >= result['ftp_docs'] * 0.9 and
              result['local_report'] >= result['ftp_report'] * 0.9):
            result['is_complete'] = True
            status = "COMPLETE"
        else:
            result['is_partial'] = True
            status = "PARTIAL"

        print(f"  FTP: Docs={ftp_info['docs_count']}, Report={ftp_info['report_count']}")
        print(f"  Local: Docs={local_info['docs_count']}, Report={local_info['report_count']}")
        print(f"  Status: {status}")

        results.append(result)

    # 통계 계산
    print("\n[3/3] Generating report...")

    complete = [r for r in results if r['is_complete']]
    partial = [r for r in results if r['is_partial']]
    missing = [r for r in results if r['is_missing']]

    # 로그 파일 작성
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("3GPP RAN1 Download Status Report\n")
        f.write("="*80 + "\n")
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Target Range: TSGR1_84 ~ TSGR1_122\n")
        f.write(f"Total Meetings: {len(target_meetings)}\n")
        f.write("="*80 + "\n\n")

        # 통계
        f.write(f"SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"Complete: {len(complete)}/{len(target_meetings)} ({len(complete)*100//len(target_meetings)}%)\n")
        f.write(f"Partial:  {len(partial)}/{len(target_meetings)} ({len(partial)*100//len(target_meetings)}%)\n")
        f.write(f"Missing:  {len(missing)}/{len(target_meetings)} ({len(missing)*100//len(target_meetings)}%)\n")
        f.write("\n")

        # 완료된 미팅
        if complete:
            f.write(f"COMPLETE MEETINGS ({len(complete)})\n")
            f.write("-"*80 + "\n")
            for r in complete:
                f.write(f"✓ {r['meeting']:<20} Docs: {r['local_docs']:>5}, Report: {r['local_report']:>3}\n")
            f.write("\n")

        # 부분 다운로드 미팅
        if partial:
            f.write(f"PARTIAL DOWNLOADS ({len(partial)})\n")
            f.write("-"*80 + "\n")
            for r in partial:
                f.write(f"⚠ {r['meeting']:<20} Docs: {r['local_docs']:>5}/{r['ftp_docs']:<5} Report: {r['local_report']:>3}/{r['ftp_report']:<3}\n")
            f.write("\n")

        # 누락된 미팅
        if missing:
            f.write(f"MISSING MEETINGS ({len(missing)})\n")
            f.write("-"*80 + "\n")
            for r in missing:
                f.write(f"✗ {r['meeting']:<20} (FTP: Docs={r['ftp_docs']}, Report={r['ftp_report']})\n")
            f.write("\n")

        # 다운로드 필요 목록
        need_download = partial + missing
        if need_download:
            f.write(f"DOWNLOAD NEEDED ({len(need_download)})\n")
            f.write("-"*80 + "\n")
            for r in need_download:
                f.write(f"{r['meeting']}\n")

    # 콘솔 출력
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Meetings: {len(target_meetings)}")
    print(f"Complete: {len(complete)} ({len(complete)*100//len(target_meetings)}%)")
    print(f"Partial:  {len(partial)} ({len(partial)*100//len(target_meetings)}%)")
    print(f"Missing:  {len(missing)} ({len(missing)*100//len(target_meetings)}%)")
    print(f"\nDownload needed: {len(need_download)} meetings")
    print("="*80)
    print(f"\nDetailed log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
