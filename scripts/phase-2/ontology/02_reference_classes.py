#!/usr/bin/env python3
"""
Phase B: Reference 클래스 인스턴스 생성

Spec 기반: docs/phase-2/specs/tdoc-ontology-spec.md Step 7.3
입력: ontology/input/meetings/RAN1/*.xlsx (59개 파일)
출력: ontology/output/instances/*.jsonld

생성 클래스 (8개):
1. Meeting - 파일명에서 추출
2. Release - Release 컬럼 고유값
3. Company - company_aliases_significant.json (222개)
4. Contact - Contact, Contact ID 컬럼
5. WorkItem - Related WIs 컬럼
6. AgendaItem - Agenda item, Agenda item description 컬럼
7. Spec - Spec 컬럼
8. WorkingGroup - To, Cc 컬럼
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import warnings

warnings.filterwarnings('ignore')

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "input" / "meetings" / "RAN1"
INTERMEDIATE_DIR = BASE_DIR / "intermediate"
OUTPUT_DIR = BASE_DIR / "output" / "instances"

# JSON-LD 컨텍스트
CONTEXT = {
    "@context": {
        "tdoc": "http://3gpp.org/ontology/tdoc#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
}


def load_excel_file(filepath: Path) -> pd.DataFrame:
    """Excel 파일 로드"""
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
        return df
    except Exception as e:
        print(f"Error loading {filepath.name}: {e}")
        return pd.DataFrame()


def extract_meeting_from_filename(filename: str) -> Tuple[str, str]:
    """파일명에서 Meeting 정보 추출

    Spec 7.3.1: ID = {WG}#{회차} (예: RAN1#120)

    파일명 패턴:
    - TDoc_List_TSGR1_100.xlsx → RAN1#100
    - TDoc_List_TSGR1_100_e.xlsx → RAN1#100-e
    - TDoc_List_TSGR1_100b_e.xlsx → RAN1#100b-e
    - TDoc_List_TSGR1_101-e.xlsx → RAN1#101-e
    """
    # TSGR1 = TSG RAN1 = RAN1
    match = re.search(r'TSGR1_(\d+)([a-z]?)(?:[-_]?(e))?', filename, re.IGNORECASE)
    if match:
        meeting_num = match.group(1)
        letter_suffix = match.group(2) if match.group(2) else ""
        e_suffix = match.group(3) if match.group(3) else ""

        # 조합: 100 → RAN1#100, 100b → RAN1#100b, 100_e → RAN1#100-e, 100b_e → RAN1#100b-e
        suffix = letter_suffix
        if e_suffix:
            suffix = f"{letter_suffix}-e"

        meeting_id = f"RAN1#{meeting_num}{suffix}"
        return meeting_id, "RAN1"
    return None, None


def parse_work_items(value: str) -> List[str]:
    """Related WIs 컬럼 파싱

    Spec 7.3.5: 쉼표로 분리하여 복수 WorkItem 생성
    """
    if pd.isna(value) or not str(value).strip():
        return []

    # 쉼표로 분리하고 공백 제거
    items = [item.strip() for item in str(value).split(',')]
    return [item for item in items if item and item not in ['', 'nan', 'NaN']]


def parse_working_groups(value: str) -> List[str]:
    """To/Cc 컬럼 파싱

    Spec 7.3.8: 쉼표로 분리하여 복수 WorkingGroup 생성
    """
    if pd.isna(value) or not str(value).strip():
        return []

    # 쉼표로 분리
    items = [item.strip() for item in str(value).split(',')]

    # 유효한 Working Group만 필터링
    # 3GPP WG 패턴: RAN1, SA2, CT1, TSG RAN 등
    valid_wgs = []
    for item in items:
        if item and item not in ['', 'nan', 'NaN']:
            # 기본 정리
            item = item.strip()
            if item:
                valid_wgs.append(item)

    return valid_wgs


def generate_meetings(files: List[Path]) -> Dict[str, dict]:
    """Meeting 인스턴스 생성

    Spec 7.3.1: 파일명에서 추출
    속성: meetingNumber, workingGroup, canonicalMeetingNumber, meetingNumberInt

    canonicalMeetingNumber: -e suffix 제거 (COVID e-meeting 매칭용)
    예: RAN1#101-e → RAN1#101, RAN1#112bis-e → RAN1#112bis

    meetingNumberInt: 숫자 정렬용 (Spec CQ 결과 규칙)
    예: RAN1#122 → 122, RAN1#122b → 122
    """
    meetings = {}

    for filepath in files:
        meeting_id, wg = extract_meeting_from_filename(filepath.name)
        if meeting_id and meeting_id not in meetings:
            # canonicalMeetingNumber: -e suffix 제거 (Spec Section 5.6, 7.3.1)
            canonical = meeting_id[:-2] if meeting_id.endswith('-e') else meeting_id

            # meetingNumberInt: 숫자 부분 추출 (정렬용)
            # RAN1#122 → 122, RAN1#122b → 122, RAN1#84bis → 84
            num_match = re.search(r'#(\d+)', meeting_id)
            meeting_num_int = int(num_match.group(1)) if num_match else 0

            meetings[meeting_id] = {
                "@id": f"tdoc:meeting/{meeting_id.replace('#', '_')}",
                "@type": "tdoc:Meeting",
                "tdoc:meetingNumber": meeting_id,
                "tdoc:canonicalMeetingNumber": canonical,
                "tdoc:meetingNumberInt": meeting_num_int,
                "tdoc:workingGroup": wg
            }

    return meetings


def generate_releases(all_data: List[pd.DataFrame]) -> Dict[str, dict]:
    """Release 인스턴스 생성

    Spec 7.3.2: Release 컬럼 고유값
    속성: releaseName
    """
    releases = {}

    for df in all_data:
        if 'Release' not in df.columns:
            continue

        for release in df['Release'].dropna().unique():
            release = str(release).strip()
            if release and release not in releases:
                releases[release] = {
                    "@id": f"tdoc:release/{release.replace('-', '_')}",
                    "@type": "tdoc:Release",
                    "tdoc:releaseName": release
                }

    return releases


def generate_companies(aliases_path: Path) -> Dict[str, dict]:
    """Company 인스턴스 생성

    Spec 7.3.3: company_aliases_significant.json 사용
    속성: companyName
    """
    companies = {}

    with open(aliases_path, 'r', encoding='utf-8') as f:
        aliases = json.load(f)

    for canonical, data in aliases.items():
        # ID 생성: 특수문자 제거
        company_id = re.sub(r'[^a-zA-Z0-9]', '_', canonical)
        companies[canonical] = {
            "@id": f"tdoc:company/{company_id}",
            "@type": ["tdoc:Company", "foaf:Organization"],
            "tdoc:companyName": canonical,
            "tdoc:aliases": data.get("aliases", [])
        }

    return companies


def generate_contacts(all_data: List[pd.DataFrame]) -> Dict[str, dict]:
    """Contact 인스턴스 생성

    Spec 7.3.4: Contact, Contact ID 컬럼
    속성: contactName, contactId
    """
    contacts = {}

    for df in all_data:
        if 'Contact' not in df.columns or 'Contact ID' not in df.columns:
            continue

        for _, row in df.iterrows():
            contact_name = row.get('Contact', '')
            contact_id = row.get('Contact ID', '')

            if pd.isna(contact_name) or not str(contact_name).strip():
                continue

            contact_name = str(contact_name).strip()
            contact_id = str(contact_id).strip() if not pd.isna(contact_id) else ""

            # Contact ID를 키로 사용 (고유)
            key = contact_id if contact_id else contact_name

            if key and key not in contacts:
                contacts[key] = {
                    "@id": f"tdoc:contact/{re.sub(r'[^a-zA-Z0-9]', '_', key)}",
                    "@type": ["tdoc:Contact", "foaf:Person"],
                    "tdoc:contactName": contact_name,
                    "tdoc:contactId": contact_id
                }

    return contacts


def generate_work_items(all_data: List[pd.DataFrame]) -> Dict[str, dict]:
    """WorkItem 인스턴스 생성

    Spec 7.3.5: Related WIs 컬럼
    속성: workItemCode
    """
    work_items = {}

    for df in all_data:
        if 'Related WIs' not in df.columns:
            continue

        for value in df['Related WIs'].dropna():
            items = parse_work_items(value)
            for item in items:
                if item not in work_items:
                    work_items[item] = {
                        "@id": f"tdoc:workitem/{re.sub(r'[^a-zA-Z0-9_-]', '_', item)}",
                        "@type": "tdoc:WorkItem",
                        "tdoc:workItemCode": item
                    }

    return work_items


def generate_agenda_items(all_data: List[pd.DataFrame]) -> Dict[str, dict]:
    """AgendaItem 인스턴스 생성

    Spec 7.3.6: Agenda item, Agenda item description 컬럼
    속성: agendaNumber, agendaDescription
    """
    agenda_items = {}

    for df in all_data:
        if 'Agenda item' not in df.columns:
            continue

        for _, row in df.iterrows():
            agenda_num = row.get('Agenda item', '')
            agenda_desc = row.get('Agenda item description', '')

            if pd.isna(agenda_num) or not str(agenda_num).strip():
                continue

            agenda_num = str(agenda_num).strip()
            agenda_desc = str(agenda_desc).strip() if not pd.isna(agenda_desc) else ""

            if agenda_num not in agenda_items:
                agenda_items[agenda_num] = {
                    "@id": f"tdoc:agenda/{re.sub(r'[^a-zA-Z0-9.]', '_', agenda_num)}",
                    "@type": "tdoc:AgendaItem",
                    "tdoc:agendaNumber": agenda_num,
                    "tdoc:agendaDescription": agenda_desc
                }
            elif not agenda_items[agenda_num].get("tdoc:agendaDescription") and agenda_desc:
                # 기존에 description이 없고 새로 발견되면 업데이트
                agenda_items[agenda_num]["tdoc:agendaDescription"] = agenda_desc

    return agenda_items


def generate_specs(all_data: List[pd.DataFrame]) -> Dict[str, dict]:
    """Spec 인스턴스 생성

    Spec 7.3.7: Spec 컬럼
    속성: specNumber
    """
    specs = {}

    for df in all_data:
        if 'Spec' not in df.columns:
            continue

        for value in df['Spec'].dropna():
            spec_num = str(value).strip()
            if spec_num and spec_num not in specs:
                specs[spec_num] = {
                    "@id": f"tdoc:spec/{spec_num.replace('.', '_')}",
                    "@type": "tdoc:Spec",
                    "tdoc:specNumber": spec_num
                }

    return specs


def generate_working_groups(all_data: List[pd.DataFrame]) -> Dict[str, dict]:
    """WorkingGroup 인스턴스 생성

    Spec 7.3.8: To, Cc 컬럼
    속성: wgName
    """
    working_groups = {}

    for df in all_data:
        # To 컬럼
        if 'To' in df.columns:
            for value in df['To'].dropna():
                wgs = parse_working_groups(value)
                for wg in wgs:
                    if wg not in working_groups:
                        working_groups[wg] = {
                            "@id": f"tdoc:wg/{re.sub(r'[^a-zA-Z0-9]', '_', wg)}",
                            "@type": "tdoc:WorkingGroup",
                            "tdoc:wgName": wg
                        }

        # Cc 컬럼
        if 'Cc' in df.columns:
            for value in df['Cc'].dropna():
                wgs = parse_working_groups(value)
                for wg in wgs:
                    if wg not in working_groups:
                        working_groups[wg] = {
                            "@id": f"tdoc:wg/{re.sub(r'[^a-zA-Z0-9]', '_', wg)}",
                            "@type": "tdoc:WorkingGroup",
                            "tdoc:wgName": wg
                        }

    return working_groups


def save_jsonld(data: Dict[str, dict], output_path: Path, class_name: str):
    """JSON-LD 형식으로 저장"""
    output = {
        **CONTEXT,
        "@graph": list(data.values())
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {class_name}: {len(data)}개 → {output_path.name}")


def main():
    """Phase B 메인 실행"""
    print("=" * 60)
    print("Phase B: Reference 클래스 인스턴스 생성")
    print("=" * 60)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 입력 파일 목록
    files = sorted(INPUT_DIR.glob("*.xlsx"))
    print(f"\n입력 파일: {len(files)}개")

    # 모든 Excel 파일 로드
    print("\n[1/9] 데이터 로딩 중...")
    all_data = []
    for filepath in files:
        df = load_excel_file(filepath)
        if not df.empty:
            all_data.append(df)
    print(f"  로드 완료: {len(all_data)}개 파일")

    # 1. Meeting
    print("\n[2/9] Meeting 인스턴스 생성...")
    meetings = generate_meetings(files)
    save_jsonld(meetings, OUTPUT_DIR / "meetings.jsonld", "Meeting")

    # 2. Release
    print("\n[3/9] Release 인스턴스 생성...")
    releases = generate_releases(all_data)
    save_jsonld(releases, OUTPUT_DIR / "releases.jsonld", "Release")

    # 3. Company
    print("\n[4/9] Company 인스턴스 생성...")
    aliases_path = INTERMEDIATE_DIR / "company_aliases_significant.json"
    if aliases_path.exists():
        companies = generate_companies(aliases_path)
        save_jsonld(companies, OUTPUT_DIR / "companies.jsonld", "Company")
    else:
        print(f"  ⚠️ {aliases_path} 없음 - Phase A를 먼저 실행하세요")
        companies = {}

    # 4. Contact
    print("\n[5/9] Contact 인스턴스 생성...")
    contacts = generate_contacts(all_data)
    save_jsonld(contacts, OUTPUT_DIR / "contacts.jsonld", "Contact")

    # 5. WorkItem
    print("\n[6/9] WorkItem 인스턴스 생성...")
    work_items = generate_work_items(all_data)
    save_jsonld(work_items, OUTPUT_DIR / "work_items.jsonld", "WorkItem")

    # 6. AgendaItem
    print("\n[7/9] AgendaItem 인스턴스 생성...")
    agenda_items = generate_agenda_items(all_data)
    save_jsonld(agenda_items, OUTPUT_DIR / "agenda_items.jsonld", "AgendaItem")

    # 7. Spec
    print("\n[8/9] Spec 인스턴스 생성...")
    specs = generate_specs(all_data)
    save_jsonld(specs, OUTPUT_DIR / "specs.jsonld", "Spec")

    # 8. WorkingGroup
    print("\n[9/9] WorkingGroup 인스턴스 생성...")
    working_groups = generate_working_groups(all_data)
    save_jsonld(working_groups, OUTPUT_DIR / "working_groups.jsonld", "WorkingGroup")

    # 요약
    print("\n" + "=" * 60)
    print("Phase B 완료")
    print("=" * 60)
    print(f"\n📊 생성 결과:")
    print(f"  Meeting:      {len(meetings):>6}개")
    print(f"  Release:      {len(releases):>6}개")
    print(f"  Company:      {len(companies):>6}개")
    print(f"  Contact:      {len(contacts):>6}개")
    print(f"  WorkItem:     {len(work_items):>6}개")
    print(f"  AgendaItem:   {len(agenda_items):>6}개")
    print(f"  Spec:         {len(specs):>6}개")
    print(f"  WorkingGroup: {len(working_groups):>6}개")
    print(f"  {'─' * 20}")
    total = sum([len(meetings), len(releases), len(companies), len(contacts),
                 len(work_items), len(agenda_items), len(specs), len(working_groups)])
    print(f"  총계:         {total:>6}개")
    print(f"\n출력 디렉토리: {OUTPUT_DIR}")

    # Phase B 결과를 intermediate에도 저장 (Phase C에서 참조용)
    reference_summary = {
        "meetings": list(meetings.keys()),
        "releases": list(releases.keys()),
        "companies": list(companies.keys()),
        "contacts": list(contacts.keys()),
        "work_items": list(work_items.keys()),
        "agenda_items": list(agenda_items.keys()),
        "specs": list(specs.keys()),
        "working_groups": list(working_groups.keys())
    }

    summary_path = INTERMEDIATE_DIR / "reference_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(reference_summary, f, ensure_ascii=False, indent=2)
    print(f"\n참조 요약 저장: {summary_path}")


if __name__ == "__main__":
    main()
