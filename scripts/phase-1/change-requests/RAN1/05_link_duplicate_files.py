#!/usr/bin/env python3
"""
중복 TSG TDoc 파일 하드링크 생성

동일한 TSG TDoc이 여러 Release에 존재하는 경우,
한 곳에만 다운로드되어 있으면 나머지 release 폴더에 하드링크 생성

Usage:
    python3 scripts/phase-1/change-requests/RAN1/05_link_duplicate_files.py
"""

import csv
import os
from pathlib import Path
from datetime import datetime


RELEASES = ["Rel-15", "Rel-16", "Rel-17", "Rel-18", "Rel-19"]


def find_tsg_file(tsg_tdoc, exclude_release=None):
    """모든 release 폴더에서 TSG 파일 찾기"""
    for release in RELEASES:
        if release == exclude_release:
            continue
        
        tsg_file = Path(f"data/data_raw/change-requests/RAN1/{release}/TSG/{tsg_tdoc}.zip")
        if tsg_file.exists():
            return tsg_file
    
    return None


def link_duplicate_files(release_name):
    """특정 Release의 누락된 TSG 파일 하드링크 생성"""
    print(f"\n[{release_name}]")
    
    # cr_list.csv 읽기
    csv_path = Path(f"data/data_raw/change-requests/RAN1/{release_name}/metadata/cr_list.csv")
    if not csv_path.exists():
        print(f"  ✗ cr_list.csv not found")
        return 0, 0
    
    tsg_dir = Path(f"data/data_raw/change-requests/RAN1/{release_name}/TSG")
    tsg_dir.mkdir(parents=True, exist_ok=True)
    
    linked_count = 0
    already_exists = 0
    not_found = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            tsg_tdoc = row['tsg_tdoc']
            
            if not tsg_tdoc or tsg_tdoc == '-':
                continue
            
            target_file = tsg_dir / f"{tsg_tdoc}.zip"
            
            # 이미 있으면 스킵
            if target_file.exists():
                already_exists += 1
                continue
            
            # 다른 release 폴더에서 찾기
            source_file = find_tsg_file(tsg_tdoc, exclude_release=release_name)
            
            if source_file:
                # 하드링크 생성
                try:
                    os.link(source_file, target_file)
                    linked_count += 1
                    print(f"  ✓ Linked: {tsg_tdoc}.zip <- {source_file.parent.parent.name}")
                except Exception as e:
                    print(f"  ✗ Failed to link {tsg_tdoc}.zip: {e}")
            else:
                not_found += 1
                print(f"  ⚠ Not found anywhere: {tsg_tdoc}.zip")
    
    print(f"  Summary: {linked_count} linked, {already_exists} already exist, {not_found} not found")
    
    return linked_count, not_found


def main():
    print("="*80)
    print("Link Duplicate TSG TDoc Files")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    total_linked = 0
    total_not_found = 0
    
    for release in RELEASES:
        linked, not_found = link_duplicate_files(release)
        total_linked += linked
        total_not_found += not_found
    
    print(f"\n{'='*80}")
    print(f"Total: {total_linked} files linked, {total_not_found} files not found")
    print(f"{'='*80}")
    
    if total_not_found > 0:
        print(f"\n⚠ {total_not_found} files could not be found in any release folder")
        print(f"   These files may need to be downloaded separately")
    else:
        print(f"\n✓ All duplicate files have been linked successfully!")
    
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
