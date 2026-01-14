#!/usr/bin/env python3
"""
Phase A: Company 정규화 파이프라인

Spec 7.6 기반 - 5단계 파이프라인:
1. 괄호 내 쉼표 보호
2. 역할 분리
3. 고유 회사명 추출
4. LLM 정규화 (수동/반자동)
5. company_aliases.json 저장

입력: ontology/input/meetings/RAN1/*.xlsx (59개 파일)
출력: ontology/intermediate/company_aliases.json
"""

import pandas as pd
from pathlib import Path
from collections import Counter
import json
import re
from typing import List, Tuple, Dict, Set

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "input" / "meetings" / "RAN1"
INTERMEDIATE_DIR = PROJECT_ROOT / "intermediate"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Step 1: 괄호 내 쉼표 보호
# ============================================================

def protect_parentheses(text: str) -> str:
    """괄호 안의 쉼표를 임시 문자로 대체"""
    result = []
    depth = 0
    for char in text:
        if char == '(':
            depth += 1
            result.append(char)
        elif char == ')':
            depth = max(0, depth - 1)  # 닫히지 않은 괄호 방어
            result.append(char)
        elif char == ',' and depth > 0:
            result.append('\x00')  # 임시 문자
        else:
            result.append(char)
    return ''.join(result)


def restore_commas(text: str) -> str:
    """임시 문자를 쉼표로 복원"""
    return text.replace('\x00', ',')


# ============================================================
# Step 2: 역할 분리
# ============================================================

# 역할 패턴 정의
ROLE_PATTERNS = [
    # "Moderator (Samsung)" 형태
    re.compile(r'^(Moderator|Rapporteur|Editor)\s*\((.+)\)$', re.IGNORECASE),
    # "Ad-Hoc Chair (Samsung)" 형태
    re.compile(r'^(Ad-?Hoc\s*Chair|Ad\s*Hoc\s*Chair)\s*\((.+)\)$', re.IGNORECASE),
    # "RAN1 Chair" 형태 (회사 없음)
    re.compile(r'^(RAN\d?\s*Chair|Chair|ETSI.*Chair|IEEE.*Chair)$', re.IGNORECASE),
]

# 역할만 있는 패턴 (회사 정보 없음)
ROLE_ONLY_PATTERN = re.compile(
    r'^(RAN\d?\s*Chair|Chair|ETSI\s+TC\s+ITS\s+Chair|IEEE\s+802\.11\s+Working\s+Group\s+Chair)$',
    re.IGNORECASE
)


def extract_role_and_company(text: str) -> Tuple[str, str]:
    """
    역할과 회사 분리

    Returns:
        (role, company) - 역할이 없으면 ("", company)
    """
    text = text.strip()

    # 역할만 있는 경우
    if ROLE_ONLY_PATTERN.match(text):
        return (text, "")  # 역할만, 회사 없음

    # 역할 + 회사 패턴
    for pattern in ROLE_PATTERNS[:2]:  # 처음 2개 패턴만 (회사 포함)
        match = pattern.match(text)
        if match:
            role = match.group(1).strip()
            company = match.group(2).strip()
            return (role, company)

    # 역할 없음
    return ("", text)


# ============================================================
# Step 3: 고유 회사명 추출
# ============================================================

def split_companies(source: str) -> List[str]:
    """Source를 개별 회사로 분리"""
    if pd.isna(source):
        return []

    source = str(source).strip()
    if not source:
        return []

    # 괄호 내 쉼표 보호
    protected = protect_parentheses(source)

    # 쉼표로 분리
    parts = protected.split(',')

    # 복원 및 정리
    companies = []
    for part in parts:
        company = restore_commas(part.strip())
        if company:
            # 역할 분리
            role, comp = extract_role_and_company(company)
            if comp:  # 회사명이 있는 경우만
                companies.append(comp)

    return companies


def load_all_companies(input_dir: Path) -> Tuple[List[str], Counter]:
    """모든 파일에서 회사명 추출"""
    files = sorted(input_dir.glob("*.xlsx"))
    print(f"파일 수: {len(files)}")

    all_companies = []

    for f in files:
        df = pd.read_excel(f)
        if 'Source' in df.columns:
            for source in df['Source'].dropna():
                companies = split_companies(source)
                all_companies.extend(companies)

    company_counts = Counter(all_companies)
    unique_companies = list(company_counts.keys())

    print(f"총 Source 레코드: {len(all_companies):,}건")
    print(f"고유 회사명: {len(unique_companies):,}개")

    return unique_companies, company_counts


# ============================================================
# Step 4: 정규화 규칙 (수동 + 패턴 기반)
# ============================================================

# 알려진 정규화 매핑 (대표명: [변형들])
KNOWN_ALIASES = {
    # 대기업 - 대소문자/약어
    "Samsung": ["Samsung", "Samsung Electronics", "SEC", "BEIJING SAMSUNG TELECOM R&D",
                "Samsung R&D Institute UK", "Samsung R&D Institute China - Beijing",
                "Samsung R&D Institute India - Bangalore", "Samsung R&D UK",
                "Samsung Research America", "Samsung R&D Institute China"],
    "Huawei": ["Huawei", "HW", "Huawei Technologies", "Huawei Technologies Co.", "Huawei Technologies Co. Ltd",
               "HUAWEI", "Huawei (editor)", "Huawei (Editor)", "Huawei Device", "Huawei Device Co."],
    "ZTE": ["ZTE", "ZTE Corporation", "ZTE Wistron", "ZTE Corp", "ZTE Microelectronics",
            "ZTE microelectronics", "ZTE MicroElectronics"],
    "Nokia": ["Nokia", "Nokia Networks", "Nokia Bell Labs", "Nokia Shanghai Bell",
              "Alcatel-Lucent Shanghai Bell", "Alcatel-Lucent", "Nokia Corporation", "NOKIA",
              "Nokia USA", "Nokia Solutions and Networks"],
    "Ericsson": ["Ericsson", "Ericsson LM", "Ericsson GmbH", "Ericsson (China)", "Ericsson Inc",
                 "ERICSSON", "Ericsson Hungary Ltd", "Nanjing Ericsson Panda Com Ltd"],
    "Qualcomm": ["Qualcomm Incorporated", "Qualcomm", "Qualcomm Inc.", "Qualcomm Technologies",
                 "Qualcomm Inc", "Qualcomm Austria RFFE GmbH", "QUALCOMM Incorporated",
                 "Qualcomm incorporated"],
    "Intel": ["Intel Corporation", "Intel", "Intel Corp", "Intel Corporation (UK) Ltd",
              "Intel Deutschland GmbH"],
    "Apple": ["Apple", "Apple Inc.", "Apple (UK) Limited", "Apple Inc", "Apple Switzerland AG",
              "Apple Computer Trading Co. Ltd", "APPLE"],
    "LG Electronics": ["LG Electronics", "LGE", "LG", "LG Innotek", "LG Electronics Inc",
                       "LG Display", "LG Uplus"],
    "NTT DOCOMO": ["NTT DOCOMO", "NTT DOCOMO, INC.", "NTT DOCOMO INC.", "DOCOMO",
                   "NTT DOCOMO, INC", "NTT DOCOMO INC", "NTT DOCOMO Inc", "NTT DOCOMO. INC",
                   "NTT DOCOMO. Inc", "NTT Docomo"],
    "vivo": ["vivo", "Vivo", "VIVO", "vivo Mobile Communication", "vivo Communication Technology",
             "vivo Mobile Communication Co."],
    "OPPO": ["OPPO", "Oppo", "OPPO Electronics", "OPPO Research Institute"],
    "MediaTek": ["MediaTek Inc.", "MediaTek", "Mediatek Inc.", "MTK", "MediaTek Inc",
                 "Mediatek Inc", "MediaTeK", "Mediatek", "MediaTek Korea Inc", "MediaTek Korea Inc.",
                 "MediaTek. Inc", "MediaTek. INC", "MediaTek (Chengdu) Inc", "MediaTek (Chengdu) Inc.",
                 "MediaTek Beijing Inc", "MediaTek Beijing Inc.", "MediaTek inc", "MediaTek inc.",
                 "Mediatek India Technology Pvt", "Mediatek India Technology Pvt.",
                 "nnMediaTek Inc", "nnMediaTek Inc."],
    "Sony": ["Sony", "Sony Corporation", "Sony Mobile Communications", "SONY", "Sony Group Corporation"],
    "Sharp": ["Sharp", "Sharp Corporation", "SHARP"],
    "Lenovo": ["Lenovo", "Lenovo Group", "Motorola Mobility", "Motorola", "Lenovo (Beijing) Ltd",
               "Motorola Mobility Germany GmbH", "MOTOROLA MOBILITY LLC", "Lenovo Group Limited"],
    "Xiaomi": ["Xiaomi", "Xiaomi Communications", "Xiaomi Inc", "XIAOMI", "Xiaomi Technology"],
    "InterDigital": ["InterDigital", "InterDigital, Inc.", "InterDigital Inc.", "InterDigital Inc",
                     "InterDigital, Inc", "InterDigital Communications", "INTERDIGITAL COMMUNICATIONS",
                     "Interdigital Asia LLC"],
    "CATT": ["CATT", "CATT/CATR", "CATR"],
    "CMCC": ["CMCC", "China Mobile", "China Mobile Communications", "China Mobile Com. Corporation"],
    "HiSilicon": ["HiSilicon", "HiSilicon Technologies", "Hisilicon", "HISILICON"],
    "Spreadtrum": ["Spreadtrum Communications", "Spreadtrum", "UNISOC", "Sanechips", "Sanechip", "SaneChip"],
    "NEC": ["NEC", "NEC Corporation", "NEC Corp"],
    "Panasonic": ["Panasonic", "Panasonic Corporation", "Panasonic Mobile Communications",
                  "PANASONIC", "Panasonic Holdings"],
    "Broadcom": ["Broadcom", "Broadcom Inc.", "Broadcom Limited", "BROADCOM LIMITED"],
    "Cisco": ["Cisco", "Cisco Systems", "CISCO"],
    "BlackBerry": ["BlackBerry", "Blackberry", "Research In Motion", "BLACKBERRY", "Blackberry QNX"],
    "ASUS": ["ASUSTEK", "ASUSTeK", "ASUSTek", "ASUS", "ASUSTEK COMPUTER (SHANGHAI)"],

    # 중국 기업
    "China Telecom": ["China Telecom", "China Telecom Corporation Ltd", "China Telecom Corp"],
    "China Unicom": ["China Unicom", "China Unicom Ltd"],
    "China Broadnet": ["China Broadnet", "China broadnet"],
    "CAICT": ["CAICT", "CAICT.", "China Academy of Information and Communications Technology"],
    "Datang": ["Datang", "Datang Mobile", "Datang Wireless"],
    "TD Tech": ["TD Tech", "TD Tech Ltd", "Chengdu TD Tech", "Chengdu TD TECH"],
    "FiberHome": ["FiberHome", "Fiberhome", "FiberHome Technologies"],
    "Potevio": ["Potevio", "Potevio Comm"],
    "Coolpad": ["Coolpad", "Coolpad Group"],
    "TCL": ["TCL", "TCL Communication", "TCL Communication Ltd"],
    "Honor": ["HONOR", "Honor", "Honor Device"],
    "FUTUREWEI": ["FUTUREWEI", "Futurewei", "Futurewei Technologies"],

    # 통신사
    "AT&T": ["AT&T", "AT & T", "AT&T Inc", "AT&T, NTT DOCOMO, INC"],
    "Verizon": ["Verizon", "Verizon Wireless", "Verizon Communications"],
    "T-Mobile": ["T-Mobile", "T-Mobile US", "T-Mobile USA", "T-Mobile USA Inc"],
    "Orange": ["Orange", "France Telecom", "Orange S.A."],
    "Deutsche Telekom": ["Deutsche Telekom", "DT", "Deutsche Telekom AG"],
    "SK Telecom": ["SK Telecom", "SKT", "SK telecom"],
    "KT": ["KT", "KT Corporation", "Korea Telecom", "KT Corp", "KT corp"],
    "KDDI": ["KDDI", "KDDI Corporation"],
    "SoftBank": ["SoftBank", "Softbank", "SoftBank Corp"],
    "Vodafone": ["Vodafone", "VODAFONE", "Vodafone Group Plc", "VODAFONE Group Plc"],
    "Telefonica": ["Telefonica", "Telefónica", "Telefonica S.A."],
    "Telecom Italia": ["Telecom Italia", "TELECOM ITALIA", "TIM"],
    "Dish Network": ["Dish Network", "DISH Network", "Dish network", "Dish", "DISH"],
    "FirstNet": ["FirstNet", "Firstnet"],
    "Telus": ["Telus", "TELUS"],
    "Rakuten": ["Rakuten", "Rakuten Mobile", "Rakuten Mobile Inc"],

    # 조직/기관
    "ETSI": ["ETSI", "ETSI MCC", "MCC", "ETSI (MCC)"],
    "3GPP": ["3GPP", "3GPP MCC"],
    "ITU": ["ITU", "ITU-R", "ITU-T"],
    "ETRI": ["ETRI", "Electronics and Telecommunications Research Institute"],
    "NIST": ["NIST", "National Institute of Standards and Technology"],
    "CEWiT": ["CEWiT", "CEWIT", "CeWiT", "CeWIT", "CeWit"],
    "CableLabs": ["CableLabs", "Cablelabs", "Cable Television Laboratories"],
    "BUPT": ["Beijing University of Posts and Telecommunications (BUPT)", "BUPT",
             "Beijing University of Posts and Telecommunications"],

    # 기타 주요 기업
    "Google": ["Google", "Google Inc", "Google LLC", "Google Korea LLC", "GOOGLE"],
    "Amazon": ["Amazon", "Amazon Web Services", "AWS", "Amazon.com"],
    "Microsoft": ["Microsoft", "Microsoft Corporation"],
    "Fujitsu": ["Fujitsu", "Fujitsu Limited", "FUJITSU"],
    "Mitsubishi": ["Mitsubishi Electric", "Mitsubishi Electric Corp", "MITSUBISHI ELECTRIC"],
    "Hitachi": ["Hitachi", "Hitachi Ltd."],
    "Toshiba": ["Toshiba", "Toshiba Corporation"],
    "Convida Wireless": ["Convida Wireless", "Convida wireless", "Convida Wireless LLC"],
    "Rohde & Schwarz": ["Rohde & Schwarz", "ROHDE & SCHWARZ", "R&S"],
    "National Instruments": ["National Instruments", "National instruments", "National Instruments Corp",
                            "NI", "National Instruments Corporation"],
    "Keysight": ["Keysight", "Keysight Technologies", "Keysight Technologies UK Ltd"],
    "Thales": ["THALES", "Thales", "Thales Group"],
    "ASTRI": ["ASTRI", "Astri", "Hong Kong Applied Science and Technology Research Institute"],
    "WILUS": ["WILUS", "WiLUS", "WILUS Inc", "Wilus Inc"],
    "AccelerComm": ["AccelerComm", "Accelercomm", "AccelerComm Ltd"],
    "NYU Wireless": ["NYU WIRELESS", "NYU Wireless", "New York University"],
}

# 문제가 있는 값 (분리 오류로 생긴 것)
INVALID_COMPANIES = {
    # 법인 접미사 (분리 오류)
    "INC.", "Inc.", "inc.", "Inc", "INC",
    "Ltd.", "Ltd", "LTD", "LTD.", "ltd",
    "Co.", "Co", "CO.", "co",
    "Corp.", "Corp", "Corporation", "CORP",
    "GmbH", "AG", "S.A.", "B.V.", "N.V.",
    "LLC", "L.L.C.", "llc",
    "Group", "Holdings", "Holding",
    "Pvt", "Pvt.", "Private",
    "Plc", "PLC", "plc",

    # Working Group (회사가 아님)
    "RAN1", "RAN2", "RAN3", "RAN4", "RAN5", "RAN",
    "SA", "SA1", "SA2", "SA3", "SA4", "SA5", "SA6",
    "CT", "CT1", "CT3", "CT4", "CT6",
    "TSG RAN", "TSG SA", "TSG CT",

    # 역할 (회사가 아님)
    "RAN1 Chair", "RAN1 chair", "RAN1 Chairman", "RAN1 chairman",
    "Chair", "Chairman", "Vice Chair", "Vice Chairman",

    # 기타 무효 값
    "etc", "etc.", "and others", "TBD", "N/A", "NA", "Unknown",
}


def normalize_company_name(name: str) -> str:
    """회사명 정규화"""
    name = name.strip()

    # 공백 정규화
    name = re.sub(r'\s+', ' ', name)

    # 후행 공백/마침표 제거
    name = name.rstrip('. ')

    return name


def is_valid_company(name: str) -> bool:
    """유효한 회사명인지 확인"""
    name = normalize_company_name(name)

    if not name:
        return False

    if name in INVALID_COMPANIES:
        return False

    # 너무 짧은 이름 (1-2글자)
    if len(name) <= 2:
        return False

    return True


def find_canonical_name(name: str) -> str:
    """정규화된 대표 이름 찾기"""
    name = normalize_company_name(name)

    # 알려진 별칭에서 검색
    for canonical, aliases in KNOWN_ALIASES.items():
        if name in aliases:
            return canonical
        # 대소문자 무시 검색
        for alias in aliases:
            if name.lower() == alias.lower():
                return canonical

    # 찾지 못하면 원본 반환
    return name


# ============================================================
# Step 5: 결과 저장
# ============================================================

def build_company_aliases(companies: List[str], counts: Counter) -> Dict[str, Dict]:
    """
    회사 별칭 사전 생성

    Returns:
        {
            "canonical_name": {
                "aliases": ["alias1", "alias2"]
            }
        }
    """
    # 정규화 적용
    canonical_mapping = {}  # original -> canonical

    for company in companies:
        if not is_valid_company(company):
            continue

        normalized = normalize_company_name(company)
        canonical = find_canonical_name(normalized)
        canonical_mapping[company] = canonical

    # 대표명별로 그룹화
    aliases_dict = {}

    for original, canonical in canonical_mapping.items():
        if canonical not in aliases_dict:
            aliases_dict[canonical] = {
                "aliases": set()
            }

        aliases_dict[canonical]["aliases"].add(original)

    # set -> list 변환 및 정렬
    for canonical in aliases_dict:
        aliases_dict[canonical]["aliases"] = sorted(aliases_dict[canonical]["aliases"])

    return aliases_dict


def save_results(aliases_dict: Dict, output_path: Path, raw_output_path: Path,
                 unique_companies: List[str], counts: Counter):
    """결과 저장"""

    # 1. 정규화 사전 저장
    # 정렬: aliases 수 기준
    sorted_aliases = dict(sorted(
        aliases_dict.items(),
        key=lambda x: len(x[1]["aliases"]),
        reverse=True
    ))

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_aliases, f, ensure_ascii=False, indent=2)

    print(f"\n정규화 사전 저장: {output_path}")
    print(f"  - 대표 회사 수: {len(sorted_aliases)}")

    # 2. 원본 회사 목록 저장 (디버깅용)
    raw_data = {
        "total_unique": len(unique_companies),
        "by_frequency": [
            {"name": name, "count": count}
            for name, count in counts.most_common()
        ]
    }

    with open(raw_output_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    print(f"원본 데이터 저장: {raw_output_path}")


def print_summary(aliases_dict: Dict):
    """결과 요약 출력"""
    print("\n" + "=" * 60)
    print("정규화 결과 요약")
    print("=" * 60)

    # 상위 30개 (aliases 수 기준)
    sorted_items = sorted(
        aliases_dict.items(),
        key=lambda x: len(x[1]["aliases"]),
        reverse=True
    )

    print("\n상위 30개 회사 (aliases 수 기준):")
    for i, (canonical, data) in enumerate(sorted_items[:30], 1):
        alias_count = len(data["aliases"])
        print(f"  {i:2}. {canonical:30} - {alias_count} aliases")

    # 통계
    total_aliases = sum(len(d["aliases"]) for d in aliases_dict.values())
    print(f"\n통계:")
    print(f"  - 정규화 전 고유 회사: {total_aliases:,}개")
    print(f"  - 정규화 후 대표 회사: {len(aliases_dict):,}개")
    print(f"  - 압축률: {(1 - len(aliases_dict)/total_aliases)*100:.1f}%")


def main():
    print("=" * 60)
    print("Phase A: Company 정규화")
    print("=" * 60)

    # Step 1-3: 회사명 추출
    unique_companies, counts = load_all_companies(INPUT_DIR)

    # Step 4: 정규화 적용
    aliases_dict = build_company_aliases(unique_companies, counts)

    # Step 5: 결과 저장
    output_path = INTERMEDIATE_DIR / "company_aliases.json"
    raw_output_path = INTERMEDIATE_DIR / "company_raw.json"
    save_results(aliases_dict, output_path, raw_output_path, unique_companies, counts)

    # 요약 출력
    print_summary(aliases_dict)

    print("\n" + "=" * 60)
    print("Phase A 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
