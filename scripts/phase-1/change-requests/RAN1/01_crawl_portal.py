#!/usr/bin/env python3
"""
3GPP Portal Change Request 크롤러

5개 Release (15-19)의 NR 38.211-215 Change Request 정보를 크롤링하여 CSV로 저장

Usage:
    python3 scripts/phase-1/change-requests/01_crawl_portal.py
"""

import csv
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlencode


# Release별 Work Item 매핑
RELEASES = {
    "Rel-15": {
        "release_code": "190",
        "workitem": "750167",
        "specs": ["38.211", "38.212", "38.213", "38.214", "38.215"]
    },
    "Rel-16": {
        "release_code": "191",
        "workitem": "800185",
        "specs": ["38.211", "38.212", "38.213", "38.214", "38.215"]
    },
    "Rel-17": {
        "release_code": "192",
        "workitem": "860140",
        "specs": ["38.211", "38.212", "38.213", "38.214", "38.215"]
    },
    "Rel-18": {
        "release_code": "193",
        "workitem": "940196",
        "specs": ["38.211", "38.212", "38.213", "38.214", "38.215"]
    },
    "Rel-19": {
        "release_code": "194",
        "workitem": "1021093",
        "specs": ["38.211", "38.212", "38.213", "38.214", "38.215"]
    }
}

BASE_URL = "https://portal.3gpp.org/ChangeRequests.aspx"

# HTTP Headers (User-Agent 필수 - 403 에러 방지)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def build_url(release_code, workitem, pageindex=0):
    """CR Portal URL 생성 (workitem 기반)"""
    params = {
        "q": "1",
        "specnumber": "38",  # 38.21x 필터링
        "release": release_code,
        "wgstatus": "",
        "tsgstatus": "2",  # approved
        "meeting": "",
        "workitem": workitem,
        "pageindex": str(pageindex)
    }
    return f"{BASE_URL}?{urlencode(params)}"


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
        import re
        match = re.search(r"window\.location\.href='(https://www\.3gpp\.org/ftp/[^']+)'", response.text)
        if match:
            return match.group(1)

    except Exception as e:
        print(f"      Warning: Failed to extract FTP URL from {portal_url}: {e}")

    return ''


def parse_cr_table(html_content):
    """HTML에서 CR 테이블 파싱"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # CR 데이터 테이블 찾기 (rgRow/rgAltRow가 있는 rgMasterTable)
    tables = soup.find_all('table', {'class': 'rgMasterTable'})

    data_table = None
    for table in tables:
        rows = table.find_all('tr', {'class': ['rgRow', 'rgAltRow']})
        if len(rows) > 0:
            data_table = table
            break

    if not data_table:
        return []

    rows = data_table.find_all('tr', {'class': ['rgRow', 'rgAltRow']})

    cr_list = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 17:
            continue

        # Cell 0-1: 빈칸 (아이콘/체크박스)
        # Cell 2부터 실제 데이터 시작

        # WG TDoc과 다운로드 URL 추출
        wg_tdoc_cell = cells[9]
        wg_tdoc_link = wg_tdoc_cell.find('a')
        wg_tdoc = wg_tdoc_cell.get_text(strip=True)
        wg_tdoc_url = wg_tdoc_link['href'] if wg_tdoc_link and wg_tdoc_link.has_attr('href') else ''

        # TSG TDoc과 다운로드 URL 추출
        tsg_tdoc_cell = cells[13]
        tsg_tdoc_link = tsg_tdoc_cell.find('a')
        tsg_tdoc = tsg_tdoc_cell.get_text(strip=True)
        tsg_tdoc_url = tsg_tdoc_link['href'] if tsg_tdoc_link and tsg_tdoc_link.has_attr('href') else ''

        # TSG FTP URL 추출 (Portal URL에서)
        tsg_ftp_url = ''
        if tsg_tdoc_url:
            tsg_ftp_url = extract_ftp_url_from_portal(tsg_tdoc_url)
            time.sleep(0.5)  # Rate limiting

        cr_data = {
            'spec_number': cells[2].get_text(strip=True),
            'cr_number': cells[3].get_text(strip=True),
            'revision': cells[4].get_text(strip=True),
            'cr_category': cells[5].get_text(strip=True),
            'impacted_version': cells[6].get_text(strip=True),
            'target_release': cells[7].get_text(strip=True),
            'title': cells[8].get_text(strip=True),
            'wg_tdoc': wg_tdoc,
            'wg_tdoc_url': wg_tdoc_url,
            'wg_status': cells[10].get_text(strip=True),
            'wg_meeting': cells[11].get_text(strip=True),
            'wg_source': cells[12].get_text(strip=True),
            'tsg_tdoc': tsg_tdoc,
            'tsg_tdoc_url': tsg_tdoc_url,
            'tsg_ftp_url': tsg_ftp_url,
            'tsg_status': cells[14].get_text(strip=True),
            'tsg_meeting': cells[15].get_text(strip=True),
            'tsg_source': cells[16].get_text(strip=True),
            'new_version': cells[17].get_text(strip=True),
            'work_items': cells[18].get_text(strip=True) if len(cells) > 18 else '',
            'remarks': cells[19].get_text(strip=True) if len(cells) > 19 else ''
        }
        cr_list.append(cr_data)

    return cr_list


def get_total_pages(html_content):
    """총 페이지 수 확인"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # 페이지 정보 찾기 (예: "214 items in 2 pages")
    pager_info = soup.find('div', {'class': 'rgWrap rgInfoPart'})
    if pager_info:
        text = pager_info.get_text()
        if 'pages' in text:
            # "214 items in 2 pages" -> 2 추출
            pages = text.split('in')[1].split('pages')[0].strip()
            return int(pages)

    return 1


def crawl_release(release_name, release_code, workitem):
    """특정 Release의 모든 CR 크롤링 (workitem 기반)"""
    print(f"  Crawling {release_name} (workitem: {workitem})...")

    all_crs = []

    # 첫 페이지로 총 페이지 수 확인
    url = build_url(release_code, workitem, pageindex=0)
    print(f"    URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        total_pages = get_total_pages(response.text)
        print(f"    Total pages: {total_pages}")

        # 각 페이지 크롤링
        for page in range(total_pages):
            if page > 0:
                url = build_url(release_code, workitem, pageindex=page)
                response = requests.get(url, headers=HEADERS, timeout=30)
                response.raise_for_status()

            crs = parse_cr_table(response.text)
            all_crs.extend(crs)
            print(f"    Page {page + 1}/{total_pages}: {len(crs)} CRs")

            # Rate limiting
            time.sleep(1)

        print(f"    ✓ Total CRs for {release_name}: {len(all_crs)}")
        return all_crs

    except Exception as e:
        print(f"    ✗ Error crawling {release_name}: {e}")
        return []




def save_to_csv(cr_list, output_path):
    """CR 리스트를 CSV로 저장"""
    if not cr_list:
        print(f"  ⚠ No data to save")
        return

    fieldnames = [
        'spec_number', 'cr_number', 'revision', 'cr_category',
        'impacted_version', 'target_release', 'title',
        'wg_tdoc', 'wg_tdoc_url', 'wg_status', 'wg_meeting', 'wg_source',
        'tsg_tdoc', 'tsg_tdoc_url', 'tsg_ftp_url', 'tsg_status', 'tsg_meeting', 'tsg_source',
        'new_version', 'work_items', 'remarks'
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cr_list)

    print(f"  ✓ Saved {len(cr_list)} CRs to {output_path}")


def main():
    print("="*80)
    print("3GPP RAN1 NR Change Request Portal Crawler")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: 38.21x specs (workitem-based filtering)")
    print("="*80)

    for release_name, release_info in RELEASES.items():
        print(f"\n{'='*80}")
        print(f"Crawling {release_name}")
        print(f"{'='*80}")

        # Crawl
        cr_list = crawl_release(
            release_name,
            release_info['release_code'],
            release_info['workitem']
        )

        # 38.211-215만 필터링
        filtered_crs = [
            cr for cr in cr_list
            if cr['spec_number'] in ['38.211', '38.212', '38.213', '38.214', '38.215']
        ]

        # Save
        output_path = Path(f"data/data_raw/change-requests/RAN1/{release_name}/metadata/cr_list.csv")
        save_to_csv(filtered_crs, output_path)

        print(f"\n✓ {release_name} complete: {len(filtered_crs)} CRs (filtered from {len(cr_list)} total)")
        time.sleep(5)  # Release 간 대기

    print("\n" + "="*80)
    print("All releases crawled successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
