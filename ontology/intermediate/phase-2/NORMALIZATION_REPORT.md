# Company 정규화 결과 리포트

**생성일**: 2026-01-14
**데이터 범위**: RAN1#84 ~ RAN1#122b (59개 미팅)

---

## 1. 정규화 결과 요약

| 항목 | 수치 |
|------|------|
| 원본 Source 레코드 | 171,071건 |
| 분리 전 고유 Source | 4,644개 |
| 분리 후 고유 회사명 | 1,020개 |
| 정규화 후 대표 회사 | 779개 |
| 유의미한 회사 (10건+) | **222개** |

---

## 2. 빈도별 분포

| 빈도 | 회사 수 | 비율 |
|------|---------|------|
| 1,000건+ | 26개 | 3.3% |
| 100-999건 | 49개 | 6.3% |
| 10-99건 | 147개 | 18.9% |
| 1-9건 | 557개 | 71.5% |
| **합계** | **779개** | 100% |

---

## 3. 상위 30개 회사

| 순위 | 회사명 | 건수 | 별칭 수 |
|------|--------|------|---------|
| 1 | Nokia | 13,995 | 10 |
| 2 | Huawei | 13,694 | 5 |
| 3 | Ericsson | 13,100 | 9 |
| 4 | HiSilicon | 10,727 | 3 |
| 5 | ZTE | 9,529 | 8 |
| 6 | Qualcomm | 9,023 | 6 |
| 7 | Samsung | 8,560 | 4 |
| 8 | LG Electronics | 6,250 | 6 |
| 9 | Intel | 6,027 | 5 |
| 10 | CATT | 5,948 | 2 |
| 11 | NTT DOCOMO | 5,346 | 14 |
| 12 | vivo | 4,917 | 4 |
| 13 | Spreadtrum | 4,487 | 9 |
| 14 | MediaTek | 4,056 | 15 |
| 15 | Lenovo | 3,749 | 8 |
| 16 | OPPO | 3,623 | 2 |
| 17 | CMCC | 2,900 | 2 |
| 18 | InterDigital | 2,800 | 9 |
| 19 | Apple | 2,717 | 6 |
| 20 | Sony | 1,812 | 3 |
| 21 | Xiaomi | 1,667 | 6 |
| 22 | NEC | 1,649 | 3 |
| 23 | Sharp | 1,547 | 4 |
| 24 | Panasonic | 1,546 | 4 |
| 25 | AT&T | 1,459 | 3 |
| 26 | Fujitsu | 1,108 | 2 |
| 27 | ETRI | 962 | 1 |
| 28 | FUTUREWEI | 872 | 2 |
| 29 | China Telecom | 807 | 2 |
| 30 | ETSI | 650 | 4 |

---

## 4. 정규화 처리 유형

### 4.1 역할 분리 (779개 → 회사만 추출)
```
"Moderator (Samsung)" → Samsung
"Ad-Hoc Chair (Huawei)" → Huawei
"WI rapporteur (MediaTek)" → MediaTek
```

### 4.2 대소문자 통일
```
vivo / Vivo / VIVO → vivo
HUAWEI / Huawei → Huawei
```

### 4.3 법인 접미사 통합
```
Qualcomm Incorporated / Qualcomm Inc. / Qualcomm → Qualcomm
NTT DOCOMO, INC. / NTT DOCOMO INC / NTT DOCOMO → NTT DOCOMO
```

### 4.4 무효값 제거
```
INC / Inc / Ltd / Corp → 제거 (분리 오류)
RAN1 / SA2 → 제거 (Working Group)
```

---

## 5. 출력 파일

| 파일 | 내용 | 용도 |
|------|------|------|
| `company_aliases.json` | 전체 779개 회사 | 완전한 정규화 사전 |
| `company_aliases_significant.json` | 10건+ 222개 회사 | 실제 사용 권장 |
| `company_raw.json` | 원본 1,020개 회사 | 디버깅용 |

---

## 6. 한계 및 권장사항

### 6.1 저빈도 회사 (557개, 1-9건)
- 대부분 오타, 변형, 임시 값
- 개별 정규화 비용 > 효과
- **권장**: 10건 이상 회사만 사용

### 6.2 복합 회사명
```
"Fujitsu, MediaTek" → 두 회사의 공동 제출
"Apple, OPPO, Moderator (MediaTek)" → 복잡한 조합
```
- 현재: 전체 문자열로 처리
- **권장**: 향후 개별 회사로 분리 필요

### 6.3 LLM 정규화 미사용
- 현재: 규칙 기반 정규화만 사용
- LLM 비용 절감
- **결과**: 779개 (목표 ~300 대비 높음)
- **권장**: 10건+ 필터링으로 222개 달성

---

## 7. 사용 방법

```python
import json

# 정규화 사전 로드
with open("company_aliases_significant.json") as f:
    aliases = json.load(f)

# 역방향 조회 맵 생성
reverse_map = {}
for canonical, data in aliases.items():
    for alias in data["aliases"]:
        reverse_map[alias.lower()] = canonical

# 정규화 함수
def normalize(company_name):
    return reverse_map.get(company_name.lower(), company_name)

# 예시
normalize("Qualcomm Incorporated")  # → "Qualcomm"
normalize("NTT DOCOMO, INC.")       # → "NTT DOCOMO"
```

---

**Phase A 완료** ✅
