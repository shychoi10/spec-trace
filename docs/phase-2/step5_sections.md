# Step-5: 역할 3 섹션 처리 및 Item 추출

## 목표

Section Agent를 통해 각 섹션의 Leaf를 순회하고, SubSection Agent로 Item을 추출하여 `sections/*.yaml` 및 `annexes/*.yaml` 생성

**전략**:
- **입력**: `toc.yaml` (section_type 판단 완료), `document.md` (본문)
- **처리**: Section Agent → SubSection Agent 위임 (LLM 기반 Item 추출)
- **출력**: `sections/{section_id}/*.yaml`, `annexes/*.yaml`

---

## 아키텍처

### Agent 계층 구조

```
Orchestrator (role_3_sections.py)
    ├── TechnicalAgent (Maintenance, Release, Study, UE_Features)
    │   ├── MaintenanceSubAgent
    │   ├── ReleaseSubAgent
    │   ├── StudySubAgent
    │   └── UEFeaturesSubAgent
    ├── IncomingLSAgent (LS)
    │   └── LSSubAgent
    └── AnnexAgent (Annex B, C-1, C-2)
        └── AnnexSubAgent
```

### section_type → Agent 매핑 (Spec 5.1)

| section_type | Section Agent | SubSection Agent |
|--------------|---------------|------------------|
| Maintenance | TechnicalAgent | MaintenanceSubAgent |
| Release | TechnicalAgent | ReleaseSubAgent |
| Study | TechnicalAgent | StudySubAgent |
| UE_Features | TechnicalAgent | UEFeaturesSubAgent |
| LS | IncomingLSAgent | LSSubAgent |
| Annex (B, C-1, C-2) | AnnexAgent | AnnexSubAgent |
| Procedural | - (skip) | - |

---

## 처리 흐름

```
toc.yaml + document.md
    ↓
Depth 1 섹션 추출 (skip=False)
    ↓
각 섹션에 대해:
    1. section_type으로 Section Agent 선택
    2. Leaf 섹션 찾기 (children: [])
    3. 본문 내용 추출 (extract_section)
    4. SubSection Agent 호출 → Item 추출
    5. sections/{section_id}/{leaf_id}.yaml 저장
    ↓
Annex 처리 (B, C-1, C-2)
    ↓
annexes/{annex_id}.yaml 저장
```

---

## 핵심 구현

### 1. Leaf 본문 추출 (Spec 4.3.1)

```python
def extract_section(
    markdown_content: str,
    section_id: str,
    section_title: str,
    next_section_id: str | None,
    next_section_title: str | None,
) -> str:
    """
    Leaf 본문 추출

    1. 현재 섹션 제목 찾기 (번호 또는 제목으로)
    2. 다음 섹션 제목 찾기 (fallback: 제목으로 찾기)
    3. 두 제목 사이의 본문 추출
    """
```

**핵심 원칙** (Spec 4.3.1 Line 2527):
> "페이지 번호가 아닌 섹션 제목의 의미로 경계 판단 (일반화 원칙)"

### 2. Item 중복 방지 규칙 (Spec Line 3456-3508)

**핵심 원칙**: `1 Topic = 1 Item`

| 규칙 | 설명 |
|------|------|
| Topic 동일성 | Summary 제목, TDoc 연속성, 기술 주제로 판단 |
| 병합 | Summary #1 → Summary #2 (같은 Topic) = 1개 Item |
| 최종 Status만 | Monday Deferred → Thursday Agreed = Agreed |
| session_info | comeback: true, first_discussed, concluded로 히스토리 추적 |

**프롬프트 구현** (maintenance.py, release.py, study.py):
```python
# CRITICAL: Item Deduplication Rules (1 Topic = 1 Item)
## Core Principle
같은 Topic에 대한 여러 세션 논의는 반드시 **하나의 Item**으로 병합합니다.
절대 같은 Topic을 여러 Item으로 분리하지 마세요.
```

### 3. 하이라이트 색상별 마커 (Spec Line 1282-1285)

| Word 색상 | python-docx 속성 | 출력 마커 | 의미 |
|-----------|-----------------|----------|------|
| 초록 | BRIGHT_GREEN | `{.mark-green}` | Agreement |
| 진한 노랑 | DARK_YELLOW/YELLOW | `{.mark-yellow}` | Working Assumption |
| 청록 | TURQUOISE | `{.mark-turquoise}` | Post-meeting Action |
| 기타 | 기타 | `{.mark}` | 미분류 |

**docx_converter.py 구현**:
```python
if color == WD_COLOR_INDEX.BRIGHT_GREEN:
    text = f"[{text}]{{.mark-green}}"
elif color == WD_COLOR_INDEX.YELLOW or color == WD_COLOR_INDEX.DARK_YELLOW:
    text = f"[{text}]{{.mark-yellow}}"
elif color == WD_COLOR_INDEX.TURQUOISE:
    text = f"[{text}]{{.mark-turquoise}}"
else:
    text = f"[{text}]{{.mark}}"
```

---

## SubSection Agent 프롬프트

### 공통 구조

| 섹션 | 내용 |
|------|------|
| Role | 역할 설명 |
| Key Characteristics | 섹션 특성 |
| Item Boundary Detection Hints | 경계 판단 힌트 (규칙 아님) |
| **Item Deduplication Rules** | 중복 방지 규칙 (필수) |
| Marker to content.type Mapping | 색상별 마커 매핑 |
| Status Determination | 상태 결정 기준 |
| Required/Optional Fields | 필드 정의 |
| Output Format | JSON 배열 출력 |

### 섹션별 특성

| SubAgent | 주요 마커 | 특수 필드 |
|----------|----------|----------|
| MaintenanceSubAgent | [Agreement], **Decision:** | cr_info |
| ReleaseSubAgent | [Agreement], [Working Assumption], FFS: | - |
| StudySubAgent | [Agreement], [Conclusion], [Observation] | tr_info |
| UEFeaturesSubAgent | [Agreement:] | FG 정의 |
| LSSubAgent | **Decision:** | ls_in, ls_out |
| AnnexSubAgent | - | entries (표 파싱) |

---

## 출력 파일 구조

```
results/RAN1_120/
├── meeting_info.yaml
├── toc.yaml
├── sections/
│   ├── 5/
│   │   ├── _index.yaml
│   │   └── 5.yaml
│   ├── 6/
│   │   ├── _index.yaml
│   │   └── 6.yaml
│   ├── 8/
│   │   ├── _index.yaml
│   │   ├── 8.1v1.yaml
│   │   ├── 8.1v2.yaml
│   │   └── 8.2.yaml
│   └── 9/
│       ├── _index.yaml
│       ├── 9.1.1.yaml
│       ├── 9.1.2.yaml
│       └── ...
└── annexes/
    ├── annex_b.yaml
    ├── annex_c1.yaml
    └── annex_c2.yaml
```

### _index.yaml 예시

```yaml
section_id: "8"
title: "Rel-18 maintenance"
section_type: Maintenance
agent: TechnicalAgent

leaves:
  - leaf_id: "8.1v1"
    title: "MIMO"
    section_type: Maintenance
    subsection_agent: MaintenanceSubAgent
    status: completed
    item_count: 4
  - leaf_id: "8.2"
    title: "Rel-18 UE Features"
    section_type: UE_Features
    subsection_agent: UEFeaturesSubAgent
    status: completed
    item_count: 1

statistics:
  total_leaves: 2
  total_items: 5
  by_status:
    Agreed: 4
    Noted: 1

_processing:
  generated_at: "2025-12-31T10:00:00Z"
  status: completed
```

### Item 예시 (8.1v1.yaml)

```yaml
- id: RAN1_120_8.1v1_001
  context:
    meeting_id: RAN1_120
    section_id: '8'
    leaf_id: 8.1v1
    leaf_title: MIMO
    section_type: Maintenance
  topic:
    summary: RRC parameter for PRACH transmission in 2TA
  resolution:
    status: Agreed
    content:
    - type: agreement
      text: Introduce a new parameter to RACH-ConfigTwoTA-r18...
      marker: '[Agreement]{.mark}'
    - type: decision
      text: The LS is approved.
      marker: '**Decision:**'
  session_info:
    first_discussed: Monday
    concluded: Tuesday
    comeback: true
  input:
    moderator_summary: R1-2500200
```

---

## 구현 파일

| 파일 | 역할 |
|------|------|
| `src/pipeline/role_3_sections.py` | Orchestrator (섹션 처리 노드) |
| `src/agents/section_agents/technical.py` | TechnicalAgent |
| `src/agents/section_agents/incoming_ls.py` | IncomingLSAgent |
| `src/agents/section_agents/annex.py` | AnnexAgent |
| `src/agents/subsection_agents/maintenance.py` | MaintenanceSubAgent |
| `src/agents/subsection_agents/release.py` | ReleaseSubAgent |
| `src/agents/subsection_agents/study.py` | StudySubAgent |
| `src/agents/subsection_agents/ue_features.py` | UEFeaturesSubAgent |
| `src/agents/subsection_agents/ls.py` | LSSubAgent |
| `src/agents/subsection_agents/annex.py` | AnnexSubAgent |
| `src/prompts/subsection_prompts/*.py` | SubSection Agent 프롬프트 |
| `src/utils/markdown.py` | extract_section() 함수 |
| `src/utils/docx_converter.py` | 하이라이트 색상 마커 생성 |

---

## 테스트

```bash
# 전체 파이프라인 실행
cd scripts/phase-2/langgraph-parser
PYTHONPATH=. timeout 600 .venv/bin/python main.py --meeting RAN1_120

# 결과 확인
ls -la output/phase-2/langgraph-parser/results/RAN1_120/sections/

# Item 수 확인
for f in output/phase-2/langgraph-parser/results/RAN1_120/sections/*/*.yaml; do
  echo "$f: $(grep -c "^- id:" "$f" 2>/dev/null || echo 0)"
done

# 중복 방지 검증 (Section 8.1v1)
cat output/phase-2/langgraph-parser/results/RAN1_120/sections/8/8.1v1.yaml
# 기대: 4개 Item (이전: 13개 중복)
```

---

## 품질 검증

### 중복 방지 검증 (Section 8.1v1)

| 지표 | 수정 전 | 수정 후 | 기대값 |
|------|---------|---------|--------|
| Item 수 | 13개 | **4개** | ~4개 |
| 같은 Topic 중복 | 있음 | **없음** | 없음 |
| session_info.comeback | 일부 | **올바름** | 올바름 |

### 색상 마커 검증

```bash
# 색상별 마커 카운트
grep -c "{.mark-green}" output/phase-2/langgraph-parser/converted/RAN1_120/document.md
grep -c "{.mark-yellow}" output/phase-2/langgraph-parser/converted/RAN1_120/document.md
grep -c "{.mark-turquoise}" output/phase-2/langgraph-parser/converted/RAN1_120/document.md
grep -c "{.mark}" output/phase-2/langgraph-parser/converted/RAN1_120/document.md
```

---

## 완료 조건

1. ✅ TechnicalAgent, IncomingLSAgent, AnnexAgent 정상 동작
2. ✅ 모든 SubSection Agent 프롬프트에 중복 방지 규칙 포함
3. ✅ 하이라이트 색상별 마커 생성 (`.mark-green`, `.mark-yellow`, `.mark-turquoise`)
4. ✅ Section 8.1v1 Item 수: 13개 → 4개 (중복 제거)
5. ✅ sections/, annexes/ YAML 파일 정상 생성
6. ✅ _index.yaml에 통계 정보 포함

---

## Spec 준수 현황

| Spec 섹션 | 요구사항 | 구현 상태 |
|-----------|----------|----------|
| 4.0 Line 1282-1285 | 색상별 마커 | ✅ docx_converter.py |
| 4.3.1 Line 2527 | 제목 기반 경계 판단 | ✅ extract_section() |
| 5.1 | Section Agent 3종 | ✅ 구현됨 |
| 5.2 | SubSection Agent 6종 | ✅ 구현됨 |
| Line 3456-3508 | Item 중복 방지 | ✅ 프롬프트에 반영 |

---

## 다음 Step

- **Step-6**: 역할 4 검증 및 크로스체크 구현

---

**Last Updated**: 2025-12-31
**Status**: ✅ Complete
