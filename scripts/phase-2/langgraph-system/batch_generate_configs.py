#!/usr/bin/env python3
"""
RAN1 #110-118 미팅 config 파일 자동 생성

Usage:
    python batch_generate_configs.py
"""

import os
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_BASE = PROJECT_ROOT / "data" / "data_transformed" / "meetings" / "RAN1"
CONFIG_DIR = Path(__file__).parent / "config" / "meetings"

# 처리할 미팅 목록 (110-118)
MEETINGS = [
    "110", "110b-e", "111", "112", "112b-e", "113",
    "114", "114b", "115", "116", "116b", "117", "118", "118b"
]

def find_minutes_file(meeting_folder: Path) -> str | None:
    """Report 폴더에서 Minutes 파일 찾기 (Draft/Final 무관)"""
    report_dir = meeting_folder / "Report"
    if not report_dir.exists():
        return None

    for subdir in report_dir.iterdir():
        if subdir.is_dir():
            for f in subdir.iterdir():
                if f.suffix == ".docx" and "Minutes" in f.name:
                    # 상대 경로 반환 (data_transformed 기준)
                    rel_path = f.relative_to(DATA_BASE.parent.parent)
                    return str(rel_path)
    return None

def find_tdoc_list(meeting_folder: Path, meeting_num: str) -> str | None:
    """Docs 폴더에서 TdocList 파일 찾기"""
    docs_dir = meeting_folder / "Docs"
    if not docs_dir.exists():
        return None

    # 미팅 번호에 맞는 TdocList 찾기
    for f in docs_dir.iterdir():
        if f.suffix == ".xlsx" and "TDoc_List" in f.name:
            # 현재 미팅 번호가 포함된 파일 우선
            if f"#{meeting_num}" in f.name or f"%23{meeting_num}" in f.name:
                rel_path = f.relative_to(DATA_BASE.parent.parent)
                return str(rel_path)

    # 없으면 아무 TdocList나 반환
    for f in docs_dir.iterdir():
        if f.suffix == ".xlsx" and "TDoc_List" in f.name:
            rel_path = f.relative_to(DATA_BASE.parent.parent)
            return str(rel_path)

    return None

def generate_config(meeting_num: str) -> str | None:
    """미팅 config YAML 생성"""
    # 폴더명 결정
    folder_name = f"TSGR1_{meeting_num}"
    meeting_folder = DATA_BASE / folder_name

    if not meeting_folder.exists():
        print(f"  ❌ Folder not found: {folder_name}")
        return None

    # 파일 찾기
    minutes_path = find_minutes_file(meeting_folder)
    tdoc_path = find_tdoc_list(meeting_folder, meeting_num)

    if not minutes_path:
        print(f"  ❌ No Minutes file found for {meeting_num}")
        return None

    # meeting_id 생성 (b-e, bis 등 정규화)
    meeting_id = f"RAN1_{meeting_num.replace('-', '_').replace('b_e', 'b_e')}"

    config = f'''# {meeting_id}.yaml
# Auto-generated config for RAN1 #{meeting_num}

meeting:
  id: "{meeting_id}"
  number: "{meeting_num}"
  working_group: "RAN1"
  folder_name: "{folder_name}"

  input:
    final_minutes: "{minutes_path}"
    tdoc_list: "{tdoc_path or ''}"

  output:
    filename_pattern: "{{meeting_id}}_{{content_type}}.md"

  hints:
    expected_counts:
      incoming_ls:
        primary: 0
        cc_only: 0
        total: 0
    source_wgs:
      - "RAN2"
      - "RAN3"
      - "RAN4"
      - "SA2"
'''
    return config

def main():
    print("=" * 60)
    print("RAN1 #110-118 Config Generator")
    print("=" * 60)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    for meeting_num in MEETINGS:
        print(f"\n[{meeting_num}] Processing...")

        config_content = generate_config(meeting_num)
        if config_content:
            # 파일명 결정
            config_name = f"RAN1_{meeting_num.replace('-', '_')}.yaml"
            config_path = CONFIG_DIR / config_name

            config_path.write_text(config_content)
            print(f"  ✅ Generated: {config_name}")
            generated += 1

    print(f"\n{'=' * 60}")
    print(f"Total: {generated}/{len(MEETINGS)} configs generated")
    print(f"Output: {CONFIG_DIR}")

if __name__ == "__main__":
    main()
