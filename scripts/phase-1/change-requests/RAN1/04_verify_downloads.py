#!/usr/bin/env python3
"""
Change Request TDoc 다운로드 검증

cr_list.csv와 실제 다운로드된 파일을 비교하여
download_status.csv 생성 및 누락 파일 확인

Usage:
    python3 scripts/phase-1/change-requests/04_verify_downloads.py
"""

import csv
from pathlib import Path
from datetime import datetime


RELEASES = ["Rel-15", "Rel-16", "Rel-17", "Rel-18", "Rel-19"]


def verify_release(release_name):
    """특정 Release의 다운로드 상태 검증"""
    print(f"\n[{release_name}]")

    # cr_list.csv 읽기
    csv_path = Path(f"data/data_raw/change-requests/RAN1/{release_name}/metadata/cr_list.csv")
    if not csv_path.exists():
        print(f"  ✗ cr_list.csv not found")
        return []

    # 다운로드 상태 확인
    status_list = []
    tsg_dir = Path(f"data/data_raw/change-requests/RAN1/{release_name}/TSG")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # TSG TDoc 확인
            tsg_tdoc = row['tsg_tdoc']
            tsg_file = tsg_dir / f"{tsg_tdoc}.zip" if tsg_tdoc and tsg_tdoc != '-' else None
            tsg_downloaded = tsg_file.exists() if tsg_file else False
            tsg_size = tsg_file.stat().st_size if tsg_downloaded else 0

            status = {
                'spec_number': row['spec_number'],
                'cr_number': row['cr_number'],
                'tsg_tdoc': tsg_tdoc,
                'tsg_downloaded': tsg_downloaded,
                'tsg_file_path': f"TSG/{tsg_tdoc}.zip" if tsg_tdoc and tsg_tdoc != '-' else '',
                'tsg_file_size': tsg_size,
                'download_date': datetime.now().strftime('%Y-%m-%d')
            }
            status_list.append(status)

    # 통계
    total_crs = len(status_list)
    tsg_expected = sum(1 for s in status_list if s['tsg_tdoc'] and s['tsg_tdoc'] != '-')
    tsg_downloaded = sum(1 for s in status_list if s['tsg_downloaded'])

    print(f"  Total CRs: {total_crs}")
    print(f"  TSG TDocs: {tsg_downloaded}/{tsg_expected} ({tsg_downloaded*100//tsg_expected if tsg_expected > 0 else 0}%)")

    # 누락 파일
    tsg_missing = [s for s in status_list if s['tsg_tdoc'] and s['tsg_tdoc'] != '-' and not s['tsg_downloaded']]

    if tsg_missing:
        print(f"  ⚠ Missing TSG TDocs: {len(tsg_missing)}")
    else:
        print(f"  ✓ All TSG files downloaded successfully!")

    return status_list


def save_download_status(release_name, status_list):
    """download_status.csv 저장"""
    if not status_list:
        return

    output_path = Path(f"data/data_raw/change-requests/RAN1/{release_name}/metadata/download_status.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'spec_number', 'cr_number',
        'tsg_tdoc', 'tsg_downloaded', 'tsg_file_path', 'tsg_file_size',
        'download_date'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(status_list)

    print(f"  ✓ Saved to {output_path}")


def generate_summary_report(all_status):
    """전체 요약 리포트 생성"""
    print(f"\n{'='*80}")
    print(f"Download Verification Summary (TSG only)")
    print(f"{'='*80}")

    total_crs = len(all_status)
    tsg_expected = sum(1 for s in all_status if s['tsg_tdoc'] and s['tsg_tdoc'] != '-')
    tsg_downloaded = sum(1 for s in all_status if s['tsg_downloaded'])

    print(f"Total CRs: {total_crs}")
    print(f"\nTSG TDocs:")
    print(f"  Expected: {tsg_expected}")
    print(f"  Downloaded: {tsg_downloaded}")
    print(f"  Missing: {tsg_expected - tsg_downloaded}")
    print(f"  Success Rate: {tsg_downloaded*100//tsg_expected if tsg_expected > 0 else 0}%")

    # 누락 파일 상세
    tsg_missing = [s for s in all_status if s['tsg_tdoc'] and s['tsg_tdoc'] != '-' and not s['tsg_downloaded']]

    if tsg_missing:
        print(f"\n{'='*80}")
        print(f"Missing Files Details")
        print(f"{'='*80}")

        print(f"\nMissing TSG TDocs ({len(tsg_missing)}):")
        for s in tsg_missing[:20]:  # 처음 20개 표시
            print(f"  - {s['tsg_tdoc']} (Spec: {s['spec_number']}, CR: {s['cr_number']})")
        if len(tsg_missing) > 20:
            print(f"  ... and {len(tsg_missing) - 20} more")

    print(f"\n{'='*80}")

    # 전체 상태
    if tsg_downloaded == tsg_expected:
        print(f"✓ All TSG downloads COMPLETE!")
    else:
        print(f"⚠ {tsg_expected - tsg_downloaded} TSG files are missing - check FTP URLs or re-run download")

    print(f"{'='*80}")


def main():
    print("="*80)
    print("RAN1 Change Request Download Verification")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    all_status = []

    for release in RELEASES:
        status_list = verify_release(release)
        save_download_status(release, status_list)
        all_status.extend(status_list)

    # 전체 요약
    generate_summary_report(all_status)


if __name__ == "__main__":
    main()
