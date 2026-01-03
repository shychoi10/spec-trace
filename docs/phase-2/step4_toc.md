# Step-4: 역할 2 TOC 파싱 구현

## 목표

TOC 구조에 section_type, skip 여부, Virtual Numbering을 적용하여 `toc.yaml` 생성

**전략**:
- **입력**: `toc_raw.yaml` (python-docx에서 직접 추출된 TOC 구조)
- **처리**: LLM 기반 의미 파싱 (섹션 번호가 아닌 제목 의미로 판단)
- **출력**: `toc.yaml` (section_type, parent/children, skip 정보 추가)

---

## 입력 (Step-2 출력)

```yaml
# state.toc_raw (toc_raw.yaml)
- id: "1"
  title: "Opening of the meeting"
  depth: 1
  page: 5
- id: "1.1"
  title: "Call for IPR"
  depth: 2
  page: 5
- id: null              # ← 번호 없는 섹션
  title: "MIMO"
  depth: 3
  page: 14
```

> **핵심 변경점**:
> - 기존: Markdown에서 TOC 영역을 `extract_toc()`로 추출 → LLM 파싱
> - 신규: python-docx에서 Word 스타일(TOC 1/2/3)로 직접 추출한 `toc_raw` 사용

---

## 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| 입력 | `state.toc_raw` | python-docx에서 직접 추출 |
| 파싱 | LLM (Gemini) | section_type 의미 판단 |
| 스키마 | TOCSection (Pydantic) | 10개 필드 |
| 출력 | YAML | toc.yaml |

---

## TOCSection 스키마

| 필드 | 타입 | 설명 | 소스 |
|------|------|------|------|
| id | str | 섹션 번호 또는 가상 번호 (8.1v1) | toc_raw + Virtual Numbering |
| title | str | 섹션 제목 | toc_raw |
| depth | int | TOC 계층 깊이 (1=최상위) | toc_raw |
| parent | str? | 부모 섹션 ID | **LLM 계산** |
| children | list[str] | 자식 섹션 ID 목록 | **LLM 계산** |
| section_type | SectionType | 7종 + unknown | **LLM 판단** |
| type_reason | str | 판단 근거 | **LLM 생성** |
| skip | bool | 처리 제외 여부 | **LLM 판단** |
| skip_reason | str? | 제외 사유 | **LLM 생성** |
| virtual | bool | 가상 번호 여부 | toc_raw의 id가 null이면 true |

---

## 처리 흐름

```
state.toc_raw (python-docx 추출)
    ↓
Virtual Numbering 적용 (id: null → 8.1v1 등)
    ↓
call_llm_for_toc() - section_type, parent/children 판단
    ↓
TOCSection 스키마 검증
    ↓
save_yaml() → toc.yaml
```

### 상세 흐름

1. **Virtual Numbering**: `id: null`인 항목에 `{parent_id}v{sequence}` 형식 부여
2. **LLM 배치 호출** (Spec 4.2.8):
   - 30개씩 배치 분할
   - 배치 간 부모 section_type 전달 (상속 판단용)
   - 응답 검증: 요청 수 = 응답 수 확인
   - 누락 시 개별 재요청 (최대 2회)
3. **Parent/Children 계산**: depth 기반으로 계층 관계 생성
4. **Skip 판단**: section_type에 따라 skip 여부 결정
5. **검증 및 저장**: TOCSection 모델로 검증 후 YAML 저장
6. **처리 이력 저장**: `toc_processing.yaml`에 배치/재요청 이력 기록

---

## section_type 판단 기준

| 우선순위 | 키워드 | section_type |
|---------|--------|--------------|
| 1 | "Annex" | Annex |
| 2 | "Liaison" | LS |
| 3 | "Opening", "Closing", "Approval", "Highlights" | Procedural |
| 4 | "UE Features" | UE_Features |
| 5 | "Study", "SI" | Study |
| 6 | "Maintenance", "Pre-Rel" | Maintenance |
| 7 | "Release XX" (숫자 포함) | Release |

**상속 규칙**: 제목에 키워드가 없으면 상위 section_type 상속

---

## skip 처리 기준

| section_type | skip |
|--------------|------|
| Procedural | true |
| Annex A, D, E, F, G, H | true |
| Annex B, C-1, C-2 | false |
| 기타 | false |

---

## Virtual Numbering

번호 없는 하위 섹션 (`id: null`)은 가상 번호 부여:

```python
def apply_virtual_numbering(toc_raw: list[dict]) -> list[dict]:
    """
    id: null인 항목에 가상 번호 부여

    형식: {parent_id}v{sequence}
    예: 8.1 하위의 "MIMO" → 8.1v1, "MIMO (Alignment)" → 8.1v2
    """
```

### 예시

**입력 (toc_raw)**:
```yaml
- id: "8.1"
  title: "Maintenance on Rel-18 work items"
  depth: 2
  page: 14
- id: null
  title: "MIMO"
  depth: 3
  page: 14
- id: null
  title: "MIMO (Alignment/editorial)"
  depth: 3
  page: 15
```

**출력 (toc.yaml)**:
```yaml
- id: "8.1"
  title: "Maintenance on Rel-18 work items"
  depth: 2
  parent: "8"
  children: ["8.1v1", "8.1v2"]
  section_type: Maintenance
  type_reason: "상위 섹션(8)에서 상속"
  skip: false
  skip_reason: null
  virtual: false

- id: "8.1v1"
  title: "MIMO"
  depth: 3
  parent: "8.1"
  children: []
  section_type: Maintenance
  type_reason: "상위 섹션(8.1)에서 상속"
  skip: false
  skip_reason: null
  virtual: true

- id: "8.1v2"
  title: "MIMO (Alignment/editorial)"
  depth: 3
  parent: "8.1"
  children: []
  section_type: Maintenance
  type_reason: "상위 섹션(8.1)에서 상속"
  skip: false
  skip_reason: null
  virtual: true
```

---

## 구현 파일

| 파일 | 역할 | 변경사항 |
|------|------|----------|
| `src/utils/toc_utils.py` | Virtual Numbering, parent/children 계산 | **신규** |
| `src/utils/llm_client.py` | call_llm_for_toc() 함수 | 입력 형식 변경 |
| `src/prompts/toc_prompt.py` | TOC_PARSING_PROMPT | toc_raw 입력용 수정 |
| `src/models/toc.py` | TOCSection, SectionType | 기존 유지 |
| `src/pipeline/role_2_toc.py` | toc_node() | toc_raw 입력 처리 |

---

## LLM 프롬프트 (수정됨)

```python
TOC_PARSING_PROMPT = """You are a TOC classifier for 3GPP RAN1 meeting documents.

## Task
Classify each TOC section with section_type and determine skip status.

## Input Format (toc_raw from python-docx)
Each section has:
- id: section number (null if unnumbered)
- title: section title
- depth: hierarchy depth (1-3)
- page: page number

## Output Format (JSON Array)
For each section, add:
- section_type: Procedural|Maintenance|Release|Study|UE_Features|LS|Annex|unknown
- type_reason: 1-line explanation
- skip: true/false
- skip_reason: reason if skip=true

## section_type Priority Rules
1. "Annex" → Annex
2. "Liaison" → LS
3. "Opening", "Closing", "Approval", "Highlights" → Procedural
4. "UE Features" → UE_Features
5. "Study", "SI" → Study
6. "Maintenance", "Pre-Rel" → Maintenance
7. "Release XX" (with number) → Release
8. No keyword → inherit from parent

## skip Rules
- Procedural → skip: true
- Annex A, D, E, F, G, H → skip: true
- Annex B, C-1, C-2 → skip: false

## TOC Raw Data
{toc_raw_yaml}

## Instructions
1. Process each section
2. Determine section_type by title meaning (NOT section number)
3. Apply inheritance for sections without keywords
4. Return JSON array with section_type, type_reason, skip, skip_reason

Return ONLY JSON array, no explanation.
"""
```

---

## 테스트 체크리스트

```bash
# 1. toc_raw.yaml 확인
cat output/phase-2/langgraph-parser/converted/RAN1_120/toc_raw.yaml

# 2. Virtual Numbering 테스트
PYTHONPATH=scripts/phase-2/langgraph-parser .venv/bin/python -c "
from src.utils.toc_utils import apply_virtual_numbering
import yaml
with open('output/phase-2/langgraph-parser/converted/RAN1_120/toc_raw.yaml') as f:
    toc_raw = yaml.safe_load(f)
toc_numbered = apply_virtual_numbering(toc_raw)
null_count = sum(1 for t in toc_raw if t.get('id') is None)
print(f'Original null ids: {null_count}')
print(f'After numbering: {len([t for t in toc_numbered if t[\"virtual\"]])} virtual')
"

# 3. toc_node() 전체 테스트
PYTHONPATH=scripts/phase-2/langgraph-parser .venv/bin/python -c "
from src.pipeline.role_2_toc import toc_node
import yaml
with open('output/phase-2/langgraph-parser/converted/RAN1_120/toc_raw.yaml') as f:
    toc_raw = yaml.safe_load(f)
state = {
    'toc_raw': toc_raw,
    'output_dir': 'output/phase-2/langgraph-parser/results/RAN1_120',
}
result = toc_node(state)
print(f'TOC sections: {len(result[\"toc\"])}')
"

# 4. 출력 파일 확인
cat output/phase-2/langgraph-parser/results/RAN1_120/toc.yaml
```

---

## 완료 조건

1. toc_node() 함수가 **toc_raw 입력**으로 정상 동작
2. Virtual Numbering이 정확히 적용됨 (id: null → 8.1v1 등)
3. parent/children 관계가 정확히 계산됨
4. RAN1_120 TOC 파싱 성공 (약 30~50개 섹션)
5. toc.yaml 파일 생성됨
6. section_type 판단 정확도 90% 이상
7. skip 처리 정상 (Procedural → skip: true)

---

## 배치 처리 (Spec 4.2.8)

대용량 TOC 안정적 처리를 위한 배치 시스템:

| 파라미터 | 값 | 설명 |
|----------|------|------|
| BATCH_SIZE | 30 | 배치당 섹션 수 (LLM 컨텍스트 한계 고려) |
| MAX_RETRY | 2 | 누락 섹션 최대 재시도 횟수 |

### 처리 흐름

```
TOC 103개 섹션
    ↓
Batch 1 (30개) → LLM → 응답 검증
    ├── 30개 응답 → 정상
    └── 29개 응답 → 1개 누락 → 재요청
    ↓
Batch 2 (30개) → LLM → 응답 검증
    ↓
Batch 3 (30개) → LLM → 응답 검증
    ↓
Batch 4 (13개) → LLM → 응답 검증
    ↓
결과 병합 → toc.yaml
```

### 처리 이력 (_processing)

```yaml
# toc_processing.yaml
_processing:
  total_sections: 103
  batch_size: 30
  max_retry: 2
  log:
  - batch: 1
    requested: 30
    received: 29
    status: partial
  - batch: 1
    action: retry_triggered
    missing_count: 1
    missing_ids: [9.1.3]
  - section_id: 9.1.3
    action: retry_success
    attempt: 1
    result: Release
  - batch: 2
    requested: 30
    received: 30
    status: complete
```

### 핵심 원칙

| 원칙 | 적용 |
|------|------|
| True Agentic AI | 배치 크기는 인프라 파라미터, 의미 판단은 LLM |
| 검증 가능성 | 누락/재요청 이력 `_processing`에 기록 |
| 복구 전략 | 누락 섹션만 개별 재요청, 실패 시 `_error` 기록 |

---

## 테스트 결과

### RAN1_120
- **섹션 수**: 103개
- **배치**: 4개 (30+30+30+13)
- **재요청**: 1개 (9.1.3 → Release)
- **Unknown**: 0개 ✅

### RAN1_122
- **섹션 수**: 119개
- **배치**: 4개 (30+30+30+29)
- **재요청**: 1개 (8.5 → Maintenance)
- **Unknown**: 0개 ✅

---

## 다음 Step

- **Step-5**: 역할 3 섹션 라우터 구현

---

**Last Updated**: 2025-12-31
**Status**: ✅ Complete
