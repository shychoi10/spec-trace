# Step-2: Maintenance Workflow 개선 계획

## 🚨 제1 원칙 (First Principles) - 반드시 준수

### 1. True Agentic AI
- ❌ Regex 패턴 매칭 금지
- ❌ 하드코딩된 if-else 규칙 금지
- ✅ 모든 텍스트 분석은 LLM 프롬프트로 수행

### 2. Content-based Naming
- ❌ Section 번호 사용 금지 (예: section7_agent.py)
- ✅ 콘텐츠 유형으로 명명 (예: maintenance_workflow.py)

### 3. 기존 코드 보호
- ❌ IncomingLS Workflow 수정 금지
- ❌ 기존 sub_agents 로직 변경 금지
- ✅ 모든 Section 처리는 독립적이어야 함

---

## 📊 Gap 분석: Ground Truth vs 현재 출력물

### Ground Truth Issue Block 구조

```markdown
### Issue: {Issue 제목}

**Origin**
- Type: `Internal_Maintenance` | `From_LS`
- Section: `7 — Pre-Rel-18 NR`
- Topic: `MIMO` | `DSS` | ...
- from_LS: R1-25xxxxx (if applicable)

**Draft / Discussion Tdocs**
- `R1-25xxxxx` – *Title* (Company) – `cr_draft`
- `R1-25xxxxx` – *Title* (Company) – `discussion`

**Moderator Summaries**
- `R1-25xxxxx` – *Summary #1 ...* – `summary`
- `R1-25xxxxx` – *Final summary ...* – `summary_final`

**LS 관련 Tdocs** (if applicable)
- `R1-25xxxxx` – *Draft LS ...* – `ls_draft`
- `R1-25xxxxx` – *Final LS ...* – `ls_final`

**Final CRs** (if applicable)
- `R1-25xxxxx` – *CR title*
  (Rel-17, **TS 38.214**, **WI-Name**, **CR0656**, **Cat F**) – `cr_final`

**Summary**
- 1-3줄 한국어 요약

**Decision / Agreement**
- 합의/결정 내용 (영문)
- Draft CR 상태 (approved/not pursued)

**CR / Spec 메타** (핵심)
- Release: **Rel-17** | **Rel-18**
- Spec: **TS 38.211** | **TS 38.212** | ...
- Work Item: `NR_MIMO_evo_DL_UL-Core` | ...
- CR: `CR0655` | ...
- Category: Cat A | Cat F

**Agenda Item**
- {Topic} (Section X)

**Issue Type**
- `SpecChange_FinalCR` | `SpecChange_AlignmentCR` | `Closed_Not_Pursued` |
  `Clarification_NoCR` | `Open_Inconclusive` | `LS_Reply_Issue`
```

### 현재 출력물의 문제점

| 항목 | Ground Truth | 현재 출력물 | Gap |
|------|-------------|------------|-----|
| **Origin** | Type, Section, Topic, from_LS | ❌ 없음 | 완전 누락 |
| **Tdoc 분류** | doc_type별 분류 (cr_draft, summary, ls_final 등) | 단순 나열 | doc_type 분류 없음 |
| **Summary** | 한국어, 기술적 맥락 | 기본적 | 품질 향상 필요 |
| **CR/Spec 메타** | Release, Spec, WI, CR#, Category | 일부만 | 불완전 |
| **Issue Type** | 6가지 분류 | ❌ 없음 | 완전 누락 |
| **Moderator Summary** | 별도 섹션 | ❌ 없음 | 누락 |
| **LS 관련 Tdocs** | 별도 섹션 | ❌ 없음 | 누락 |
| **Final CRs** | 별도 섹션 with 메타데이터 | 일부만 | 불완전 |

---

## 📁 디렉토리 구조 재설계

### 현재 구조
```
src/
├── agents/
│   ├── base_agent.py
│   ├── meta_section_agent.py
│   ├── incoming_ls_agent.py
│   ├── section_agents/
│   │   └── ls_agent.py
│   └── sub_agents/
│       ├── boundary_detector.py      # IncomingLS용
│       ├── decision_classifier.py    # IncomingLS용
│       ├── issue_formatter_agent.py
│       ├── issue_splitter_agent.py
│       ├── metadata_extractor.py
│       ├── section_overview_agent.py
│       ├── summary_generator.py
│       ├── tdoc_linker.py
│       ├── tdocs_extractor_agent.py
│       └── tdocs_selector_agent.py
├── models/
├── workflows/
└── utils/
```

### 개선된 구조
```
src/
├── agents/
│   ├── base_agent.py                 # 공통 기반 클래스
│   ├── meta_section_agent.py         # Section 타입 분류
│   │
│   ├── shared/                       # ✅ 신규: 공유 에이전트
│   │   ├── __init__.py
│   │   ├── tdocs_categorizer.py      # doc_type 분류 (cr_draft, summary 등)
│   │   ├── origin_extractor.py       # Origin 블록 추출
│   │   ├── cr_metadata_extractor.py  # CR/Spec 메타 추출
│   │   └── issue_type_classifier.py  # Issue Type 분류
│   │
│   ├── incoming_ls/                  # IncomingLS 전용 (기존 유지)
│   │   ├── __init__.py
│   │   ├── boundary_detector.py
│   │   ├── decision_classifier.py
│   │   ├── tdoc_linker.py
│   │   ├── summary_generator.py
│   │   └── ... (기타 기존 sub_agents)
│   │
│   └── maintenance/                  # ✅ 신규: Maintenance 전용
│       ├── __init__.py
│       ├── item_boundary_detector.py # Topic/Item 경계 감지
│       ├── moderator_summary_extractor.py
│       ├── ls_tdocs_extractor.py     # LS 관련 Tdoc 추출
│       ├── final_cr_extractor.py     # Final CR 추출
│       └── maintenance_formatter.py  # Ground Truth 형식 출력
│
├── models/
│   ├── issue.py                      # 기존 유지
│   ├── maintenance_item.py           # ✅ 확장 필요
│   ├── section_types.py
│   └── enums.py                      # ✅ IssueType enum 추가
│
├── workflows/
│   ├── incoming_ls_workflow.py       # ❌ 수정 금지
│   └── maintenance_workflow.py       # ✅ 대폭 개선 필요
│
└── utils/
```

---

## 🔧 핵심 개선 사항

### 1. Issue Type 분류 (신규)

```python
class IssueType(Enum):
    SPEC_CHANGE_FINAL_CR = "SpecChange_FinalCR"
    SPEC_CHANGE_ALIGNMENT_CR = "SpecChange_AlignmentCR"
    CLOSED_NOT_PURSUED = "Closed_Not_Pursued"
    CLARIFICATION_NO_CR = "Clarification_NoCR"
    OPEN_INCONCLUSIVE = "Open_Inconclusive"
    LS_REPLY_ISSUE = "LS_Reply_Issue"
    UE_FEATURE_DEFINITION = "UE_Feature_Definition"
    UE_FEATURE_CLARIFICATION = "UE_Feature_Clarification"
```

### 2. doc_type 분류 (신규)

```python
class DocType(Enum):
    CR_DRAFT = "cr_draft"
    CR_FINAL = "cr_final"
    SUMMARY = "summary"
    SUMMARY_FINAL = "summary_final"
    DISCUSSION = "discussion"
    LS_INCOMING = "ls_incoming"
    LS_DRAFT = "ls_draft"
    LS_FINAL = "ls_final"
    LS_REPLY_DRAFT = "ls_reply_draft"
    SESSION_NOTES = "session_notes"
```

### 3. Origin 블록 (신규)

```python
@dataclass
class IssueOrigin:
    type: str  # "Internal_Maintenance" | "From_LS"
    section: str  # "7 — Pre-Rel-18 NR"
    topic: Optional[str]  # "MIMO" | "DSS"
    from_ls: Optional[str]  # "R1-2500012" (if From_LS)
```

### 4. CR/Spec 메타데이터 (개선)

```python
@dataclass
class CRMetadata:
    release: str  # "Rel-17" | "Rel-18"
    spec: str  # "TS 38.211" | "TS 38.212" | ...
    work_item: Optional[str]  # "NR_MIMO_evo_DL_UL-Core"
    cr_id: Optional[str]  # "CR0655"
    category: Optional[str]  # "Cat A" | "Cat F"
```

---

## 📋 구현 순서

### Phase A: 모델 및 Enum 정의 (Day 1)

1. `models/enums.py` 확장
   - IssueType enum 추가
   - DocType enum 추가

2. `models/maintenance_item.py` 확장
   - IssueOrigin dataclass 추가
   - CRMetadata dataclass 개선
   - TdocWithType dataclass 추가

### Phase B: 공유 에이전트 구현 (Day 2-3)

1. `agents/shared/origin_extractor.py`
   - LLM으로 Origin 블록 추출

2. `agents/shared/tdocs_categorizer.py`
   - LLM으로 Tdoc doc_type 분류

3. `agents/shared/issue_type_classifier.py`
   - LLM으로 Issue Type 분류

4. `agents/shared/cr_metadata_extractor.py`
   - LLM으로 CR/Spec 메타 추출

### Phase C: Maintenance 전용 에이전트 (Day 4-5)

1. `agents/maintenance/item_boundary_detector.py`
   - Topic별 Item 경계 감지

2. `agents/maintenance/moderator_summary_extractor.py`
   - Moderator Summary 문서 추출

3. `agents/maintenance/final_cr_extractor.py`
   - Final CR 문서 및 메타데이터 추출

4. `agents/maintenance/maintenance_formatter.py`
   - Ground Truth 형식으로 마크다운 출력

### Phase D: 워크플로우 개선 (Day 6)

1. `workflows/maintenance_workflow.py` 개선
   - 새로운 에이전트 통합
   - Ground Truth 형식 출력

### Phase E: 테스트 및 검증 (Day 7)

1. RAN1 #120 3개 Maintenance Section 테스트
2. Ground Truth와 출력물 비교
3. IncomingLS 영향 없음 확인

---

## ✅ 체크리스트

### 제1 원칙 준수 확인
- [ ] 모든 텍스트 분석이 LLM 프롬프트로 수행되는가?
- [ ] Regex 패턴 매칭이 없는가?
- [ ] 하드코딩된 if-else 분류 규칙이 없는가?
- [ ] Section 번호 하드코딩이 없는가?
- [ ] 파일명/클래스명에 Section 번호가 없는가?

### 독립성 확인
- [ ] IncomingLS Workflow가 변경되지 않았는가?
- [ ] 기존 sub_agents가 수정되지 않았는가?
- [ ] 각 Section 처리가 독립적인가?

### Ground Truth 일치 확인
- [ ] Origin 블록이 출력되는가?
- [ ] Tdoc이 doc_type별로 분류되는가?
- [ ] Issue Type이 올바르게 분류되는가?
- [ ] CR/Spec 메타데이터가 완전한가?
- [ ] Moderator Summary가 별도 섹션으로 출력되는가?
- [ ] LS 관련 Tdocs가 별도 섹션으로 출력되는가?
- [ ] Final CRs가 메타데이터와 함께 출력되는가?

---

## 🎯 예상 결과

개선 후 출력물 예시:

```markdown
### Issue: DCI size alignment for UL grant (DSS)

**Origin**
- Type: `Internal_Maintenance`
- Section: `7 — Pre-Rel-18 NR`
- Topic: `DSS`

**Draft / Discussion Tdocs**
- `R1-2500143` – *Draft CR on DCI size alignment for UL grant*
  (ZTE, Sanechips) – `cr_draft`

**Moderator Summaries**
- `R1-2501488` – *FL summary of DCI size alignment for UL grant* – `summary`

**Summary**
UL grant 관련 **DCI size alignment** 문제에 대한 Draft CR 제안.
FL summary에서 스펙 변경이 필요한지 여부를 검토.

**Decision / Agreement**
- FL summary 결론:
  - **"Keep the current text as it is in the spec."**
- Draft CR `R1-2500143` → **not pursued**

**CR / Spec 메타**
- Spec: TS 38.2xx (DCI 관련)
- Final CR: 없음 (Spec 변경 없음)

**Agenda Item**
- DSS (Section 7)

**Issue Type**
- `Closed_Not_Pursued` (No spec change)
```

---

## 다음 단계

1. 사용자 승인 대기
2. Phase A 시작: 모델/Enum 정의
3. 순차적으로 Phase B → C → D → E 진행
