#!/usr/bin/env python3
"""
Phase C: Tdoc/CR/LS 인스턴스 생성

Spec 기반: docs/phase-2/specs/tdoc-ontology-spec.md Step 7.3.9~7.3.11
입력: ontology/input/meetings/RAN1/*.xlsx (59개 파일)
출력: ontology/output/instances/tdocs.jsonld

클래스별 판단 로직 (Spec 4.5):
- CR: Type이 'CR', 'draftCR', 'pCR'
- LS: Type이 'LS out', 'LS in'
- Tdoc: 그 외 모든 Type
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import pandas as pd
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "input" / "meetings" / "RAN1"
INTERMEDIATE_DIR = BASE_DIR / "intermediate"
OUTPUT_DIR = BASE_DIR / "output" / "instances"

# JSON-LD 컨텍스트
# Note: Relations must have "@type": "@id" to be recognized as relationships by n10s
CONTEXT = {
    "@context": {
        "tdoc": "http://3gpp.org/ontology/tdoc#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        # Relations - must be @id type for n10s to create relationships
        "modifies": {"@id": "tdoc:modifies", "@type": "@id"},
        "replyTo": {"@id": "tdoc:replyTo", "@type": "@id"},
        "sentTo": {"@id": "tdoc:sentTo", "@type": "@id"},
        "hasContact": {"@id": "tdoc:hasContact", "@type": "@id"},
        "belongsTo": {"@id": "tdoc:belongsTo", "@type": "@id"},
        "presentedAt": {"@id": "tdoc:presentedAt", "@type": "@id"},
        "submittedBy": {"@id": "tdoc:submittedBy", "@type": "@id"},
        "originatedFrom": {"@id": "tdoc:originatedFrom", "@type": "@id"},
    }
}

# CR 타입
CR_TYPES = {'CR', 'draftCR', 'pCR'}

# LS 타입
LS_TYPES = {'LS out', 'LS in'}

# Working Group 패턴 (Issue #1, #5 해결용)
# Source 컬럼에 WG와 Company가 혼합되어 있음 (예: "RAN3, Huawei")
# 이를 분리하여 WG는 ORIGINATED_FROM, Company는 SUBMITTED_BY 관계로 연결
WG_PATTERNS = [
    r'^RAN\d?$',      # RAN, RAN1-6
    r'^SA\d?$',       # SA, SA1-6
    r'^CT\d?$',       # CT, CT1-6
    r'^TSG[ _]?RAN$', # TSG RAN
    r'^TSG[ _]?SA$',  # TSG SA
    r'^TSG[ _]?CT$',  # TSG CT
]

# 역할 패턴 (Chair, Rapporteur 등)
ROLE_PATTERNS = [
    r'.*[Cc]hair.*',
    r'.*[Cc]hairman.*',
]


def load_company_aliases() -> Dict[str, str]:
    """Company 별칭 → 정규화 맵 로드"""
    aliases_path = INTERMEDIATE_DIR / "company_aliases_significant.json"
    reverse_map = {}

    if aliases_path.exists():
        with open(aliases_path, 'r', encoding='utf-8') as f:
            aliases = json.load(f)

        for canonical, data in aliases.items():
            for alias in data.get("aliases", []):
                reverse_map[alias.lower()] = canonical
            reverse_map[canonical.lower()] = canonical

    return reverse_map


def load_reference_data() -> Dict[str, set]:
    """Reference 클래스 데이터 로드 (유효성 검증용)"""
    summary_path = INTERMEDIATE_DIR / "reference_summary.json"
    if summary_path.exists():
        with open(summary_path, 'r', encoding='utf-8') as f:
            return {k: set(v) for k, v in json.load(f).items()}
    return {}


def extract_meeting_from_filename(filename: str) -> str:
    """파일명에서 Meeting ID 추출"""
    match = re.search(r'TSGR1_(\d+)([a-z]?)(?:[-_]?(e))?', filename, re.IGNORECASE)
    if match:
        meeting_num = match.group(1)
        letter_suffix = match.group(2) if match.group(2) else ""
        e_suffix = match.group(3) if match.group(3) else ""
        suffix = letter_suffix
        if e_suffix:
            suffix = f"{letter_suffix}-e"
        return f"RAN1#{meeting_num}{suffix}"
    return None


def classify_tdoc_type(type_value: str) -> str:
    """Type 값으로 클래스 분류

    Spec 4.5 Type별 클래스 매핑:
    - CR: CR, draftCR, pCR
    - LS: LS out, LS in
    - Tdoc: 그 외 모든 값
    """
    if pd.isna(type_value):
        return "Tdoc"

    type_value = str(type_value).strip()

    if type_value in CR_TYPES:
        return "CR"
    elif type_value in LS_TYPES:
        return "LS"
    else:
        return "Tdoc"


def is_working_group(name: str) -> bool:
    """Working Group 패턴인지 확인

    Issue #1, #5: Source 컬럼에 WG와 Company가 혼합됨
    예: "RAN3, Huawei" → RAN3는 WG, Huawei는 Company
    """
    name = name.strip()
    for pattern in WG_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return True
    return False


def is_role(name: str) -> bool:
    """역할 패턴인지 확인 (Chair, Rapporteur 등)"""
    name = name.strip()
    for pattern in ROLE_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return True
    return False


def parse_submitters(source: str, company_map: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """Source 컬럼에서 회사와 Working Group을 분리 추출

    Issue #1, #5 해결: WG와 Company를 분리하여 다른 관계로 연결
    - Company → SUBMITTED_BY 관계
    - WorkingGroup → ORIGINATED_FROM 관계

    Spec 7.6.3: 괄호 내 쉼표 보호 → 역할 분리 → 쉼표로 분리

    Returns:
        Tuple[List[str], List[str]]: (companies, working_groups)
    """
    if pd.isna(source) or not str(source).strip():
        return [], []

    source = str(source)

    # 역할 패턴 제거: "Moderator (Samsung)" → "Samsung"
    role_pattern = r'^(?:Moderator|Rapporteur|WI [Rr]apporteur|Ad-Hoc Chair|.*Chair)\s*\(([^)]+)\)$'
    match = re.match(role_pattern, source)
    if match:
        source = match.group(1)

    # 괄호 안의 쉼표 보호
    protected = re.sub(r'\(([^)]*),([^)]*)\)', lambda m: m.group(0).replace(',', '§'), source)

    # 쉼표로 분리
    parts = [p.strip().replace('§', ',') for p in protected.split(',')]

    # 분류: Company vs WorkingGroup
    companies = []
    working_groups = []

    for part in parts:
        if not part:
            continue

        # 역할에서 회사 추출
        role_match = re.match(role_pattern, part)
        if role_match:
            part = role_match.group(1)

        # WG 패턴 확인
        if is_working_group(part):
            wg_name = part.upper()  # 정규화: RAN3, SA2 등
            if wg_name not in working_groups:
                working_groups.append(wg_name)
        # 역할 패턴은 건너뜀 (RAN1_Chair 등)
        elif is_role(part):
            continue
        # 일반 회사
        else:
            normalized = company_map.get(part.lower(), part)
            if normalized and normalized not in companies:
                companies.append(normalized)

    return companies, working_groups


def parse_companies(source: str, company_map: Dict[str, str]) -> List[str]:
    """Source 컬럼에서 회사 목록 추출 및 정규화 (하위 호환성용)

    Note: parse_submitters()를 사용하는 것을 권장
    """
    companies, _ = parse_submitters(source, company_map)
    return companies


def parse_work_items(value: str) -> List[str]:
    """Related WIs 컬럼 파싱"""
    if pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


def parse_working_groups(value: str) -> List[str]:
    """To/Cc 컬럼 파싱"""
    if pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


def safe_string(value) -> Optional[str]:
    """안전하게 문자열로 변환"""
    if pd.isna(value):
        return None
    s = str(value).strip()
    return s if s else None


def safe_datetime(value) -> Optional[str]:
    """날짜/시간 값을 ISO 형식으로 변환"""
    if pd.isna(value):
        return None
    try:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    except:
        return None


def safe_bool(value) -> Optional[bool]:
    """Boolean 값 변환"""
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ['yes', 'true', '1', 'y']:
        return True
    elif s in ['no', 'false', '0', 'n']:
        return False
    return None


def create_tdoc_instance(row: pd.Series, meeting_id: str, company_map: Dict[str, str]) -> dict:
    """Tdoc 인스턴스 생성 (기본 클래스)

    Spec 7.3.9: 속성 및 관계 매핑
    """
    tdoc_number = safe_string(row.get('TDoc', ''))
    if not tdoc_number:
        return None

    # 기본 속성
    instance = {
        "@id": f"tdoc:{tdoc_number}",
        "@type": "tdoc:Tdoc",
        "tdoc:tdocNumber": tdoc_number,
        "tdoc:title": safe_string(row.get('Title', '')),
        "tdoc:type": safe_string(row.get('Type', '')),
        "tdoc:status": safe_string(row.get('TDoc Status', '')),
    }

    # 선택적 속성
    if abstract := safe_string(row.get('Abstract', '')):
        instance["tdoc:abstract"] = abstract

    if for_value := safe_string(row.get('For', '')):
        instance["tdoc:for"] = for_value

    if reservation_date := safe_datetime(row.get('Reservation date', '')):
        instance["tdoc:reservationDate"] = reservation_date

    if uploaded_date := safe_datetime(row.get('Uploaded', '')):
        instance["tdoc:uploadedDate"] = uploaded_date

    if remarks := safe_string(row.get('Secretary Remarks', '')):
        instance["tdoc:secretaryRemarks"] = remarks

    # 관계: submittedBy (Company), originatedFrom (WorkingGroup)
    # Issue #1, #5 해결: WG와 Company를 분리
    companies, working_groups = parse_submitters(row.get('Source', ''), company_map)
    if companies:
        instance["submittedBy"] = [f"tdoc:company/{re.sub(r'[^a-zA-Z0-9]', '_', c)}" for c in companies]
    if working_groups:
        instance["originatedFrom"] = [f"tdoc:wg/{wg}" for wg in working_groups]

    # 관계: hasContact (Contact)
    if contact_id := safe_string(row.get('Contact ID', '')):
        instance["hasContact"] = f"tdoc:contact/{re.sub(r'[^a-zA-Z0-9]', '_', contact_id)}"

    # 관계: relatedTo (WorkItem)
    work_items = parse_work_items(row.get('Related WIs', ''))
    if work_items:
        instance["tdoc:relatedTo"] = [f"tdoc:workitem/{re.sub(r'[^a-zA-Z0-9_-]', '_', wi)}" for wi in work_items]

    # 관계: belongsTo (AgendaItem)
    if agenda := safe_string(row.get('Agenda item', '')):
        instance["belongsTo"] = f"tdoc:agenda/{re.sub(r'[^a-zA-Z0-9.]', '_', agenda)}"

    # 관계: targetRelease (Release)
    if release := safe_string(row.get('Release', '')):
        instance["tdoc:targetRelease"] = f"tdoc:release/{release.replace('-', '_')}"

    # 관계: presentedAt (Meeting)
    instance["presentedAt"] = f"tdoc:meeting/{meeting_id.replace('#', '_')}"

    # 관계: isRevisionOf, revisedTo, replyTo, replyIn (Tdoc → Tdoc)
    if is_revision_of := safe_string(row.get('Is revision of', '')):
        instance["tdoc:isRevisionOf"] = f"tdoc:{is_revision_of}"

    if revised_to := safe_string(row.get('Revised to', '')):
        instance["tdoc:revisedTo"] = f"tdoc:{revised_to}"

    if reply_to := safe_string(row.get('Reply to', '')):
        instance["replyTo"] = f"tdoc:{reply_to}"

    if reply_in := safe_string(row.get('Reply in', '')):
        instance["tdoc:replyIn"] = f"tdoc:{reply_in}"

    return instance


def create_cr_instance(row: pd.Series, meeting_id: str, company_map: Dict[str, str]) -> dict:
    """CR 인스턴스 생성 (Tdoc 상속 + 추가 속성)

    Spec 7.3.10: CR 전용 속성 및 modifies 관계
    """
    # 기본 Tdoc 속성
    instance = create_tdoc_instance(row, meeting_id, company_map)
    if not instance:
        return None

    # 클래스 변경
    instance["@type"] = "tdoc:CR"

    # CR 전용 속성
    if cr_number := safe_string(row.get('CR', '')):
        instance["tdoc:crNumber"] = cr_number

    if cr_category := safe_string(row.get('CR category', '')):
        instance["tdoc:crCategory"] = cr_category

    if clauses := safe_string(row.get('Clauses Affected', '')):
        instance["tdoc:clausesAffected"] = clauses

    if tsg_pack := safe_string(row.get('TSG CR Pack', '')):
        instance["tdoc:tsgCRPack"] = tsg_pack

    # Boolean 속성 (영향 범위)
    if (uicc := safe_bool(row.get('UICC', ''))) is not None:
        instance["tdoc:affectsUICC"] = uicc

    if (me := safe_bool(row.get('ME', ''))) is not None:
        instance["tdoc:affectsME"] = me

    if (ran := safe_bool(row.get('RAN', ''))) is not None:
        instance["tdoc:affectsRAN"] = ran

    if (cn := safe_bool(row.get('CN', ''))) is not None:
        instance["tdoc:affectsCN"] = cn

    # 관계: modifies (Spec) - CR 전용
    if spec := safe_string(row.get('Spec', '')):
        instance["modifies"] = f"tdoc:spec/{spec.replace('.', '_')}"

    return instance


def create_ls_instance(row: pd.Series, meeting_id: str, company_map: Dict[str, str]) -> dict:
    """LS 인스턴스 생성 (Tdoc 상속 + 추가 속성)

    Spec 7.3.11: direction, sentTo, ccTo, originalLS
    """
    # 기본 Tdoc 속성
    instance = create_tdoc_instance(row, meeting_id, company_map)
    if not instance:
        return None

    # 클래스 변경
    instance["@type"] = "tdoc:LS"

    # direction 추출
    type_value = safe_string(row.get('Type', ''))
    if type_value == 'LS out':
        instance["tdoc:direction"] = "out"
    elif type_value == 'LS in':
        instance["tdoc:direction"] = "in"

    # 관계: sentTo (WorkingGroup)
    to_wgs = parse_working_groups(row.get('To', ''))
    if to_wgs:
        instance["sentTo"] = [f"tdoc:wg/{re.sub(r'[^a-zA-Z0-9]', '_', wg)}" for wg in to_wgs]

    # 관계: ccTo (WorkingGroup)
    cc_wgs = parse_working_groups(row.get('Cc', ''))
    if cc_wgs:
        instance["tdoc:ccTo"] = [f"tdoc:wg/{re.sub(r'[^a-zA-Z0-9]', '_', wg)}" for wg in cc_wgs]

    # 관계: originalLS (LS in 전용)
    if instance.get("tdoc:direction") == "in":
        if original_ls := safe_string(row.get('Original LS', '')):
            instance["tdoc:originalLS"] = f"tdoc:{original_ls}"

    return instance


def process_file(filepath: Path, company_map: Dict[str, str]) -> Tuple[List[dict], Dict[str, int]]:
    """단일 파일 처리"""
    meeting_id = extract_meeting_from_filename(filepath.name)
    if not meeting_id:
        return [], {}

    try:
        df = pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        print(f"  Error loading {filepath.name}: {e}")
        return [], {}

    instances = []
    stats = {"Tdoc": 0, "CR": 0, "LS": 0}

    for _, row in df.iterrows():
        type_value = safe_string(row.get('Type', ''))
        doc_class = classify_tdoc_type(type_value)

        if doc_class == "CR":
            instance = create_cr_instance(row, meeting_id, company_map)
        elif doc_class == "LS":
            instance = create_ls_instance(row, meeting_id, company_map)
        else:
            instance = create_tdoc_instance(row, meeting_id, company_map)

        if instance:
            instances.append(instance)
            stats[doc_class] += 1

    return instances, stats


def main():
    """Phase C 메인 실행"""
    print("=" * 60)
    print("Phase C: Tdoc/CR/LS 인스턴스 생성")
    print("=" * 60)

    # Company 정규화 맵 로드
    print("\n[1/4] Company 정규화 맵 로딩...")
    company_map = load_company_aliases()
    print(f"  정규화 맵 로드: {len(company_map)}개 별칭")

    # 입력 파일 목록
    files = sorted(INPUT_DIR.glob("*.xlsx"))
    print(f"\n[2/4] 입력 파일: {len(files)}개")

    # 파일별 처리
    print("\n[3/4] 인스턴스 생성 중...")
    all_instances = []
    total_stats = {"Tdoc": 0, "CR": 0, "LS": 0}

    for i, filepath in enumerate(files, 1):
        instances, stats = process_file(filepath, company_map)
        all_instances.extend(instances)

        for k, v in stats.items():
            total_stats[k] += v

        if i % 10 == 0 or i == len(files):
            print(f"  {i}/{len(files)} 파일 처리 완료...")

    # 저장
    print(f"\n[4/4] JSON-LD 저장...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        **CONTEXT,
        "@graph": all_instances
    }

    output_path = OUTPUT_DIR / "tdocs.jsonld"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 요약
    print("\n" + "=" * 60)
    print("Phase C 완료")
    print("=" * 60)

    total = sum(total_stats.values())
    print(f"\n📊 생성 결과:")
    print(f"  Tdoc (일반): {total_stats['Tdoc']:>8}개")
    print(f"  CR:          {total_stats['CR']:>8}개")
    print(f"  LS:          {total_stats['LS']:>8}개")
    print(f"  {'─' * 22}")
    print(f"  총계:        {total:>8}개")

    print(f"\n출력 파일: {output_path}")
    print(f"파일 크기: {output_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
