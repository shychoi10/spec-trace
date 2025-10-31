#!/usr/bin/env python3
"""
RAN1 Meeting Download List Generator

전체 미팅의 누락 파일 수집 및 aria2c 입력 파일 생성

Usage:
    python3 scripts/ran1-meetings/generate_download_list.py

Output:
    logs/ran1-meetings/aria2c_input.txt
"""

import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime
import time


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
    """FTP 디렉토리의 링크 목록 가져오기"""
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
        print(f"    Error fetching {url}: {e}")
        return []


def is_likely_file(item_name):
    """파일인지 확인 (확장자 기반)"""
    file_extensions = [
        '.zip', '.doc', '.docx', '.pdf', '.txt', '.xls', '.xlsx',
        '.ppt', '.pptx', '.htm', '.html', '.xml', '.csv', '.gz',
        '.tar', '.rar', '.7z', '.msg', '.eml', '.xlsm'
    ]
    return any(item_name.lower().endswith(ext) for ext in file_extensions)


def get_all_file_urls_recursive(url, depth=0, max_depth=10):
    """재귀적으로 모든 파일 URL 수집"""
    if depth > max_depth:
        return []
    items = fetch_directory_listing(url)
    file_urls = []
    for item in items:
        is_folder = item.endswith('/')
        if is_folder:
            subfolder_url = urljoin(url, item)
            file_urls.extend(get_all_file_urls_recursive(subfolder_url, depth + 1, max_depth))
        else:
            if is_likely_file(item):
                file_url = urljoin(url, item)
                file_urls.append(file_url)
            else:
                test_url = urljoin(url, item + '/')
                test_items = fetch_directory_listing(test_url)
                if test_items:
                    file_urls.extend(get_all_file_urls_recursive(test_url, depth + 1, max_depth))
                else:
                    file_url = urljoin(url, item)
                    file_urls.append(file_url)
    return file_urls


def load_target_meetings():
    """CLAUDE.md에서 타겟 미팅 목록 로드"""
    claude_md = "data/data_raw/meetings/RAN1/CLAUDE.md"
    meetings = []
    with open(claude_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    in_list = False
    for line in lines:
        if "Download Target List" in line:
            in_list = True
            continue
        if in_list:
            if line.strip() and line.strip()[0].isdigit():
                parts = line.strip().split('. ')
                if len(parts) >= 2:
                    meeting = parts[1].strip()
                    meetings.append(meeting)
            elif line.strip().startswith("##"):
                break
    return meetings


def extract_relative_path_from_url(url):
    """URL에서 상대 경로 추출"""
    parts = url.split('/WG1_RL1/')
    if len(parts) == 2:
        return parts[1]
    return None


def get_local_files(local_dir):
    """로컬 파일 목록 수집"""
    local_path = Path(local_dir)
    if not local_path.exists():
        return set()
    local_files = set()
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(local_path)
            local_files.add(str(rel_path))
    return local_files


def main():
    BASE_URL = "https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/"
    LOCAL_DIR = "data/data_raw/meetings/RAN1"
    ARIA2C_INPUT_FILE = "logs/ran1-meetings/aria2c_input.txt"

    start_time = time.time()

    print("="*80)
    print("RAN1 Meeting Download List Generator")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # [1/4] Load target meetings
    print("\n[1/4] Loading target meetings from CLAUDE.md...")
    meetings = load_target_meetings()
    print(f"Total meetings: {len(meetings)}")

    # [2/4] Scan local files
    print("\n[2/4] Scanning local files...")
    local_files = get_local_files(LOCAL_DIR)
    print(f"Total local files: {len(local_files)}")

    # [3/4] Collect FTP URLs and find missing files
    print("\n[3/4] Collecting FTP URLs and finding missing files...")
    all_missing_urls = []
    meeting_stats = {}

    for i, meeting in enumerate(meetings, 1):
        print(f"\n[{i}/{len(meetings)}] {meeting}")
        meeting_start = time.time()
        meeting_missing = []

        # Docs folder
        docs_url = urljoin(BASE_URL, f"{meeting}/Docs/")
        print(f"  Scanning Docs...")
        docs_urls = get_all_file_urls_recursive(docs_url)
        print(f"  Docs: {len(docs_urls)} files on FTP")

        for url in docs_urls:
            rel_path = extract_relative_path_from_url(url)
            if rel_path and rel_path not in local_files:
                meeting_missing.append(url)

        # Report folder
        report_url = urljoin(BASE_URL, f"{meeting}/Report/")
        print(f"  Scanning Report...")
        report_urls = get_all_file_urls_recursive(report_url)
        print(f"  Report: {len(report_urls)} files on FTP")

        for url in report_urls:
            rel_path = extract_relative_path_from_url(url)
            if rel_path and rel_path not in local_files:
                meeting_missing.append(url)

        meeting_elapsed = time.time() - meeting_start
        missing_count = len(meeting_missing)
        print(f"  Missing: {missing_count} files (took {meeting_elapsed:.1f}s)")

        all_missing_urls.extend(meeting_missing)
        meeting_stats[meeting] = {
            'ftp_total': len(docs_urls) + len(report_urls),
            'missing': missing_count
        }

    # [4/4] Generate aria2c input file
    print("\n[4/4] Generating aria2c input file...")
    Path(ARIA2C_INPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

    with open(ARIA2C_INPUT_FILE, 'w', encoding='utf-8') as f:
        for url in all_missing_urls:
            rel_path = extract_relative_path_from_url(url)
            if rel_path:
                parts = rel_path.split('/')
                if len(parts) >= 3:
                    meeting = parts[0]
                    folder = parts[1]
                    filename = '/'.join(parts[2:])
                    target_dir = f"/home/sihyeon/workspace/spec-trace/data/data_raw/meetings/RAN1/{meeting}/{folder}"
                    if '/' in filename:
                        sub_dirs = '/'.join(filename.split('/')[:-1])
                        target_dir = f"{target_dir}/{sub_dirs}"
                        filename = filename.split('/')[-1]
                    f.write(f"{url}\n")
                    f.write(f"  dir={target_dir}\n")
                    f.write(f"  out={filename}\n")

    elapsed = time.time() - start_time

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total meetings: {len(meetings)}")
    print(f"Total local files: {len(local_files)}")
    print(f"Total missing files: {len(all_missing_urls)}")
    print(f"aria2c input file: {ARIA2C_INPUT_FILE}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print("="*80)

    if len(all_missing_urls) == 0:
        print("\nAll files are already downloaded!")
    else:
        print(f"\nNext step:")
        print(f"  python3 scripts/ran1-meetings/download_with_aria2c.py")


if __name__ == "__main__":
    main()
