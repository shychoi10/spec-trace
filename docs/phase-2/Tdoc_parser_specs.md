## 1 개요

### 1.1 목적

**목표**

- 3GPP WG 회의록(Final Minutes Report)을 구조화된 데이터로 변환
- GraphDB 구축을 위한 중간 표현(YAML) 파일 생성
- 회의에서 논의된 기술 결정사항(Agreement, Conclusion, Decision)을 추적 가능한 형태로 추출

**입력**

| 항목 | 내용 |
| --- | --- |
| 형식 | .docx (Final Minutes Report) |
| 예시 | Final_Minutes_report_RAN1_120_v100.docx |
| 처리 단위 | 단일 문서 |

**출력**

| 항목 | 내용 |
| --- | --- |
| 형식 | YAML 파일 세트 |
| 용도 | GraphDB 로딩을 위한 중간 표현 (GraphDB 변환은 별도 처리) |

**출력 파일 구성**

| 파일 | 설명 |
| --- | --- |
| meeting_info.yaml | 회의 메타데이터 |
| toc.yaml | 문서 구조 (목차) |
| sections/{section_id}/*.yaml | 섹션별 Item 추출 결과 |
| annexes/*.yaml | 부록 데이터 |
| extraction_result.yaml | 통합 결과 + 검증 결과 |

---

### 1.2 범위

**지원 문서**

| 항목 | 내용 |
| --- | --- |
| 형식 | Final Minutes Report (.docx) |
| 특징 | 회의 종료 후 최종본 1개만 발행 (버전 관리 없음) |

**헤더 패턴**

```
Source: {source}
Title: Final Report of 3GPP TSG RAN WG{WG} #{number} v{version}
({location}, {date_range})
Document for: {purpose}

```

**지원 WG**

| 구분 | WG |
| --- | --- |
| 검증 완료 | RAN1 |

※ RAN2~5는 구조가 유사할 것으로 예상되나, 추후 검증 필요

**검증된 예시 문서**

| 문서 | 장소 | 일자 |
| --- | --- | --- |
| RAN1 #120 | Athens, Greece | 2025-02-17 ~ 2025-02-21 |
| RAN1 #122 | Bengaluru, India | 2025-08-25 ~ 2025-08-29 |

**범위 외**

- Draft Report (미승인 문서)
- TSG Plenary 회의록 (형식 다름)
- SA, CT 등 다른 TSG 문서
- 다른 형식의 3GPP 문서 (TS, TR, CR 원본 등)

---

### 1.3 핵심 원칙

**1. True Agentic AI (의미 기반 처리)**

| 항목 | 내용 |
| --- | --- |
| 정의 | 하드코딩 규칙 대신 LLM의 의미 이해 기반 처리 |
| 핵심 | LLM이 문맥과 의미를 파악하여 스스로 판단 |

| 적용 영역 | 설명 | 예시 |
| --- | --- | --- |
| 섹션 경계 판단 | 페이지 번호만으로 판단하지 않음, title 의미로 최종 판단 | page 힌트로 범위 축소 → LLM이 의미 기반 경계 확정 |
| Item 경계 판단 | 하나의 논의 흐름을 의미 단위로 구분 | Moderator Summary → Discussion → Agreement를 하나의 Item으로 |
| Type 판단 | 섹션 번호가 아닌 내용으로 Type 결정 | "Maintenance" vs "Release 19" vs "Study Item" |

---

**2. 일반화 (문서 독립성)**

| 항목 | 내용 |
| --- | --- |
| 정의 | 특정 문서에 귀속되지 않는 설계 |
| 핵심 | 새로운 회의록이 들어와도 동일 파이프라인으로 처리 가능 |

| 적용 영역 | 설명 | 예시 |
| --- | --- | --- |
| 섹션 번호 하드코딩 금지 | "Section 9 = Release 19" 같은 규칙 금지 | #120: Section 9 = Release 19, #122: Section 9 = UE Features (같은 번호, 다른 콘텐츠) |
| Type 기반 Agent 할당 | 섹션 번호가 아닌 Type으로 Agent 결정 | "Maintenance" → MaintenanceSubAgent |
| 구조 차이 대응 | 회의마다 다른 TOC 구조 수용 | UE Features가 8.2(Depth 2)일 수도, Section 9(Depth 1)일 수도 있음 |

---

**3. 이해 가능한 기준 (검증 가능성)**

| 항목 | 내용 |
| --- | --- |
| 정의 | LLM의 판단 결과를 사람이 검증할 수 있어야 함 |
| 핵심 | 판단 근거와 과정이 투명하게 기록됨 |

| 적용 영역 | 설명 | 예시 |
| --- | --- | --- |
| 결과 투명성 | 추출 결과에 근거 포함 | Item에 source_docs, marker 정보 포함 |
| Human Review | 불확실한 경우 사람에게 위임 | type: unknown → Human Review 트리거 |
| 크로스체크 | 자동 검증으로 오류 탐지 | 본문 CR vs Annex B 비교 |
| 에러 명시 | 실패 시 원인 기록 | _error 필드에 error_type, error_message |
| 원문 용어 보존 | 3GPP 원문 용어 그대로 사용 | Agreement, Conclusion, Moderator Summary 등 |

---

### 1.4 용어 정의

**3GPP 문서 용어**

| 용어 | 정의 | 예시 |
| --- | --- | --- |
| TDoc | Technical Document, 회의 문서 번호 | R1-2500138 |
| CR | Change Request, 스펙 변경 요청 | Draft CR on DCI size |
| LS | Liaison Statement, 그룹 간 통신 문서 | LS on UL 8Tx |
| WI | Work Item, 규격화 작업 항목 | NR_MIMO_evo_DL_UL-Core |
| SI | Study Item, 연구 항목 | Study on AI/ML for NR |
| TS | Technical Specification, 기술 규격 | TS 38.213 |
| TR | Technical Report, 기술 보고서 | TR 38.843 |

**회의록 구조 용어**

| 용어 | 정의 | 예시 |
| --- | --- | --- |
| Leaf Section | children이 없는 최말단 섹션 | 9.1.1 Beam management |
| Intro Content | 중간 노드(비-Leaf)에 있는 콘텐츠 | Section 9.1에 직접 있는 Agreement |
| Item | 하나의 완결된 논의 흐름 (트리거 → 토론 → 결론) | Moderator Summary + Discussion + Agreement |
| Moderator Summary | 모더레이터가 정리한 논의 요약 문서 | Summary #1 on beam management |
| FL Summary | Feature Lead가 정리한 요약 (Moderator Summary와 동일 취급) | FL summary #1 for AI/ML |

**파서 구조 용어**

| 용어 | 정의 | 참조 |
| --- | --- | --- |
| Orchestrator | 전체 파이프라인을 조율하는 중앙 컨트롤러 | 2.2장 |
| Section Agent | Depth 1 섹션을 담당하는 Agent | 5.1장 |
| SubSection Agent | Leaf에서 Item을 추출하는 Agent | 5.2장 |
| Depth | TOC 계층 깊이 (1=최상위, 2=하위, ...) | 4.2장 |
| section_type | 섹션의 콘텐츠 유형 | 3.3장 |

※ Agent 종류 및 section_type 상세는 해당 참조 장 확인

**결과 상태 용어**

| 용어 | 정의 | 문서 내 표기 |
| --- | --- | --- |
| Agreement | 합의된 사항 | [Agreement]{.mark} |
| Conclusion | 결론 (합의 실패 포함) | **Conclusion** |
| Decision | 결정 사항 | **Decision:** |
| Working Assumption | 잠정 합의 (추후 확정 필요) | [Agreement]{.mark} + "working assumption" |
| FFS | For Further Study, 추후 검토 필요 | FFS: whether/how to... |
| Observation | 관찰 결과 (Study Item에서 주로 사용) | Capture the following observations into TR |

※ 위 용어는 문서 내 마커이며, 파서 출력 상태값(Agreed, No_Consensus 등)은 3.3장 참조

**확장 원칙**

- 새로운 회의록에서 발견되는 용어는 Human Review 후 해당 분류에 추가
- 추가 시 "용어 / 정의 / 예시" 형식 유지

## 2 전체 아키텍처

### 2.0 개요

**목적**

| 항목 | 내용 |
| --- | --- |
| 정의 | 파이프라인 전체 구조와 구성 요소 간 관계 정의 |
| 범위 | 흐름, 역할, Agent 계층 (세부 구현은 4~8장) |

**핵심 원칙의 아키텍처 반영**

| 원칙 (1.3 참조) | 아키텍처 반영 |
| --- | --- |
| True Agentic AI | 각 역할 내부에서 LLM이 의미 기반 판단 |
| 일반화 | section_type 기반 Agent 할당 (섹션 번호 하드코딩 금지) |
| 검증 가능성 | 역할 4에서 크로스체크, 실패 시 Human Review 분기 |

---

### 2.1 파이프라인 흐름도

※ 화살표는 실행 순서를 나타냄. 데이터 의존 관계는 2.3 참조
※ Agent 종류 및 상세는 5장 참조

```
┌─────────────────────────────────────────────────────────────────┐
│                        입력 문서 (.docx)                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    역할 1: 메타데이터 추출                        │
│                         (순차 처리)                              │
│                              │                                   │
│                              ▼                                   │
│                     meeting_info.yaml                            │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│       역할 2: TOC 파싱 + section_type 판단 + Agent 할당          │
│                         (순차 처리)                              │
│                              │                                   │
│                              ▼                                   │
│                         toc.yaml                                 │
│                   (skip 여부 포함)                               │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      역할 3: 섹션 처리                            │
│                         (병렬 처리)                              │
│                                                                  │
│   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│   │ Technical │ │ IncomingLS│ │   Annex   │ │   skip    │      │
│   │   Agent   │ │   Agent   │ │   Agent   │ │(Procedural│      │
│   │           │ │           │ │           │ │ 등)       │      │
│   └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └───────────┘      │
│         │             │             │                           │
│         ▼             ▼             ▼                           │
│    SubSection    SubSection    SubSection                       │
│      Agent         Agent         Agent                          │
│         │             │             │                           │
│         ▼             ▼             ▼                           │
│    sections/     sections/     annexes/                         │
│    {id}/*.yaml   {id}/*.yaml   *.yaml                           │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   역할 4: 결과 취합 + 검증                        │
│                         (순차 처리)                              │
│                              │                                   │
│                              ▼                                   │
│                   extraction_result.yaml                         │
└─────────────────────────────────────────────────────────────────┘

```

**처리 방식 요약**

| 역할 | 처리 방식 | 출력 | 상세 |
| --- | --- | --- | --- |
| 역할 1 | 순차 | meeting_info.yaml | 4.1장 |
| 역할 2 | 순차 | toc.yaml | 4.2장 |
| 역할 3 | 병렬 (Section Agent 동시 실행) | sections/*.yaml, annexes/*.yaml | 4.3장 |
| 역할 4 | 순차 | extraction_result.yaml | 4.4장 |

※ 각 역할에서 실패 시 Human Review 분기 (상세: 7장 참조)

---

### 2.2 Orchestrator 역할

| 역할 | 설명 |
| --- | --- |
| 파이프라인 조율 | 역할 1 → 2 → 3 → 4 순서대로 실행 |
| 상태 관리 | 각 역할의 출력을 State에 저장, 필요한 역할에서 참조 |
| 병렬 실행 관리 | 역할 3에서 Section Agent 동시 실행 |
| skip 처리 | toc.yaml의 skip: true인 섹션은 Agent 호출 안 함 |
| 에러 처리 | 실패 감지 → Human Review 트리거 |
| 재처리 지원 | Human Review 완료 후 특정 역할부터 재실행 |
| 파일 경로 관리 | meeting_id 기반 출력 디렉토리 구성 |

**구현 방식**

| 구분 | 구현 | 판단 주체 |
| --- | --- | --- |
| Orchestrator | 코드 (LangGraph) | 흐름 제어만 |
| 각 역할 내부 | LLM 호출 | 의미 기반 판단 |

※ LangGraph State 및 구현 상세는 구현 단계에서 결정

---

### 2.3 역할 간 의존 관계

| 역할 | 입력 | 출력 | 참조하는 이전 출력 |
| --- | --- | --- | --- |
| 역할 1 | 원본 문서 헤더 | meeting_info.yaml | (없음) |
| 역할 2 | TOC 영역 | toc.yaml | (없음), 대용량 시 배치 처리 (4.2.8) |
| 역할 3 | 본문 섹션들 | sections/*.yaml, annexes/*.yaml | toc.yaml (skip 여부 포함) |
| 역할 4 | 모든 출력 파일 | extraction_result.yaml | meeting_info, toc, sections, annexes 전체 |

※ 파일 저장 경로의 meeting_id는 Orchestrator가 관리

**의존 관계 다이어그램**

```
역할 1 ──출력──▶ meeting_info.yaml ─────────────────┐
                                                    │
역할 2 ──출력──▶ toc.yaml (skip 정보 포함)          │
                      │                             │
                      ▼ (참조: skip 여부 확인)      │
역할 3 ──출력──▶ sections/*.yaml                    │
                  annexes/*.yaml                    │
                      │                             │
                      ▼ (참조)         (참조) ◀─────┘
역할 4 ──출력──▶ extraction_result.yaml

```

---

### 2.4 Agent 계층 구조

```
Orchestrator (코드)
    │
    ├── 역할 1: 메타데이터 추출 (LLM)
    │
    ├── 역할 2: TOC 파싱 + section_type 판단 + Agent 할당 (LLM)
    │
    ├── 역할 3: 섹션 처리
    │       │
    │       ├── skip 여부 확인 (Orchestrator)
    │       │       │
    │       │       ├── skip: true → 처리 안 함
    │       │       │
    │       │       └── skip: false → Section Agent 호출
    │       │               │
    │       │               └──▶ SubSection Agent 호출 (Leaf별)
    │       │
    │       └── [상세: 5장 참조]
    │
    └── 역할 4: 결과 취합 + 검증 (LLM + 코드)

```

**Agent 요약**

| 계층 | 역할 | 상세 |
| --- | --- | --- |
| Section Agent | Depth 1 섹션 담당, Leaf 탐색, SubSection Agent 호출 | 5.1장 |
| SubSection Agent | Leaf Section에서 Item 추출 | 5.2장 |

**Section Agent → SubSection Agent 호출 관계**

| Section Agent | 담당 section_type | 호출하는 SubSection Agent |
| --- | --- | --- |
| TechnicalAgent | Maintenance, Release, Study, UE_Features | section_type별 전용 SubAgent |
| IncomingLSAgent | LS | LSSubAgent |
| AnnexAgent | Annex (B, C-1, C-2) | AnnexSubAgent |

※ 호출 조건은 Leaf의 section_type에 따라 결정 (5.2장 참조)
※ 각 Agent 종류는 현재 기준이며, 확장 가능 (5.3장 참조)

---

### 2.5 처리 제외 대상

**skip 처리되는 섹션**

| 구분 | section_type | 예시 | 제외 이유 |
| --- | --- | --- | --- |
| Procedural 섹션 | Procedural | Opening, Approval of Agenda, Highlights, Closing | 추출 가치 없음 |
| 일부 Annex | Annex | A (A-1, A-2 포함), D, E, F, G, H | 크로스체크 불필요 |

**toc.yaml에서의 표시**

```yaml
# skip 처리 예시
- id: "1"
  title: "Opening of the meeting"
  section_type: Procedural
  skip: true
  skip_reason: "Procedural section"

- id: "annex_a1"
  title: "List of TDocs"
  section_type: Annex
  skip: true
  skip_reason: "Not in extraction scope"

# 처리 대상 예시
- id: "9"
  title: "Release 19"
  section_type: Release
  skip: false

```

※ 처리 제외 대상의 상세 기준은 3장 및 4.2장 참조

---

### 2.6 대용량 처리

| 항목 | 내용 |
| --- | --- |
| 적용 조건 | Leaf 콘텐츠가 컨텍스트 한도 초과 시 |
| 처리 방식 | Item 경계를 예측하여 청크 단위로 분할 처리 |
| 담당 | Section Agent |
| 상세 | 4.3.5장 참조 |

---

## 3 데이터 모델

### 3.0 개요

**목적**

| 구분 | 내용 |
| --- | --- |
| Primary | Agreement, Conclusion, Decision 추출 |
| Secondary | CR/LS 크로스체크 |

**핵심 원칙**

| 원칙 | 적용 |
| --- | --- |
| 최소 필드 | 꼭 필요한 정보만 |
| 검증 가능 | 원문 마커와 매핑 |
| 확장 가능 | 필요 시 추가 |

---

### 3.1 디렉토리 구조

```
/outputs/{meeting_id}/
│
├── meeting_info.yaml              ← 역할 1
├── toc.yaml                       ← 역할 2
├── extraction_result.yaml         ← 역할 4
├── media_index.yaml               ← 역할 4 (미디어 인덱스)
│
├── sections/                      ← 역할 3
│   └── {section_id}/
│       ├── _index.yaml
│       └── {leaf_id}.yaml
│
├── annexes/                       ← 역할 3 (크로스체크)
│   ├── annex_b.yaml               ← CR 목록
│   ├── annex_c1.yaml              ← Outgoing LS
│   └── annex_c2.yaml              ← Incoming LS
│
└── media/                         ← 전처리 (4.0)
    ├── image1.png
    └── ...

```

**ID 형식**

| ID | 형식 | 예시 |
| --- | --- | --- |
| meeting_id | {WG}_{number} | RAN1_120 |
| section_id | TOC 섹션 번호 | 8, 9, 10 |
| leaf_id | TOC 최말단 번호 | 9.1.1, 8.2 |

---

### 3.2 출력 파일 명세

| 파일 | 역할 | 상세 |
| --- | --- | --- |
| meeting_info.yaml | 회의 메타데이터 | 4.1장 |
| toc.yaml | 목차 + Agent 할당 | 4.2장 |
| sections/*.yaml | Item 추출 결과 | 4.3장 |
| annexes/*.yaml | 크로스체크용 | 4.3장 |
| media_index.yaml | 미디어 참조 인덱스 | 4.4장 |
| media/* | 추출된 이미지 파일 | 4.0장 |
| extraction_result.yaml | 통합 + 검증 | 4.4장 |

---

### 3.3 Item 스키마

**3.3.1 Item 정의**

| 항목 | 설명 |
| --- | --- |
| 정의 | 하나의 완결된 논의/처리 흐름 |
| 핵심 | Agreement, Conclusion, Decision 중 하나 이상 포함 |

**section_type 전체 목록**

| section_type | 처리 | 설명 |
| --- | --- | --- |
| Procedural | skip | 절차 섹션 (Opening, Closing 등) |
| Maintenance | Item 추출 | 기존 Release 유지보수 |
| Release | Item 추출 | 새 기능 개발 |
| Study | Item 추출 | 연구 단계 |
| UE_Features | Item 추출 | UE 기능 정의 |
| LS | Item 추출 | Incoming LS 처리 |
| Annex | 별도 스키마 | 부록 (3.5 참조) |

※ toc.yaml에서는 7종 전체 사용 (4.2 참조)

**Item 추출 대상 section_type**

| section_type | 단위 | 주요 결과 |
| --- | --- | --- |
| Maintenance | Moderator Summary | Agreement, CR |
| Release | Moderator Summary | Agreement |
| Study | Moderator Summary | Agreement, Conclusion |
| UE_Features | Feature 그룹 | Agreement |
| LS | 1 LS = 1 Item | Decision |

※ Procedural은 skip, Annex는 별도 스키마로 처리
※ Item 경계 판단 방법은 5장 SubSection Agent에서 정의

---

**3.3.2 필수 필드**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | string | Item 고유 식별자 |
| context | object | 맥락 정보 |
| resolution | object | 결과 정보 |

**id 형식**

```
{meeting_id}_{leaf_id}_{sequence}
예: RAN1_120_9.1.1_001
예 (가상 번호): RAN1_120_8.1v1_001

```

※ 가상 번호(virtual numbering)는 4.2 참조

**context**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| meeting_id | string | 회의 식별자 |
| section_id | string | Depth 1 섹션 번호 |
| leaf_id | string | Leaf 섹션 번호 |
| leaf_title | string | Leaf 섹션 제목 |
| section_type | string | 콘텐츠 유형 |

**context.section_type 값**

Item의 context.section_type에는 **Item 추출 대상만 포함**:

| 값 | 설명 |
| --- | --- |
| Maintenance | 기존 Release 유지보수 |
| Release | 새 기능 개발 |
| Study | 연구 단계 |
| UE_Features | UE 기능 정의 |
| LS | Incoming LS 처리 |

※ Procedural은 skip, Annex는 별도 스키마이므로 Item의 context.section_type에 포함되지 않음
※ toc.yaml의 section_type은 7종 전체 사용 (4.2 참조)

**resolution**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| status | string | 결과 상태 |
| content | array | 결과 내용 목록 |

**resolution.status 값**

| 값 | 설명 | 판단 힌트 (예시) |
| --- | --- | --- |
| Agreed | 합의됨 | [Agreement]{.mark} |
| Concluded | 결론 도출 | **Conclusion** |
| No_Consensus | 합의 실패 | "No consensus" |
| Deferred | 다음 회의로 연기 | "Deferred to next meeting", "postponed to RAN1#XXX” |
| Noted | 확인됨 | "noted" |
| Pending | 같은 회의 내 재논의 예정 | "Comeback on {요일}", "Come back on {요일}", "revisit on {요일}” |

※ 위 6개는 권장 값이며, LLM은 문서 맥락에 따라 새로운 status 생성 가능
※ 새로운 status 생성 시 판단 근거를 명확히 기록

**status 결정 우선순위**

content에 여러 type이 혼재할 때 status 결정 기준:

| 우선순위 | content.type 존재 | status |
| --- | --- | --- |
| 1 | agreement (확정적 합의) | Agreed |
| 2 | conclusion | Concluded |
| 3 | working_assumption만 | Agreed |
| 4 | decision만 (LS 등) | Noted |
| 5 | ffs만 | Pending |
| 6 | 명시적 "No consensus" | No_Consensus |

※ 여러 type 혼재 시 가장 높은 우선순위 기준으로 status 결정
※ 모든 type은 content 배열에 포함 (누락 없이)

**예시**

| content.type 목록 | status | 이유 |
| --- | --- | --- |
| [agreement, ffs] | Agreed | agreement가 ffs보다 우선 |
| [agreement, working_assumption] | Agreed | 둘 다 Agreed |
| [conclusion, observation] | Concluded | conclusion 우선 |
| [ffs] | Pending | ffs만 있음 |

**resolution.content 항목**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| type | string | 내용 유형 |
| text | string | 전체 내용 (원문) |
| marker | string | 문서 내 마커 |

**resolution.content 확장 필드 (CR 포함 시)**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| reason_for_change | string | - | 변경 사유 |
| summary_of_change | string | - | 변경 요약 |
| consequences_if_not_approved | string | - | 미승인 시 영향 |
| target_spec | string | - | 대상 스펙 |
| target_section | string | - | 대상 섹션 |
| text_proposal | string | - | TP 원문 (멀티라인) |
| endorsed_tdoc | string | - | TP 출처 TDoc |

※ 위 필드들은 Agreement가 CR/TP를 포함할 때 사용
※ Moderator Summary TDoc 내 TP 텍스트에서 추출

**resolution.content 예시 (CR 포함)**

yaml

`resolution:
  status: Agreed
  content:
    - type: agreement
      marker: "[Agreement]{.mark}"
      reason_for_change: "The condition of reporting CSI report for inference for BM-Case2 is unclear."
      summary_of_change: "Adding the condition of reporting CSI report for inference for BM-Case2."
      consequences_if_not_approved: "gNB and UE may have different understanding on the condition."
      target_spec: "38.214"
      target_section: "5.2.2.5"
      text_proposal: |
        **5.2.2.5 CSI reference resource definition**
        <omitted texts>
        For a *CSI-ReportConfig* configured with...
      endorsed_tdoc: "R1-2506453"`

**marker 필드 형식**

| 패턴 | 의미 | 예시 |
| --- | --- | --- |
| `{.mark-green}` | Agreement (초록 하이라이트) | `[Agreement]{.mark-green}` |
| `{.mark-yellow}` | Working Assumption (진한 노랑) | `[Working Assumption]{.mark-yellow}` |
| `{.mark-turquoise}` | Post-meeting Action (청록) | `[Post-120-AI/ML-01]{.mark-turquoise}` |
| `{.mark}` | 기타 하이라이트 (색상 미분류) | `[텍스트]{.mark}` |
| `**텍스트**` | 볼드 (하이라이트 아님) | `**Decision:**` |

※ marker 필드는 원문 형식 그대로 보존
※ 색상 정보로 Agreement vs Working Assumption 구분 가능

**content.type 값**

| 값 | 설명 | 판단 힌트 |
| --- | --- | --- |
| agreement | 합의 사항 | [Agreement]{.mark-green} |
| conclusion | 결론 | **Conclusion** |
| decision | 결정 | **Decision:** |
| working_assumption | 작업 가정 | [Working Assumption]{.mark-yellow} |
| observation | 관찰 사항 | [Observation] |
| ffs | 추가 검토 필요 | FFS: |
| post_meeting_action | 회의 후 작업 | [Post-120-...]{.mark-turquoise} |

※ 위는 권장 값이며, 새로운 유형은 LLM이 문서 마커를 기반으로 생성 가능
※ text에는 원문의 이미지 참조(`![](media/...)`)가 포함될 수 있음

※ 색상 마커({.mark-green} 등)로 type 판단 정확도 향상

---

**3.3.3 선택 필드**

**topic** (기술 논의)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| summary | string | 1줄 요약 |

**input** (기술 논의 및 LS)

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| moderator_summary | string 또는 array | △ | Summary TDoc 번호(들) |
| discussion_tdocs | array | ✓ | 논의에 사용된 TDoc 목록 |

※ △ = 기술 논의(Maintenance, Release, Study, UE_Features)에서 필수, LS에서는 해당 없음
※ `Relevant tdocs:` 또는 `Relevant Tdoc(s)` 섹션에 나열된 모든 TDoc 포함
※ LS Item에서도 discussion_tdocs는 필수 (Relevant TDocs 목록)

**discussion_tdocs 형식**

| 상황 | 형식 | 예시 |
| --- | --- | --- |
| 일반 논의 문서 | TDoc 번호 문자열 | `"R1-2500200"` |
| Revision 있는 문서 | 객체 형식 | `{tdoc_id: "R1-2501480", revision_of: "R1-2500832"}` |

**discussion_tdocs 항목 필드**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| tdoc_id | string | ✓ | TDoc 번호 |
| title | string | ✓ | TDoc 제목 |
| source | string | ✓ | 제출 회사 |
| tdoc_type | string | ✓ | TDoc 유형 |
| revision_of | string | - | 이전 버전 TDoc (있으면) |

**tdoc_type 값**

| 값 | 설명 | 식별 패턴 |
| --- | --- | --- |
| discussion | 일반 논의 문서 | 기본값 |
| draft_cr | CR 초안 | "Draft CR", "CR on" |
| draft_ls | LS 초안 | "Draft LS", "Reply LS" |
| summary | Moderator Summary | "Summary", "FL summary" |
| way_forward | Way Forward | "Way Forward", "WF" |

※ 원본 패턴: `[{TDoc}](link) {title} {source}` 에서 추출

**discussion_tdocs 예시**

```yaml
discussion_tdocs:
  - tdoc_id: "R1-2500200"
    title: "Discussion on beam management"
    source: "Huawei, HiSilicon"
    tdoc_type: discussion
  - tdoc_id: "R1-2500520"
    title: "Draft CR on DCI format"
    source: "Samsung"
    tdoc_type: draft_cr
  - tdoc_id: "R1-2501480"
    title: "Revised CR on beam management"
    source: "ZTE"
    tdoc_type: draft_cr
    revision_of: "R1-2500832"

```

**Revision 패턴 추출**

| 원문 패턴 | 추출 |
| --- | --- |
| `R1-2501480 (rev of R1-2500832)` | tdoc_id: R1-2501480, revision_of: R1-2500832 |
| `R1-2501461 (revision of R1-2500813)` | tdoc_id: R1-2501461, revision_of: R1-2500813 |

※ `Relevant tdocs:` 섹션에 나열된 모든 TDoc 포함
※ Discussion, Draft LS, Draft CR 등 모든 논의 문서 포함
※ `(rev of R1-xxx)` 패턴 발견 시 revision_of 필드 추가

**moderator_summary 형식**

| 상황 | 형식 | 예시 |
| --- | --- | --- |
| 단일 Summary | string | `"R1-2501410"` |
| 다중 Summary (같은 Topic) | array | `["R1-2501410", "R1-2501520"]` |

※ 같은 Topic에 대해 Summary #1, #2, #3이 있으면 배열로 모두 기록

**output** (결과물)

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| crs | array | △ | 승인된 CR 목록 (상세) |
| outgoing_ls | array | △ | 승인된 LS 목록 |
| endorsed_tdocs | array | - | endorse된 TDoc 목록 |

※ △ = 해당 결과가 있는 경우 필수

```yaml
output:
  crs:
    - tdoc_id: "R1-2501572"
      target_spec: "38.212"
      cr_number: "0210"
      category: "F"
      release: "Rel-18"
      work_item: "NR_MIMO_evo_DL_UL-Core"
      revision_of: null
  outgoing_ls:
    - tdoc_id: "R1-2501636"
      replies_to: "R1-2500012"
  endorsed_tdocs:
    - "R1-2501410"

```

**approved_tdocs 형식**

**output.crs 항목**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| tdoc_id | string | ✓ | CR TDoc 번호 |
| target_spec | string | ✓ | 대상 스펙 (예: "38.212") |
| cr_number | string | - | CR 번호 (Annex B에서 확인) |
| category | string | - | CR 카테고리 |
| release | string | ✓ | 대상 Release |
| work_item | string | - | Work Item 코드 |
| revision_of | string | - | 이전 CR TDoc |

**category 값**

| 값 | 설명 |
| --- | --- |
| F | Essential correction |
| A | Corresponds to a correction in an earlier release |
| B | Addition of feature |
| C | Functional modification of feature |
| D | Editorial modification |

**output.outgoing_ls 항목**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| tdoc_id | string | ✓ | LS TDoc 번호 |
| replies_to | string | - | 원본 Incoming LS (Reply인 경우) |

```yaml
approved_tdocs:
  - tdoc_id: "R1-2501636"
    type: "LS"              # Draft CR | LS | TP | Summary | WF
  - tdoc_id: "R1-2501572"
    type: "Draft CR"

```

**TDoc 타입 분류**

| 타입 | 설명 | 식별 패턴 |
| --- | --- | --- |
| Draft CR | Change Request 초안 | "Draft CR", "alignment CR" |
| LS | Liaison Statement | "LS", "Reply LS" |
| TP | Text Proposal | "TP in R1-xxx" |
| Summary | Moderator Summary | "Summary", "FL summary" |
| WF | Way Forward | "Way Forward" |

**승인 패턴**

| 패턴 | 의미 | 추출 대상 |
| --- | --- | --- |
| `[approved in R1-xxx]{.mark}` | 최종 승인 | approved_tdocs |
| `is agreed` | 합의됨 | approved_tdocs |
| `is endorsed` | 지지됨 | endorsed_tdocs |
| `Final LS is approved` | LS 승인 | approved_tdocs (type: LS) |
| `TP in R1-xxx is agreed` | TP 승인 | approved_tdocs (type: TP) |

**session_info** (세션 추적)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| first_discussed | string | 첫 논의 세션 (예: "Monday") |
| concluded | string | 결론 세션 (예: "Thursday") |
| comeback | boolean | 재논의 여부 |

**cr_info** (CR 승인 시)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| tdoc_id | string | CR TDoc 번호 |
| spec | string | 대상 스펙 |
| cr_number | string | CR 번호 |

**tr_info** (Study용)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| tr_number | string | TR 번호 (예: "TR 38.843") |
| update_tdoc | string | 업데이트 TDoc |

**ls_in** (LS 처리)

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| tdoc_id | string | ✓ | Incoming LS TDoc |
| title | string | ✓ | LS 제목 |
| source_wg | string | ✓ | 발신 WG (예: RAN2, RAN4, SA3) |
| source_company | string | - | 발신 회사 (있는 경우, 예: Samsung, ZTE) |

**원본 패턴**: `**[{TDoc}](link) {title} {source_wg}, {source_company}**`

- 쉼표가 있으면: 쉼표 앞 마지막 단어 = source_wg, 쉼표 뒤 = source_company
- 쉼표가 없으면: 마지막 단어 = source_wg, source_company = null

**ls_out** (LS 응답)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| action | string | 아래 값 중 하나 |
| reply_tdoc | string | 응답 TDoc 번호 |
| replies_to | string | 원본 Incoming LS TDoc 번호 |

**ls_out.action 값**

| 값 | 판단 키워드 | 설명 |
| --- | --- | --- |
| No_Action | "No action is needed", "No further action" | 추가 조치 불필요 |
| Note | "To be taken into account" | 참고로 반영 |
| Deferred | "To be discussed", "To be handled in" (현재 회의 agenda) | 현재 회의 내 처리 예정 |
| Response_Required | "response is needed", "response is necessary" | 회신 필요 |
| Deferred_Next_Meeting | "To be handled in next meeting" | 다음 회의로 연기 |
| Replied | 최종 LS 승인됨 | 회신 완료 |

**ls_out 예시**

```yaml
ls_out:
  action: Replied
  reply_tdoc: "R1-2501636"
  replies_to: "R1-2500012"      # 이 Reply가 답변하는 원본 LS

```

※ replies_to는 ls_in.tdoc_id와 동일한 값
※ Graph DB에서 REPLIES_TO 엣지 생성에 사용

**release_category** (LS 전용)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| release_category | string | LS 그룹 분류 (예: "Rel-19 AI/ML", "Rel-18 MIMO") |

**원본 패턴**:

- `*Rel-{버전} {주제}**`
- `*[Rel-{버전} {주제}]{.underline}**`

---

**handling** (LS 전용) - 후속 처리 정보

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| agenda_item | string | 처리 agenda (예: "8.1", "8.3") |
| topic | string | 주제 (선택, 예: "MIMO") |
| moderator | string | 담당자 이름 |
| moderator_company | string | 담당자 회사 |
| deferred_to | string | 연기된 회의 (예: "RAN1#122bis") |

**원본 패턴**:

- `"agenda item {번호} ({주제}) - {담당자} ({회사})"`
- `"agenda item {번호} - {담당자} ({회사})"`
- `"To be handled in next meeting {회의번호}"`

---

**LS 특수 플래그**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| cc_only | boolean | RAN1이 Cc로만 포함된 LS |
| received_during_week | boolean | 회의 주중에 수신된 LS |

**원본 패턴**:

- CC-only: "cc-ed" 또는 "cc-" 키워드 포함된 섹션 헤더
- 주중 수신: "during the week" 키워드 포함된 섹션 헤더

**_error** (에러 시)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| error_type | string | 에러 유형 |
| error_message | string | 메시지 |

※ _error 필드가 존재하면 에러, 없으면 정상
※ error_type 권장 값: parsing_failed, extraction_failed, type_unknown, validation_failed
※ 새로운 에러 유형은 LLM이 상황에 맞게 생성

**_processing** (처리 메타데이터)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| generated_at | string | 생성 시각 (ISO 8601) |
| status | string | 처리 상태 |
| chunked | boolean | 청킹 여부 (선택) |
| chunk_count | integer | 청크 수 (chunked=true 시) |
| batch_info | object | 배치 처리 정보 (선택, 역할 2에서 사용) |

※ status 권장 값: completed, partial, failed
※ 대용량 Leaf 처리 시 chunked=true, chunk_count로 청크 수 기록

**batch_info** (배치 처리 시, 역할 2 toc.yaml용)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| total_batches | integer | 총 배치 수 |
| retry_count | integer | 재요청 횟수 |
| retried_sections | array | 재요청된 섹션 ID 목록 |

**batch_info 예시**

```yaml
_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed
  batch_info:
    total_batches: 4
    retry_count: 2
    retried_sections: ["9.1.5", "10.2.3"]

```

※ batch_info는 역할 2 TOC 파싱에서 배치 처리 시 기록
※ 4.2.8 "대용량 TOC 처리" 참조

**_warning** (경고 시)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| type | string | 경고 유형 |
| message | string | 메시지 |
| context | object | 추가 컨텍스트 (선택) |

※ _warning은 처리는 계속되나 주의가 필요한 경우 기록
※ _error와 달리 파이프라인이 중단되지 않음
※ warning_type 권장 값: unknown_section_type, low_confidence, ambiguous_boundary, normalization_failed

**_warning 예시**

```yaml
_warning:
  type: unknown_section_type
  message: "section_type 판단 실패, 기본값 사용"
  context:
    original_title: "New Agenda Item"
    assigned_type: Release

```

**media_refs** (미디어 참조)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| type | string | 미디어 유형 |
| ref | string | 파일 경로 또는 위치 식별자 |
| label | string | Figure/Table 레이블 (선택) |

**media_refs.type 값**

| 값 | 설명 |
| --- | --- |
| image | 이미지 파일 참조 |
| table | 본문 내 테이블 |

**media_refs 예시**

```yaml
media_refs:
  - type: image
    ref: "media/image5.png"
    label: "Figure 3"
  - type: table
    ref: "inline"
    label: "Table 1"

```

※ media_refs는 resolution.content.text에 이미지(`![](media/...)`) 또는 테이블이 포함된 경우 기록
※ 미디어가 없는 Item에서는 생략

---

**3.3.4 Item 예시**

**기술 논의 (Release)**

```yaml
id: RAN1_120_9.1.2_001

context:
  meeting_id: RAN1_120
  section_id: "9"
  leaf_id: "9.1.2"
  leaf_title: "Specification support for positioning accuracy enhancement"
  section_type: Release

topic:
  summary: "AI/ML positioning Case 3b 파라미터 결정"

input:
  moderator_summary: "R1-2501410"
  discussion_tdocs:
    - "R1-2500195"
    - "R1-2500196"
    - tdoc_id: "R1-2501480"
      revision_of: "R1-2500832"

output:
  approved_tdocs:
    - tdoc_id: "R1-2501532"
      type: "Draft CR"
  endorsed_tdocs:
    - "R1-2501410"

resolution:
  status: Agreed
  content:
    - type: agreement
      text: "For Case 3b, support k = {0...5}"
      marker: "[Agreement]{.mark}"
    - type: agreement
      text: "For Case 3b, support Nt' = {8, 16, 24}"
      marker: "[Agreement]{.mark}"

session_info:
  first_discussed: "Tuesday"
  concluded: "Thursday"
  comeback: false

```

**CR 승인 (Maintenance, 가상 번호)**

```yaml
id: RAN1_120_8.1v1_003

context:
  meeting_id: RAN1_120
  section_id: "8"
  leaf_id: "8.1v1"
  leaf_title: "MIMO"
  section_type: Maintenance

topic:
  summary: "DCI format 0_3 dormancy 정정"

input:
  moderator_summary: "R1-2501500"
  discussion_tdocs:
    - tdoc_id: "R1-2500200"
      title: "Discussion on DCI format 0_3"
      source: "Huawei, HiSilicon"
      tdoc_type: discussion
    - tdoc_id: "R1-2501532"
      title: "Draft CR on DCI dormancy"
      source: "Samsung"
      tdoc_type: draft_cr

resolution:
  status: Agreed
  content:
    - type: agreement
      marker: "[Agreement]{.mark}"
      reason_for_change: "Clarification needed for dormancy indication"
      summary_of_change: "Add NOTE regarding DCI format 0_3 dormancy"
      consequences_if_not_approved: "Ambiguity in UE behavior"
      target_spec: "38.212"
      target_section: "7.3.1.1.2"
      text_proposal: |
        Add the following NOTE after Table 7.3.1.1.2-36:
        NOTE: When the UE receives...
      endorsed_tdoc: "R1-2501532"

output:
  crs:
    - tdoc_id: "R1-2501572"
      target_spec: "38.212"
      cr_number: "0210"
      category: "F"
      release: "Rel-18"
      work_item: "NR_MIMO_evo_DL_UL-Core"
  endorsed_tdocs:
    - "R1-2501532"

session_info:
  first_discussed: "Tuesday"
  concluded: "Thursday"
  comeback: false

```

**LS 처리**

```yaml
id: RAN1_120_5_001

context:
  meeting_id: RAN1_120
  section_id: "5"
  leaf_id: "5"
  leaf_title: "Incoming Liaison Statements"
  section_type: LS

release_category: "Rel-18 MIMO"

ls_in:
  tdoc_id: "R1-2500012"
  title: "LS on UL 8Tx"
  source_wg: "RAN2"
  source_company: "Samsung"

input:
  discussion_tdocs:
    - "R1-2500195"   # Discussion on LS from RAN2 on UL 8Tx
    - "R1-2500196"   # Draft reply LS on UL 8Tx
    - "R1-2500248"   # Draft reply LS to RAN2 on UL 8Tx

handling:
  agenda_item: "8.1"
  topic: "MIMO"
  moderator: "Sa"
  moderator_company: "Samsung"

ls_out:
  action: Response_Required
  reply_tdoc: null
  replies_to: "R1-2500012"

resolution:
  status: Deferred
  content:
    - type: decision
      text: "RAN2 is requesting RAN1 input to finalize the MAC specification support of UL 8TX. RAN1 response is necessary and to be handled in agenda item 8.1 (MIMO) - Sa (Samsung)."
      marker: "**Decision:**"
```

**Study (observation, ffs 포함)**

```yaml
id: RAN1_120_9.7.1_001

context:
  meeting_id: RAN1_120
  section_id: "9"
  leaf_id: "9.7.1"
  leaf_title: "ISAC deployment scenarios"
  section_type: Study

topic:
  summary: "ISAC 채널 모델링 calibration 접근법"

input:
  moderator_summary: "R1-2501076"

resolution:
  status: Concluded
  content:
    - type: conclusion
      text: "For ISAC channel modelling calibration, RAN1 considers both large-scale and full-scale calibration"
      marker: "[Conclusion]"
    - type: observation
      text: "Large scale parameters do not include fast fading"
      marker: "[Observation]"
    - type: ffs
      text: "FFS: additional calibration for the combined channel"
      marker: "FFS:"

tr_info:
  tr_number: "TR 38.901"
  update_tdoc: "R1-2501640"

session_info:
  first_discussed: "Wednesday"
  concluded: "Thursday"
  comeback: false

```

---

### 3.4 Media Index 스키마

**목적**: 문서 내 이미지/테이블과 Item 간 연결 관계 추적

**media_index.yaml 구조**

```yaml
# media_index.yaml
meeting_id: RAN1_120

images:
  - id: "img_001"
    path: "media/image1.png"
    referenced_in:
      - item_id: "RAN1_120_9.1.1_001"
        leaf_id: "9.1.1"
    label: "Figure 3"

tables:
  - id: "tbl_001"
    referenced_in:
      - item_id: "RAN1_120_9.1.2_002"
        leaf_id: "9.1.2"
    label: "Table 1"

statistics:
  total_images: 15
  total_tables: 8
  items_with_media: 12

```

**images 항목**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | string | 이미지 식별자 (img_001, img_002, ...) |
| path | string | 파일 경로 (media/image1.png) |
| referenced_in | array | 참조하는 Item 목록 |
| label | string | Figure 레이블 (선택) |

**tables 항목**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | string | 테이블 식별자 (tbl_001, tbl_002, ...) |
| referenced_in | array | 포함된 Item 목록 |
| label | string | Table 레이블 (선택) |

**referenced_in 항목**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| item_id | string | Item 식별자 |
| leaf_id | string | Leaf 섹션 번호 |

**statistics**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| total_images | integer | 총 이미지 수 |
| total_tables | integer | 총 테이블 수 |
| items_with_media | integer | 미디어 포함 Item 수 |

※ media_index.yaml은 역할 4에서 생성
※ Item의 media_refs와 양방향 참조 관계

---

### 3.5 Annex 스키마

**목적**: 본문 추출 결과 크로스체크

**대상**: B (CR), C-1 (Outgoing LS), C-2 (Incoming LS)

※ 다른 Annex (A, D, E, F, G, H)는 추출 안 함 (2.5장 참조)

**Annex B (CR 목록)**

```yaml
annex_id: annex_b
title: "List of CRs agreed at RAN1 #120"
entries:
  - tdoc_id: "R1-2501501"
    title: "Correction on transition time..."
    source: "vivo, ASUSTeK"
    release: "Rel-18"
    spec: "38.213"
    version: "18.5.0"
    work_item: "NR_ext_to_71GHz-Core"
    cr_number: "0693"
    revision: ""
    category: "F"

```

**entries 필드 상세**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| tdoc_id | string | ✓ | TDoc 번호 |
| title | string | ✓ | CR 제목 |
| source | string | ✓ | 제출 회사 |
| release | string |  | 릴리즈 (예: "Rel-18") |
| spec | string | ✓ | 대상 스펙 (예: "38.213") |
| version | string |  | 스펙 버전 (예: "18.5.0") |
| work_item | string |  | Work Item 코드 |
| cr_number | string | ✓ | CR 번호 |
| revision | string |  | Revision 번호 |
| category | string |  | CR 카테고리 (F, A, B, C, D) |

※ 필수 필드만 있어도 크로스체크 가능, 나머지는 선택

※ 필수 필드(tdoc_id, title, source, spec, cr_number)는 RAN1 #120, #122에서 검증됨
※ 선택 필드(release, version, work_item, revision, category)는 RAN1 #120, #122 기준이며, 다른 회의/WG 검증 후 확정 필요

**Annex C-1 (Outgoing LS)**

```yaml
annex_id: annex_c1
title: "List of Outgoing LSs"
entries:
  - tdoc_id: "R1-2501479"
    title: "Reply LS on..."
    to: "RAN2"

```

**Annex C-2 (Incoming LS)**

```yaml
annex_id: annex_c2
title: "List of Incoming LSs"
entries:
  - tdoc_id: "R1-2500012"
    title: "LS on UL 8Tx"
    source: "RAN2"
    handled_in: "8.1"  # 선택, 처리된 agenda item

```

※ handled_in은 선택 필드이며, 7.2.3 크로스체크 시 참고용으로 활용

---

### 3.6 TDoc 참조 패턴

| 유형 | 패턴 | 의미 |
| --- | --- | --- |
| 기본 | `[R1-XXXXXXX](...)` | 일반 참조 |
| 승인 | `[[R1-XXXXXXX]{.mark}](...)` | 승인 문서 |
| 볼드 | `[**R1-XXXXXXX**](...)` | Summary 등 |
| Revision | `(rev of [R1-XXXXXXX])` | 수정 버전 |
| Approved in | `[approved in R1-XXX]` | 최종 승인 |

---

**TDoc 번호 정규화**

**목적**: 크로스체크 시 본문과 Annex 간 TDoc 번호 매칭을 위한 정규화

**정규화 규칙**

| 단계 | 처리 | 예시 |
| --- | --- | --- |
| 1 | Markdown 링크 문법 제거 | `[R1-2501501](...)` → `R1-2501501` |
| 2 | 대괄호 제거 | `[R1-2501501]` → `R1-2501501` |
| 3 | 서식 마커 제거 | `{.mark}`, `**`, `__` 제거 |
| 4 | revision 정보 제거 | `(rev of R1-xxx)` 제거 |
| 5 | 공백 trim | 앞뒤 공백 제거 |
| 6 | 대문자 유지 | `r1-2501501` → `R1-2501501` |

**변환 예시**

| 원문 형태 | 정규화 결과 |
| --- | --- |
| `R1-2501501` | R1-2501501 |
| `[R1-2501501]` | R1-2501501 |
| `[R1-2501501](../Docs/R1-2501501.zip)` | R1-2501501 |
| `[[R1-2501501]{.mark}](../Docs/R1-2501501.zip)` | R1-2501501 |
| `[**R1-2501501**](../Docs/R1-2501501.zip)` | R1-2501501 |
| `R1-2501564 (rev of R1-2501123)` | R1-2501564 |
| `r1-2501501` | R1-2501501 |

**WG별 TDoc 패턴**

| WG | 패턴 | 정규식 |
| --- | --- | --- |
| RAN1 | R1-XXXXXXX | `R1-\\d{7}` |
| RAN2 | R2-XXXXXXX | `R2-\\d{7}` |
| RAN3 | R3-XXXXXXX | `R3-\\d{7}` |
| RAN4 | R4-XXXXXXX | `R4-\\d{7}` |
| SA2 | S2-XXXXXXX | `S2-\\d{7}` |

**크로스체크 적용**

| 비교 대상 | 정규화 적용 |
| --- | --- |
| 본문 cr_info.tdoc_id | 정규화 후 비교 |
| Annex B entries[].tdoc_id | 정규화 후 비교 |
| 본문 ls_out.reply_tdoc | 정규화 후 비교 |
| Annex C-1 entries[].tdoc_id | 정규화 후 비교 |

※ 정규화된 TDoc 번호로 비교, 원본 형태는 marker 필드에 보존
※ 정규화 실패 시 원문 그대로 사용 + _warning 기록

---

**TDoc 역할 분류**

| 역할 | 설명 | 식별 패턴 |
| --- | --- | --- |
| incoming_ls | 수신 LS | Section 5, "LS on", "Reply LS from" |
| discussion | 논의 기고문 | `Relevant tdocs:` 목록, "Discussion on" |
| draft_ls | LS 초안 | "Draft reply LS", "Draft LS" |
| draft_cr | CR 초안 | "Draft CR", "alignment CR" |
| moderator_summary | 정리 문서 | "Summary #N", "FL summary", "Moderator summary" |
| final_ls | 최종 LS | `[approved in R1-xxx]{.mark}`, "Final LS" |
| final_cr | 최종 CR | "Final CR in", "is agreed for CR" |
| session_notes | 세션 노트 | "Session notes" |

**TDoc 관계 (Edges)**

| 관계 | 설명 | 패턴 |
| --- | --- | --- |
| revision_of | 수정본 | `(rev of R1-xxx)` |
| replies_to | LS 답신 | "Reply LS to R1-xxx" |
| draft_of | 초안→최종 | "Final LS is approved in R1-xxx" |
| merged_into | 병합 | "merged into R1-xxx" |

**TDoc 상태**

| 상태 | 마커/패턴 |
| --- | --- |
| agreed | `[Agreement]{.mark}`, "is agreed" |
| endorsed | "is endorsed", `[endorsed]{.mark}` |
| approved | "is approved", `{.mark-green}` |
| noted | "is noted" |
| not_pursued | "not pursued", "no consensus" |
| withdrawn | "is withdrawn" |
| comeback | "Comeback on {요일}" |

---

### 3.7 마커 패턴

**결과 마커**

| 마커 | 패턴 | 색상 | 추출 대상 |
| --- | --- | --- | --- |
| Agreement | `[Agreement]{.mark-green}` | 초록 | content |
| Agreement (콜론 형태) | `[Agreement:]` | - | content |
| Working Assumption | `[Working Assumption]{.mark-yellow}` | 진한 노랑 | content |
| Post-meeting Action | `[Post-120-...]{.mark-turquoise}` | 청록 | content |
| Conclusion | `**Conclusion**` | - | content |
| Conclusion (마커 형태) | `[Conclusion]` | - | content |
| Decision | `**Decision:**` | - | content |
| Observation | `[Observation]` | - | content |

**색상 정보 가용성**

| 변환 방식 | 색상 정보 | 비고 |
| --- | --- | --- |
| pandoc | 유실됨 (`{.mark}`만 출력) | 모든 하이라이트가 동일하게 처리 |
| python-docx | 보존됨 (`highlight_color` 속성) | 4.0 전처리에서 색상별 마커 생성 |

※ pandoc 사용 시 색상 정보가 유실되므로, **텍스트 패턴 기반 판단**을 우선 적용
※ python-docx 직접 파싱 시에만 색상 기반 구분 가능

※ 본 파이프라인은 python-docx 채택으로 색상 정보가 보존됨 (4.0장 참조)
※ Fallback 규칙은 색상 추출 실패 시 또는 향후 변환 도구 변경 시를 대비한 것

**색상 유실 시 Fallback 규칙**

| 마커 텍스트 | content.type |
| --- | --- |
| `[Agreement]{.mark}` | agreement |
| `[Working Assumption]{.mark}` | working_assumption |
| `[Conclusion]{.mark}` | conclusion |
| `[Observation]{.mark}` | observation |
| `[기타 텍스트]{.mark}` | 텍스트 내용으로 LLM 판단 |

※ 색상과 텍스트가 모두 있으면 텍스트 기준 우선
※ 색상 정보는 보조 판단 수단으로 활용

**승인 TDoc 마커**

| 마커 | 패턴 | 의미 |
| --- | --- | --- |
| 승인 TDoc | `[R1-XXXXXXX]{.mark-green}` | 해당 TDoc 승인 |
| 링크+승인 | `[[R1-XXXXXXX]{.mark-green}](...)` | 승인 TDoc 링크 |
| endorsed | `[endorsed]{.mark}` | Session notes 승인 |

※ `{.mark-green}`이 없는 TDoc 참조는 일반 참조 (승인 아님)

---

### 3.8 확장 원칙

| 상황 | 처리 |
| --- | --- |
| 새로운 패턴 | _error 기록 → Human Review |
| 반복 패턴 | 스키마 추가 |
| 불확실 | 추출 안 함 |

---

### 3.9 Graph DB 연결 스키마

**목적**: Item 추출 결과를 Graph DB 노드/엣지로 변환하기 위한 매핑 정의

**노드 (Nodes)**

| 노드 타입 | 소스 필드 | 예시 |
| --- | --- | --- |
| Meeting | context.meeting_id | RAN1_120 |
| Section | context.section_id | 9 |
| Leaf | context.leaf_id | 9.1.2 |
| Item | id | RAN1_120_9.1.2_001 |
| TDoc | input.*, output.* | R1-2501410 |
| Spec | cr_info.spec | 38.214 |
| CR | cr_info.cr_number | CR0693 |

**엣지 (Edges)**

| 관계 | 소스 → 타겟 | 소스 필드 |
| --- | --- | --- |
| CONTAINS | Meeting → Section | context |
| CONTAINS | Section → Leaf | context |
| CONTAINS | Leaf → Item | context |
| DISCUSSED_IN | Item → TDoc | input.moderator_summary |
| USES | Item → TDoc | input.discussion_tdocs |
| PRODUCES | Item → TDoc | output.approved_tdocs |
| ENDORSES | Item → TDoc | output.endorsed_tdocs |
| APPROVES_CR | Item → CR | cr_info |
| MODIFIES | CR → Spec | cr_info.spec |
| REVISION_OF | TDoc → TDoc | input.discussion_tdocs[].revision_of |
| REPLIES_TO | TDoc → TDoc | ls_out.replies_to |

## 4 역할별 상세 설계

### 4.0 문서 전처리

**목적**: .docx 원본을 LLM이 처리할 수 있는 텍스트로 변환하며, 서식 정보(하이라이트, 볼드 등)를 마커로 보존

**변환 도구 선택**

| 도구 | 장점 | 단점 | 결정 |
| --- | --- | --- | --- |
| pandoc | 널리 사용, 간편 | **하이라이트 손실** (치명적) | ❌ |
| mammoth | HTML class 보존 | 추가 HTML 파싱 필요 | △ |
| **python-docx** | **스타일 정보 완전 제어** | 직접 구현 필요 | ✅ 채택 |

※ pandoc은 Word 하이라이트를 `{.mark}`로 변환하지 못함 → Agreement 마커 인식 불가

**파이프라인**

```
.docx (원본)
    ↓
python-docx 직접 파싱
    ↓
├── document.md (서식 마커 포함)
├── toc_raw.yaml (TOC 구조)
└── media/ (이미지)
    ↓
역할 1~4 처리

```

**변환 요구사항**

| 항목 | 요구사항 | 구현 방식 |
| --- | --- | --- |
| 하이라이트 | `[텍스트]{.mark}` 마커 생성 | `run.font.highlight_color` 감지 |
| 볼드 | `**텍스트**` | `run.bold` 감지 |
| 이탤릭 | `*텍스트*` | `run.italic` 감지 |
| 밑줄 | `[텍스트]{.underline}` | `run.underline` 감지 |
| 링크 | `[텍스트](URL)` | hyperlink 관계 추출 |
| 헤더 | `#` , `##` , `###` | [paragraph.style.name](http://paragraph.style.name/) 기반 |
| 표 | Markdown 표 | table 요소 변환 |
| 이미지 | `![](media/imageN.ext)` | 관계 ID로 추출 |
| TOC | 별도 toc_raw.yaml | TOC 스타일 단락 파싱 |

**서식 변환 규칙**

| Word 서식 | python-docx 속성 | 출력 형식 |
| --- | --- | --- |
| 하이라이트 (초록) | `highlight_color == BRIGHT_GREEN` | `[텍스트]{.mark-green}` |
| 하이라이트 (진한 노랑) | `highlight_color == DARK_YELLOW` | `[텍스트]{.mark-yellow}` |
| 하이라이트 (청록) | `highlight_color == TURQUOISE` | `[텍스트]{.mark-turquoise}` |
| 하이라이트 (기타) | `highlight_color == 기타` | `[텍스트]{.mark}` |
| 볼드 | `run.bold == True` | `**텍스트**` |
| 이탤릭 | `run.italic == True` | `*텍스트*` |
| 볼드+이탤릭 | 둘 다 True | `***텍스트***` |
| 밑줄 | `run.underline != None` | `[텍스트]{.underline}` |
| 하이라이트+볼드 | 둘 다 해당 | `[**텍스트**]{.mark-*}` |

**하이라이트 색상 의미** (RAN1 기준)

| 색상 | 출력 | 의미 | 용도 |
| --- | --- | --- | --- |
| BRIGHT_GREEN | `{.mark-green}` | Agreement | 합의 사항, 승인 TDoc |
| DARK_YELLOW | `{.mark-yellow}` | Working Assumption | 잠정 합의 |
| TURQUOISE | `{.mark-turquoise}` | Post-meeting Action | 회의 후 작업 |
| 기타 | `{.mark}` | 미분류 | 새로운 색상 발견 시 |

※ 색상 의미는 RAN1 #120, #122 분석 기준
※ 다른 WG에서 색상 의미가 다를 수 있음 → Human Review 후 확장

**복합 서식 우선순위**

하이라이트가 가장 바깥, 색상 정보 보존:

```
Word: [초록 하이라이트된 볼드 텍스트]
출력: [텍스트]{.mark-green}
Word: [진한 노랑 하이라이트된 볼드 텍스트]
출력: [텍스트]{.mark-yellow}

```

**TOC 추출 (별도 처리)**

| 항목 | 방법 |
| --- | --- |
| TOC 식별 | `paragraph.style.name`이 "TOC 1", "TOC 2", "TOC 3" 등 |
| 섹션 번호 | 텍스트에서 `^\\d+(\\.\\d+)*` 패턴 추출 |
| 제목 | 번호 이후 텍스트 |
| 페이지 번호 | `\\t` 이후 숫자 (또는 필드 코드) |
| 앵커/링크 | hyperlink 관계에서 추출 |

**TOC 스타일 매핑**

| Word 스타일 | depth |
| --- | --- |
| TOC 1 | 1 |
| TOC 2 | 2 |
| TOC 3 | 3 |
| TOC 4 | 4 |

※ depth는 스타일에서 직접 결정 (들여쓰기 파싱 불필요)

**헤더 추출**

| Word 스타일 | 출력 |
| --- | --- |
| Heading 1 | `# 제목` |
| Heading 2 | `## 제목` |
| Heading 3 | `### 제목` |
| Heading 4 | `#### 제목` |
| Title | (메타데이터로 처리) |

**이미지 처리**

| 단계 | 처리 | 설명 |
| --- | --- | --- |
| 추출 | `document.part.rels` | 이미지 관계에서 바이너리 추출 |
| 저장 | media/imageN.ext | 순서대로 번호 부여 |
| 본문 참조 | `![](media/...)` 유지 | 원본 참조 형식 보존 |
| Figure 레이블 | 패턴 인식 | "Figure N:" → media_refs.label |
| 인덱싱 | media_index.yaml | 이미지-Item 연결 기록 |

**Figure 레이블 패턴**

| 패턴 | 예시 |
| --- | --- |
| `Figure N:` | Figure 3: Parameter table |
| `Fig. N` | Fig. 3 |
| `Figure N` (괄호 내) | (see Figure 3) |

**테이블 처리**

| 단계 | 처리 | 설명 |
| --- | --- | --- |
| 변환 | Markdown 표 | 본문 text에 포함 |
| 셀 서식 | 보존 | 볼드, 하이라이트 등 |
| Table 레이블 | 패턴 인식 | "Table N:" → media_refs.label |
| 인덱싱 | media_index.yaml | 테이블 위치 기록 |

※ 이미지 내용 분석은 하지 않음 (향후 확장 가능)
※ media_refs 필드로 Item과 미디어 연결 관계 추적

**링크 변환**

| Word 요소 | 출력 |
| --- | --- |
| 외부 링크 | `[텍스트](URL)` |
| TDoc 링크 | `[R1-2501234](../Docs/R1-2501234.zip)` |
| 내부 앵커 | `[텍스트](#anchor)` |
| 하이라이트된 TDoc | `[[R1-2501234]{.mark}](../Docs/R1-2501234.zip)` |

**출력 파일 구조**

```
/raw/
└── {meeting_id}.docx            ← 원본 보존

/converted/{meeting_id}/
├── document.md                  ← 서식 마커 포함 본문
├── toc_raw.yaml                 ← TOC 구조 (python-docx에서 직접 추출)
└── media/                       ← 추출된 이미지
    ├── image1.png
    └── ...

/outputs/{meeting_id}/
├── toc.yaml                     ← section_type 판단 완료
├── media/                       ← 최종 출력에 복사
├── media_index.yaml             ← 미디어 인덱스
└── ...

```

**toc_raw.yaml 구조**

```yaml
# python-docx에서 직접 추출한 TOC
entries:
  - text: "1 Opening of the meeting"
    style: "TOC 1"
    depth: 1
    page: 5
    anchor: "opening-of-the-meeting"
  - text: "1.1 Call for IPR"
    style: "TOC 2"
    depth: 2
    page: 5
    anchor: "call-for-ipr"
  - text: "MIMO"
    style: "TOC 3"
    depth: 3
    page: 14
    anchor: "mimo"
    unnumbered: true

```

※ TOCAgent는 toc_raw.yaml을 입력으로 받아 section_type 판단 후 toc.yaml 생성

**변환 검증**

| 검증 항목 | 방법 | 실패 시 |
| --- | --- | --- |
| 하이라이트 보존 | `{.mark}` 개수 > 0 | 경고 (문서에 없을 수도) |
| TOC 존재 | toc_raw.yaml entries > 0 | 에러 |
| 헤더 매칭 | TOC entries ≈ 본문 헤더 수 | 경고 |
| 이미지 추출 | media/ 파일 수 = 문서 내 이미지 수 | 경고 |

**에러 처리**

| 상황 | 처리 |
| --- | --- |
| .docx 파일 손상 | 파이프라인 중단, 에러 로그 |
| 하이라이트 0개 | 경고 (문서에 Agreement가 없을 수도 있음) |
| TOC 스타일 없음 | 텍스트 패턴으로 fallback |
| 이미지 추출 실패 | 경고, 참조만 보존 |

※ 4.0은 코드 레벨 구현이며, LLM 판단 로직 없음

---

### 4.1 역할 1: 메타데이터 추출

**목적**: 문서 헤더에서 회의 메타데이터 추출 → meeting_info.yaml 생성

**입력**

| 항목 | 내용 |
| --- | --- |
| 소스 | 변환된 Markdown (document.md) |
| 범위 | TOC 이전까지 (헤더 영역) |

**헤더 구조**

```
Source: {source}

Title: Final Report of 3GPP TSG {TSG} {WG} #{number} v{version}

({location}, {date_range})

Document for: {purpose}

```

**추출 필드 매핑**

| 헤더 요소 | 추출 필드 | 예시 |
| --- | --- | --- |
| Source: | source | MCC Support |
| TSG {TSG} | tsg | RAN |
| {WG} | wg | WG1 |
| (TSG + WG 조합) | wg_code | RAN1 |
| #{number} | meeting_number | 120 |
| v{version} | version | 1.0.0 |
| ({location}, | location | Athens, Greece |
| {date_range}) | start_date, end_date | 2025-02-17, 2025-02-21 |
| Document for: | document_for | Approval |
| (wg_code + meeting_number) | meeting_id | RAN1_120 |

**출력**

```yaml
# meeting_info.yaml
meeting_id: RAN1_120
tsg: RAN
wg: WG1
wg_code: RAN1
meeting_number: "120"
version: "1.0.0"
location: Athens, Greece
start_date: "2025-02-17"
end_date: "2025-02-21"
source: MCC Support
document_for: Approval

```

**에러 처리**

| 상황 | 처리 |
| --- | --- |
| 헤더 파싱 실패 | _error 필드에 기록 → Human Review |
| 필수 필드 누락 | 추출된 필드만 저장 + _error에 상황 명시 |

※ _error 구조는 3.3.3 참조
※ 4.1은 정규식 기반 파싱 우선, 실패 시 LLM fallback

---

### 4.2 역할 2: TOC 파싱 + section_type 판단

**목적**: TOC 구조 파싱 → section_type 판단 → skip 여부 결정 → toc.yaml 생성

**입력**

| 항목 | 내용 |
| --- | --- |
| 소스 | 변환된 Markdown (document.md) |
| 범위 | TOC 영역 |

**TOC 영역 판단**

| 구분 | 기준 |
| --- | --- |
| 시작 | "Table of contents" 이후 |
| 끝 | 본문 첫 섹션 시작 전 |

※ TOC 항목은 `[제목 [페이지](#anchor)](#anchor)` 형식, 본문은 제목만 → LLM이 구분

**처리 흐름**

```
1. TOC 영역 추출
2. LLM이 섹션 계층 구조 파싱
3. 각 섹션의 section_type 판단
4. skip 여부 결정
5. toc.yaml 생성
6. Orchestrator에 반환

```

---

### 4.2.1 섹션 구조 파싱

**추출 정보**

| 필드 | 설명 | 예시 |
| --- | --- | --- |
| id | 섹션 번호 | 9.1.1 |
| title | 섹션 제목 | Beam management |
| depth | 계층 깊이 | 3 |
| parent | 상위 섹션 ID | 9.1 |
| children | 하위 섹션 ID 목록 | [] |
| section_type | 콘텐츠 유형 | Release |
| skip | 처리 제외 여부 | false |
| skip_reason | 제외 사유 (skip: true인 경우) | Procedural section |
| virtual | 가상 번호 여부 (해당 시) | true |

**Leaf Section 정의**

| 항목 | 설명 |
| --- | --- |
| 정의 | children이 빈 배열([])인 섹션 |
| 의미 | Item 추출이 이루어지는 최말단 섹션 |
| 예시 | 9.1.1 Beam management (children: []) |

**Annex ID 형식**

| 형식 | 예시 |
| --- | --- |
| annex_{letter} | annex_b |
| annex_{letter}{number} | annex_a1, annex_c2 |

### 4.2.1.1 Depth 4 이상 처리

| 항목 | 내용 |
| --- | --- |
| 정의 | 10.1.1.1 같은 4단계 이상 번호 |
| 발생 예 | RAN1 #122의 Release 섹션 일부 |
| 처리 방식 | Depth 3 Leaf와 동일하게 처리 |
| Leaf 판정 | 하위 번호 없으면 Leaf |

※ Depth가 깊어져도 처리 로직은 동일 (의미 기반 경계 판단)
※ leaf_id에 전체 번호 기록 (예: "10.1.1.1")

---

### 4.2.2 section_type 판단

**개요**

| 항목 | 설명 |
| --- | --- |
| 판단 주체 | TOCAgent (1차), Section Agent (2차 확인) |
| 판단 기준 | 섹션 제목의 의미 (섹션 번호 아님) |
| 핵심 원칙 | 일반화 - 특정 회의에 종속되지 않음 |

---

**section_type 목록 (현재 식별된 7종)**

| section_type | 설명 | 처리 |
| --- | --- | --- |
| Procedural | 절차적 섹션 | skip |
| Maintenance | 기존 릴리즈 유지보수 | Item 추출 |
| Release | 신규 릴리즈 기능 개발 | Item 추출 |
| Study | 연구 단계 (TR 작성) | Item 추출 |
| UE_Features | UE 기능 정의 | Item 추출 |
| LS | Liaison Statement | Item 추출 |
| Annex | 부록 | 일부만 처리 (B, C-1, C-2) |

※ 위 7종은 RAN1 #120, #122 분석 기준이며, 새로운 유형 발견 시 5.3장 확장 가이드 참조
※ unknown 타입 발생 시 Human Review 후 목록 확장 검토

---

**판단 기준 (의미 기반)**

| section_type | 판단 키워드 | 예시 제목 |
| --- | --- | --- |
| Procedural | Opening, Closing, Approval, Highlights, Minutes | "Opening of the meeting" |
| Maintenance | Maintenance, Pre-Rel-XX | "Maintenance on Release 18", "Pre-Rel-18 NR Maintenance" |
| Release | Release XX (새 기능 개발) | "Release 19", "Release 20 NR" |
| Study | Study, SI, 6GR | "Study on ISAC for NR", "Rel-20 Study of 6GR" |
| UE_Features | UE Features | "Rel-18 UE Features", "Rel-19 UE Features" |
| LS | Incoming Liaison Statements | "Incoming Liaison Statements" |
| Annex | Annex | "Annex B: List of CRs" |

※ 섹션 번호가 아닌 **섹션 제목의 의미**로 판단 (일반화 원칙)
※ Pre-Rel-XX 패턴은 Maintenance로 분류 (Pre-Rel-18, Pre-Rel-19 등)
※ Study는 Release 하위에 있을 수도, 독립 Depth 1 섹션일 수도 있음

---

**판단 우선순위 (참고용 힌트)**

제목에 여러 키워드가 포함된 경우 아래 순서를 **참고**하여 판단:

| 우선순위 | 키워드 | section_type |
| --- | --- | --- |
| 높음 | "Annex" | Annex |
| 높음 | "Liaison" | LS |
| 높음 | "Opening", "Closing", "Approval", "Highlights" | Procedural |
| 중간 | "UE Features" | UE_Features |
| 중간 | "Study", "SI" | Study |
| 중간 | "Maintenance", "Pre-Rel" | Maintenance |
| 낮음 | "Release XX" (숫자 포함) | Release |

※ 위 순서는 일반적 패턴이며, LLM은 문맥에 따라 다르게 판단 가능
※ 판단 근거는 toc.yaml의 type_reason 필드에 기록

**예시**

| 제목 | 판단 | 근거 |
| --- | --- | --- |
| "Rel-18 UE Features" | UE_Features | 우선순위 4 |
| "Maintenance on Release 18" | Maintenance | 우선순위 6 ("Release"보다 "Maintenance" 우선) |
| "Release 19" | Release | 우선순위 7 |
| "Rel-20 Study of 6GR" | Study | 우선순위 5 |

---

### section_type 상속

| 규칙 | 설명 |
| --- | --- |
| 우선 | 제목에 판단 키워드가 있으면 → 개별 판단 |
| 기본 | 없으면 → 상위 section_type 상속 |

※ 판단 우선순위 키워드가 제목에 있으면 상속보다 우선

**상속 예시: RAN1 #120 Section 8**

| id | title | section_type | 판단 근거 |
| --- | --- | --- | --- |
| 8 | Maintenance on Release 18 | Maintenance | 제목에 "Maintenance" |
| 8.1 | Maintenance on Rel-18 work items | Maintenance | 상속 |
| 8.2 | Rel-18 UE Features | UE_Features | "UE Features" → 개별 판단 |

---

### 불확실한 경우 처리

| 상황 | 처리 | 예시 |
| --- | --- | --- |
| 키워드 없음 + 상위도 없음 | `unknown` 표시 → 역할 3에서 재판단 | 새로운 형태의 섹션 |
| 키워드 애매함 | `unknown` 표시 → 역할 3에서 재판단 | "AI/ML enhancements" (Release? Study?) |
| 복합 키워드 | 우선순위 적용 | 위 표 참조 |
| LLM 응답 누락 | 재요청으로 해결 (4.2.8) | 배치 처리 시 일부 누락 |

※ `unknown`과 "응답 누락"은 다른 문제:

- `unknown`: LLM이 의미적으로 판단 못함 → 역할 3 Orchestrator가 Leaf 내용 보고 재판단 (4.3.6)
- 응답 누락: LLM이 일부 섹션에 대해 응답하지 않음 → 역할 2에서 재요청으로 해결 (4.2.8)

---

### Suspended 섹션 처리

| 상황 | 처리 |
| --- | --- |
| "*Suspended in RAN1#XXX*" 표기 | 해당 섹션은 Item 추출 대상이나, 마커가 없으면 Item 0개 |
| "*Placeholder only*" 표기 | 해당 섹션은 Item 추출 대상이나, 마커가 없으면 Item 0개 |

※ Suspended/Placeholder 섹션은 skip이 아님 (향후 회의에서 활성화될 수 있음)
※ 마커가 없으면 정상적으로 Item 0개로 처리 (에러 아님)

---

### 2단계 판단 체계

| 단계 | 주체 | 역할 | 입력 |
| --- | --- | --- | --- |
| 1차 | TOCAgent | 제목 기반 판단 | 섹션 제목 |
| 2차 | Section Agent | 확인/수정 | Leaf 내용 (필요 시) |

**2차 판단 트리거**

| 조건 | 처리 |
| --- | --- |
| section_type = unknown | Section Agent가 Leaf content 보고 판단 |
| 제목과 내용 불일치 의심 | Section Agent가 확인 |
| 1차 판단 신뢰 | 그대로 사용 (대부분의 경우) |

※ 프롬프트 상세는 6장 참조

---

### 회의록별 구조 차이 예시

| 섹션 번호 | RAN1 #120 | RAN1 #122 |
| --- | --- | --- |
| Section 9 | Release 19 | Rel-19 UE Features |
| Section 10 | Closing | Release 20 NR |
| Section 11 | - | Rel-20 Study of 6GR |

→ **동일 섹션 번호라도 회의마다 콘텐츠가 다름. 섹션 번호 하드코딩 금지**

---

**section_type의 Depth 다양성**

동일한 section_type이라도 회의마다 다른 Depth에 위치할 수 있음:

| section_type | 가능한 위치 | 예시 |
| --- | --- | --- |
| Study | Release 하위 (Depth 2~3) | 9.7 Study on channel modelling for ISAC |
| Study | 독립 Section (Depth 1) | 11 Rel-20 Study of 6GR |
| UE_Features | Maintenance/Release 하위 (Depth 2) | 8.2 Rel-18 UE Features |
| UE_Features | 독립 Section (Depth 1) | 9 Rel-19 UE Features |

→ **섹션 번호나 Depth가 아닌 제목의 의미로 section_type 판단** (일반화 원칙)
→ 동일 section_type이 Depth 1일 수도, Depth 2~3일 수도 있음

---

### 다른 섹션 참조

| 내용 | 참조 |
| --- | --- |
| skip 처리 기준 | 4.2.4 |
| Virtual Numbering | 4.2.5 |
| TOC 출력 예시 | 4.2.6 |
| Section Agent 역할 | 5.1 |
| 프롬프트 설계 | 6장 |

---

### 4.2.3 section_type → Section Agent 매핑

| section_type | Section Agent | 비고 |
| --- | --- | --- |
| Maintenance | TechnicalAgent | 기술 논의 |
| Release | TechnicalAgent | 기술 논의 |
| Study | TechnicalAgent | 기술 논의 |
| UE_Features | TechnicalAgent | 기술 논의 |
| LS | IncomingLSAgent | LS 처리 |
| Annex (B, C-1, C-2) | AnnexAgent | 크로스체크 |
| Procedural | - | skip 처리 |
| Annex (기타) | - | skip 처리 |
| unknown | - | Human Review |

※ 역할 3에서 Orchestrator가 이 매핑을 참조하여 Section Agent 호출

---

### 4.2.4 skip 처리

**skip 대상**

| section_type | skip | 이유 |
| --- | --- | --- |
| Procedural | true | 추출 가치 없음 |
| Annex (A, D~H) | true | 크로스체크 불필요 |
| Annex (B, C-1, C-2) | false | 크로스체크 대상 |
| unknown | false | Human Review 후 처리 |
| 기타 | false | Item 추출 대상 |

---

### 4.2.5 번호 없는 하위 섹션 (Virtual Numbering)

**문제 상황**

일부 섹션은 하위 섹션이 있지만 번호가 없음:

```
실제 TOC (RAN1 #120, Section 8.1):
8.1 Maintenance on Rel-18 work items
  ├── MIMO                           ← 번호 없음
  ├── MIMO (Alignment/editorial)     ← 번호 없음
  ├── Network Energy Savings         ← 번호 없음
  └── Sidelink                       ← 번호 없음
8.2 Rel-18 UE Features

```

**해결: 가상 번호 부여**

| 형식 | 설명 | 예시 |
| --- | --- | --- |
| {parent_id}v{sequence} | 상위 ID + 'v' + 순번 | 8.1v1, 8.1v2, 8.1v3 |

**Virtual Numbering 적용 여부**

| 조건 | 처리 |
| --- | --- |
| 번호 없는 하위 섹션 존재 | Virtual Numbering 적용 |
| 모든 섹션에 번호 있음 | Virtual Numbering 불필요 |

※ 모든 회의록에 번호 없는 섹션이 있는 것은 아님
※ toc_raw.yaml의 `unnumbered: true` 플래그로 감지
※ 플래그가 없으면 Virtual Numbering 로직 스킵

**Item ID 예시**

```
RAN1_120_8.1v1_001

```

---

### 4.2.6 출력 예시

**RAN1 #120**

```yaml
# toc.yaml
meeting_id: RAN1_120

sections:
  # Procedural (skip)
  - id: "1"
    title: "Opening of the meeting"
    depth: 1
    parent: null
    children: ["1.1", "1.2", "1.3", "1.4", "1.5"]
    section_type: Procedural
    type_reason: "제목에 'Opening' 키워드 포함"
    skip: true
    skip_reason: "Procedural section"

  # Incoming LS
  - id: "5"
    title: "Incoming Liaison Statements"
    depth: 1
    parent: null
    children: []
    section_type: LS
    type_reason: "제목에 'Liaison' 키워드 포함"
    skip: false

  # Pre-Rel Maintenance
  - id: "6"
    title: "Pre-Rel-18 E-UTRA Maintenance"
    depth: 1
    parent: null
    children: []
    section_type: Maintenance
    type_reason: "제목에 'Pre-Rel', 'Maintenance' 키워드 포함"
    skip: false

  - id: "7"
    title: "Pre-Rel-18 NR Maintenance"
    depth: 1
    parent: null
    children: []
    section_type: Maintenance
    type_reason: "제목에 'Pre-Rel', 'Maintenance' 키워드 포함"
    skip: false

  # Maintenance (번호 없는 하위 섹션 포함)
  - id: "8"
    title: "Maintenance on Release 18"
    depth: 1
    parent: null
    children: ["8.1", "8.2"]
    section_type: Maintenance
    type_reason: "제목에 'Maintenance' 키워드 포함"
    skip: false

  - id: "8.1"
    title: "Maintenance on Rel-18 work items"
    depth: 2
    parent: "8"
    children: ["8.1v1", "8.1v2", "8.1v3"]
    section_type: Maintenance
    type_reason: "상위 섹션(8)에서 상속"
    skip: false

  - id: "8.1v1"
    title: "MIMO"
    depth: 3
    parent: "8.1"
    children: []
    section_type: Maintenance
    type_reason: "상위 섹션(8.1)에서 상속"
    skip: false
    virtual: true

  - id: "8.1v2"
    title: "MIMO (Alignment/editorial issues)"
    depth: 3
    parent: "8.1"
    children: []
    section_type: Maintenance
    type_reason: "상위 섹션(8.1)에서 상속"
    skip: false
    virtual: true

  - id: "8.2"
    title: "Rel-18 UE Features"
    depth: 2
    parent: "8"
    children: []
    section_type: UE_Features
    type_reason: "제목에 'UE Features' 키워드 → 상위(Maintenance)보다 우선"
    skip: false

  # Release (Depth 3까지)
  - id: "9"
    title: "Release 19"
    depth: 1
    parent: null
    children: ["9.1", "9.2", "9.3", "9.7", "9.15"]
    section_type: Release
    type_reason: "제목이 'Release XX' 패턴"
    skip: false

  - id: "9.1"
    title: "AI/ML for NR Air Interface"
    depth: 2
    parent: "9"
    children: ["9.1.1", "9.1.2", "9.1.3", "9.1.4"]
    section_type: Release
    type_reason: "상위 섹션(9)에서 상속"
    skip: false

  - id: "9.1.1"
    title: "Specification support for beam management"
    depth: 3
    parent: "9.1"
    children: []
    section_type: Release
    type_reason: "상위 섹션(9.1)에서 상속"
    skip: false

  - id: "9.7"
    title: "Study on channel modelling for ISAC for NR"
    depth: 2
    parent: "9"
    children: ["9.7.1", "9.7.2"]
    section_type: Study
    type_reason: "제목에 'Study' 키워드 → 상위(Release)보다 우선"
    skip: false

  - id: "9.7.1"
    title: "ISAC deployment scenarios"
    depth: 3
    parent: "9.7"
    children: []
    section_type: Study
    type_reason: "상위 섹션(9.7)에서 상속"
    skip: false

  - id: "9.15"
    title: "Rel-19 UE Features"
    depth: 2
    parent: "9"
    children: ["9.15.1", "9.15.2"]
    section_type: UE_Features
    type_reason: "제목에 'UE Features' 키워드 → 상위(Release)보다 우선"
    skip: false

  - id: "9.15.1"
    title: "UE features for AI/ML for NR Air Interface"
    depth: 3
    parent: "9.15"
    children: []
    section_type: UE_Features
    type_reason: "상위 섹션(9.15)에서 상속"
    skip: false

  # Closing (skip)
  - id: "10"
    title: "Closing of the meeting"
    depth: 1
    parent: null
    children: []
    section_type: Procedural
    type_reason: "제목에 'Closing' 키워드 포함"
    skip: true
    skip_reason: "Procedural section"

  # Annex
  - id: "annex_a1"
    title: "List of Tdocs at RAN1 #120"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: true
    skip_reason: "Not in crosscheck scope"

  - id: "annex_b"
    title: "List of CRs agreed at RAN1 #120"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: false

  - id: "annex_c1"
    title: "List of Outgoing LSs from RAN1 #120"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: false

  - id: "annex_c2"
    title: "List of Incoming LSs from RAN1 #120"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: false

```

**RAN1 #122**

```yaml
# toc.yaml
meeting_id: RAN1_122

sections:
  # Procedural (skip)
  - id: "1"
    title: "Opening of the meeting"
    depth: 1
    parent: null
    children: ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"]
    section_type: Procedural
    type_reason: "제목에 'Opening' 키워드 포함"
    skip: true
    skip_reason: "Procedural section"

  # Incoming LS
  - id: "5"
    title: "Incoming Liaison Statements"
    depth: 1
    parent: null
    children: []
    section_type: LS
    type_reason: "제목에 'Liaison' 키워드 포함"
    skip: false

  # Pre-Rel Maintenance
  - id: "6"
    title: "Pre-Rel-19 E-UTRA Maintenance"
    depth: 1
    parent: null
    children: []
    section_type: Maintenance
    type_reason: "제목에 'Pre-Rel', 'Maintenance' 키워드 포함"
    skip: false

  - id: "7"
    title: "Pre-Rel-19 NR Maintenance"
    depth: 1
    parent: null
    children: []
    section_type: Maintenance
    type_reason: "제목에 'Pre-Rel', 'Maintenance' 키워드 포함"
    skip: false

  # Maintenance (Rel-19)
  - id: "8"
    title: "Maintenance on Rel-19 NR and E-UTRA"
    depth: 1
    parent: null
    children: ["8.1", "8.2", "8.3"]
    section_type: Maintenance
    type_reason: "제목에 'Maintenance' 키워드 포함"
    skip: false

  - id: "8.1"
    title: "Maintenance on AI/ML for NR Air Interface"
    depth: 2
    parent: "8"
    children: ["8.1.1", "8.1.2", "8.1.3"]
    section_type: Maintenance
    type_reason: "상위 섹션(8)에서 상속"
    skip: false

  - id: "8.1.1"
    title: "Specification support for beam management"
    depth: 3
    parent: "8.1"
    children: []
    section_type: Maintenance
    type_reason: "상위 섹션(8.1)에서 상속"
    skip: false

  # UE Features (Depth 1 전체)
  - id: "9"
    title: "Rel-19 UE Features"
    depth: 1
    parent: null
    children: ["9.1", "9.2", "9.3"]
    section_type: UE_Features
    type_reason: "제목에 'UE Features' 키워드 포함"
    skip: false

  - id: "9.1"
    title: "UE features for AI/ML for NR Air Interface"
    depth: 2
    parent: "9"
    children: []
    section_type: UE_Features
    type_reason: "상위 섹션(9)에서 상속"
    skip: false

  # Release (Depth 4 포함)
  - id: "10"
    title: "Release 20 NR"
    depth: 1
    parent: null
    children: ["10.1", "10.2", "10.3", "10.5"]
    section_type: Release
    type_reason: "제목이 'Release XX' 패턴"
    skip: false

  - id: "10.1"
    title: "AI/ML for NR air interface enhancements"
    depth: 2
    parent: "10"
    children: ["10.1.1", "10.1.2"]
    section_type: Release
    type_reason: "상위 섹션(10)에서 상속"
    skip: false

  - id: "10.1.1"
    title: "CSI spatial/frequency compression without temporal aspects"
    depth: 3
    parent: "10.1"
    children: ["10.1.1.1", "10.1.1.2"]
    section_type: Release
    type_reason: "상위 섹션(10.1)에서 상속"
    skip: false

  - id: "10.1.1.1"
    title: "Inference related aspects"
    depth: 4
    parent: "10.1.1"
    children: []
    section_type: Release
    type_reason: "상위 섹션(10.1.1)에서 상속"
    skip: false

  - id: "10.1.1.2"
    title: "Other aspects"
    depth: 4
    parent: "10.1.1"
    children: []
    section_type: Release
    type_reason: "상위 섹션(10.1.1)에서 상속"
    skip: false

  - id: "10.5"
    title: "Study on ISAC for NR"
    depth: 2
    parent: "10"
    children: ["10.5.1"]
    section_type: Study
    type_reason: "제목에 'Study' 키워드 → 상위(Release)보다 우선"
    skip: false

  - id: "10.5.1"
    title: "Evaluation assumptions and performance evaluation"
    depth: 3
    parent: "10.5"
    children: []
    section_type: Study
    type_reason: "상위 섹션(10.5)에서 상속"
    skip: false

  # Study (Depth 1)
  - id: "11"
    title: "Rel-20 Study of 6GR"
    depth: 1
    parent: null
    children: ["11.1", "11.2", "11.3"]
    section_type: Study
    type_reason: "제목에 'Study' 키워드 포함"
    skip: false

  - id: "11.1"
    title: "Overview of 6GR air interface"
    depth: 2
    parent: "11"
    children: []
    section_type: Study
    type_reason: "상위 섹션(11)에서 상속"
    skip: false

  - id: "11.3"
    title: "Waveform and frame structure for 6GR air interface"
    depth: 2
    parent: "11"
    children: ["11.3.1", "11.3.2"]
    section_type: Study
    type_reason: "상위 섹션(11)에서 상속"
    skip: false

  - id: "11.3.1"
    title: "Waveform"
    depth: 3
    parent: "11.3"
    children: []
    section_type: Study
    type_reason: "상위 섹션(11.3)에서 상속"
    skip: false

  # Closing (skip)
  - id: "12"
    title: "Closing of the meeting"
    depth: 1
    parent: null
    children: []
    section_type: Procedural
    type_reason: "제목에 'Closing' 키워드 포함"
    skip: true
    skip_reason: "Procedural section"

  # Annex
  - id: "annex_b"
    title: "List of CRs agreed at RAN1 #122"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: false

  - id: "annex_c1"
    title: "List of Outgoing LSs from RAN1 #122"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: false

  - id: "annex_c2"
    title: "List of Incoming LSs from RAN1 #122"
    depth: 1
    parent: null
    children: []
    section_type: Annex
    type_reason: "제목에 'Annex' 키워드 포함"
    skip: false

```

※ 위 예시는 일부만 표시, 실제는 모든 섹션 포함

**두 문서 구조 비교**

| 항목 | RAN1 #120 | RAN1 #122 |
| --- | --- | --- |
| 최대 Depth | 3 | 4 |
| Section 9 | Release 19 | Rel-19 UE Features |
| Section 10 | Closing | Release 20 NR |
| Section 11 | - | Rel-20 Study of 6GR |
| Section 12 | - | Closing |
| 번호 없는 섹션 | 8.1 하위 (MIMO 등) | 없음 |

→ **섹션 번호가 아닌 section_type으로 처리해야 하는 이유**

---

### 4.2.7 에러 처리

| 상황 | 처리 |
| --- | --- |
| TOC 파싱 실패 | _error 필드에 기록 → Human Review |
| section_type 판단 불확실 | section_type: unknown → 역할 3에서 재판단 (4.3.6) |
| LLM 응답 누락 | 재요청으로 해결 (4.2.8) |
| 번호 없는 섹션 발견 | 가상 번호 부여 (4.2.5) |

**에러 유형 구분**

| 유형 | 원인 | 해결 위치 | 해결 방법 |
| --- | --- | --- | --- |
| 응답 누락 | LLM이 일부만 응답 | 역할 2 | 누락 섹션 재요청 |
| 판단 불가 | LLM이 의미적으로 판단 못함 | 역할 3 | Leaf 내용 보고 재판단 (4.3.6) |

※ 두 유형은 원인과 해결책이 다름 - 혼동하지 말 것
※ _error 구조는 3.3.3 참조

---

### 4.2.8 대용량 TOC 처리

**목적**: LLM 컨텍스트 한계를 고려한 안정적 처리

**처리 원칙**

| 원칙 | 설명 |
| --- | --- |
| 분할 처리 | TOC가 LLM 컨텍스트 한계에 근접하면 배치로 분할 |
| 응답 검증 | 요청 섹션 수 = 응답 섹션 수 확인 필수 |
| 복구 전략 | 누락 발생 시 해당 섹션만 개별 재요청 |
| 컨텍스트 연속성 | 배치 간 부모 section_type 전달 (상속 판단용) |

**처리 흐름**

┌─────────────────────────────────────────────────────────────┐
│                    TOC 크기 판단                             │
│         컨텍스트 한계 근접 시 배치 분할 (권장 30개)           │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│                    배치별 LLM 호출                           │
│              이전 배치의 부모 section_type 전달              │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│                      응답 검증                               │
│                                                              │
│   요청 = 응답 ──────────────────────────▶ 정상               │
│                                                              │
│   요청 > 응답 ──▶ 누락 섹션 식별 ──▶ 개별 재요청             │
│                         │                                    │
│                         ▼                                    │
│               재시도 2회 초과 ──▶ _error + Human Review      │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│                 결과 병합 → toc.yaml 생성                    │
└─────────────────────────────────────────────────────────────┘

**부모 컨텍스트 전달**

배치 간 상속 판단을 위해 이전 배치의 부모 섹션 정보 전달:

```yaml
# 다음 배치에 전달하는 컨텍스트 예시
parent_context:
  - id: "8"
    section_type: Maintenance
  - id: "9"
    section_type: Release

```

**구현 파라미터** (권장값, 조정 가능)

| 파라미터 | 권장값 | 조정 기준 |
| --- | --- | --- |
| 배치 크기 | 30개 | LLM 모델, 컨텍스트 크기, 응답 안정성 |
| 최대 재시도 | 2회 | 안정성 vs 비용 트레이드오프 |

※ 위 파라미터는 현재 Claude 모델 기준 경험적 권장값
※ LLM 모델 변경 또는 성능 개선 시 조정 가능
※ 하드코딩 규칙이 아닌 구현 가이드임

**재요청 규칙**

| 항목 | 설명 |
| --- | --- |
| 재요청 대상 | 응답에서 누락된 섹션만 |
| 재요청 방식 | 개별 요청 (1개씩) |
| 실패 시 | _error 기록, Human Review 트리거 |

**핵심 원칙 준수** (1.3장 참조)

| 원칙 | 적용 |
| --- | --- |
| True Agentic AI | 배치 크기는 인프라 파라미터, 의미 판단은 LLM |
| 일반화 | 문서 크기와 무관하게 동일 로직 적용 |
| 검증 가능성 | 누락/재요청 이력 _processing에 기록 |

※ 배치 처리는 LLM 기술적 한계 대응이며, 도메인 로직 하드코딩과 다름

---

### 4.3 역할 3: 섹션 처리

**목적**: Section Agent가 담당 섹션의 Leaf를 찾아 SubSection Agent에게 Item 추출 위임

---

**4.3.1 처리 흐름**

**전체 흐름**

```
toc.yaml (역할 2 출력)
    ↓
Orchestrator
    ├── section_type = unknown? → 2차 판단 (4.3.6)
    └── section_type 확정 → Section Agent 할당
    ↓
Depth 1 섹션별로 Section Agent 호출 (병렬)
    ↓
┌─────────────────────────────────────────────────┐
│ Section Agent                                   │
│                                                 │
│  1. toc.yaml에서 Leaf 조회 (children: [])        │
│  2. 각 Leaf에 대해:                              │
│     a. 본문 내용 추출                            │
│     b. section_type으로 SubSection Agent 결정   │
│     c. SubSection Agent 호출 → Item 추출         │
│     d. (내용이 크면) 청킹 처리                   │
│  3. 결과 파일 생성                               │
│                                                 │
└─────────────────────────────────────────────────┘
    ↓
sections/{section_id}/ 저장

```

**처리 주체 구분**

| 단계 | 처리 주체 | 설명 |
| --- | --- | --- |
| Section Agent 할당 | 코드 | section_type → Agent 매핑 |
| Leaf 조회/순회 | 코드 | toc.yaml 기반 |
| 본문 내용 추출 | 코드 | 헤더 기반 분리 |
| SubSection Agent 할당 | 코드 | section_type 기반 매핑 |
| Item 추출 | **LLM** | SubSection Agent |
| unknown 재판단 | **LLM** | Orchestrator (4.3.6) |

---

**병렬 처리**

| 항목 | 설명 |
| --- | --- |
| 단위 | Depth 1 섹션별로 독립 실행 |
| 동시성 | Section Agent 간 병렬 처리 |
| 의존성 | toc.yaml만 참조, Section Agent 간 의존 없음 |

---

**입력**

| 항목 | 내용 |
| --- | --- |
| toc.yaml | 섹션 구조 + section_type 정보 |
| document.md | 변환된 본문 |

---

**출력 파일 구조**

```
sections/{section_id}/
├── _index.yaml          ← 섹션 메타 + Leaf 목록
└── {leaf_id}.yaml       ← Leaf별 Item 목록

annexes/
└── {annex_id}.yaml      ← Annex별 파싱 결과

```

**출력 예시**

```
sections/9/
├── _index.yaml
├── 9.1.1.yaml
├── 9.1.2.yaml
└── 9.1.3.yaml

annexes/
├── annex_b.yaml
├── annex_c1.yaml
└── annex_c2.yaml

```

---

**Leaf 본문 추출**

| 단계 | 설명 |
| --- | --- |
| 1 | TOC의 page 정보로 대략적 탐색 범위 확보 |
| 2 | 해당 범위 내에서 Leaf 섹션 제목 찾기 |
| 3 | LLM이 의미 기반으로 정확한 경계 판단 |

※ page는 탐색 범위 축소용 힌트이며, 최종 경계 판단은 LLM이 의미 기반으로 수행
※ 정규식은 fallback으로만 사용

---

**Leaf 판단 규칙**

| 조건 | Leaf 여부 | 처리 |
| --- | --- | --- |
| children: [] | ✅ Leaf | 섹션 전체 본문 → SubSection Agent |
| children: [하위...] | ❌ 중간 노드 | 하위 Leaf만 처리 |

※ Depth 1 섹션이라도 children: []이면 Leaf로 처리
※ "하위 항목이 TOC에 없음" = 해당 섹션이 Leaf
※ 예: Section 6 (Pre-Rel-18 E-UTRA Maintenance)이 children: []이면 섹션 전체가 1개 Leaf

---

**Intro Content 처리**

| 용어 | 정의 |
| --- | --- |
| Intro Content | 중간 노드(비-Leaf)에 직접 있는 콘텐츠 |

| 상황 | 처리 |
| --- | --- |
| 중간 노드에 Agreement/Conclusion 등 마커 있음 | 해당 노드를 Leaf처럼 처리, Item 추출 |
| 중간 노드에 마커 없음 (일반 텍스트만) | 무시 (Leaf에서만 Item 추출) |

**예시**

```
Section 9.1 (중간 노드, children: [9.1.1, 9.1.2])
├── [Agreement]{.mark} 직접 포함  → 9.1도 Item 추출 대상
├── 9.1.1 (Leaf)                  → Item 추출
└── 9.1.2 (Leaf)                  → Item 추출

```

※ 중간 노드에 마커가 있으면 해당 노드의 콘텐츠(하위 Leaf 제외)에서 Item 추출

---

### 4.3.2 Section Agent (3종)

**개요**

| Agent | 담당 section_type | 처리 방식 |
| --- | --- | --- |
| TechnicalAgent | Maintenance, Release, Study, UE_Features | 코드 (SubAgent 호출) |
| IncomingLSAgent | LS | 코드 (SubAgent 호출) |
| AnnexAgent | Annex (B, C-1, C-2만) | 코드 (SubAgent 호출) |

※ Procedural은 skip 처리되어 Agent 호출 없음 (4.2.4 참조)
※ Section Agent는 Leaf 순회 및 SubSection Agent 호출 역할 (LLM 판단은 SubSection Agent에서)

---

**TechnicalAgent**

| 항목 | 내용 |
| --- | --- |
| 역할 | 기술 논의 섹션의 Leaf 순회 및 SubAgent 호출 |
| 호출 SubAgent | MaintenanceSubAgent, ReleaseSubAgent, StudySubAgent, UEFeaturesSubAgent |

**IncomingLSAgent**

| 항목 | 내용 |
| --- | --- |
| 역할 | LS 섹션의 Leaf 순회 및 SubAgent 호출 |
| 호출 SubAgent | LSSubAgent |

**AnnexAgent**

| 항목 | 내용 |
| --- | --- |
| 역할 | Annex 섹션 순회 및 SubAgent 호출 |
| 호출 SubAgent | AnnexSubAgent |
| 처리 대상 | Annex B (CR), Annex C-1 (Outgoing LS), Annex C-2 (Incoming LS) |

※ Annex A, D~H는 skip 처리 (4.2.4 참조)

---

### 4.3.3 SubSection Agent 할당 (6종)

**section_type → SubSection Agent 매핑**

| section_type | SubSection Agent | Section Agent |
| --- | --- | --- |
| Maintenance | MaintenanceSubAgent | TechnicalAgent |
| Release | ReleaseSubAgent | TechnicalAgent |
| Study | StudySubAgent | TechnicalAgent |
| UE_Features | UEFeaturesSubAgent | TechnicalAgent |
| LS | LSSubAgent | IncomingLSAgent |
| Annex | AnnexSubAgent | AnnexAgent |

※ section_type은 toc.yaml에서 1차 결정됨 (4.2.2 참조)
※ unknown인 경우 4.3.7 참조

---

**할당 예시 (RAN1 #120)**

| Leaf | section_type | Section Agent | SubSection Agent |
| --- | --- | --- | --- |
| 8.1v1 (MIMO) | Maintenance | TechnicalAgent | MaintenanceSubAgent |
| 8.2 (UE Features) | UE_Features | TechnicalAgent | UEFeaturesSubAgent |
| 9.1.1 (Beam management) | Release | TechnicalAgent | ReleaseSubAgent |
| 5 (Incoming LS) | LS | IncomingLSAgent | LSSubAgent |
| annex_b | Annex | AnnexAgent | AnnexSubAgent |

---

### 4.3.4 대용량 처리 (청킹)

**청킹 조건**

| 상황 | 처리 |
| --- | --- |
| Leaf 내용이 적정 크기 | 그대로 SubSection Agent에 전달 |
| Leaf 내용이 너무 큼 | 의미 단위로 청킹 후 순차 처리 |

**토큰 기준**

| 항목 | 기준 |
| --- | --- |
| 청킹 트리거 | Leaf 콘텐츠 > 6,000 토큰 |
| 청크 목표 크기 | 4,000 ~ 6,000 토큰 |
| 최소 청크 크기 | 1,000 토큰 (이하면 이전 청크에 병합) |

※ 토큰 수는 근사치이며, 의미 단위 경계가 우선
※ Claude 모델 기준 (다른 LLM 사용 시 조정 필요)

**청킹 원칙**

| 원칙 | 설명 |
| --- | --- |
| 의미 단위 | 토큰 수가 아닌 의미 단위로 분할 |
| Item 보존 | 하나의 Item이 쪼개지지 않도록 |

※ 의미 단위로 청킹 (핵심 원칙: True Agentic AI)

**section_type별 청킹 단위**

| section_type | 청킹 단위 |
| --- | --- |
| Maintenance, Release, Study | Moderator Summary 경계 |
| UE_Features | Feature 그룹 경계 |
| LS | 개별 LS 항목 |
| Annex | 표/목록 경계 |

**처리 흐름**

```
Section Agent:
  1. Leaf 크기 판단 → 청킹 필요
  2. 의미 단위로 청크 분할
  3. 청크별 SubSection Agent 호출
  4. 결과 병합

```

**출력 표시**

```yaml
_processing:
  chunked: true
  chunk_count: 3

```

**청킹 한계**

| 상황 | 처리 |
| --- | --- |
| Item 하나가 컨텍스트 초과 | _error 기록 → Human Review |

---

### 4.3.5 에러 처리

| 상황 | 처리 |
| --- | --- |
| Leaf 경계 판단 실패 | _error 기록 → Human Review |
| SubSection Agent 추출 실패 | _error 기록 → Human Review |
| 청킹 실패 | _error 기록 → Human Review |
| 일부 Leaf 실패 | 성공한 Leaf는 저장, 실패 Leaf만 _error |

※ _error 구조는 3.3.3 참조

---

### 4.3.6 unknown 처리

**발생 조건**

| 상황 | 예시 |
| --- | --- |
| 키워드 없음 + 상속 불가 | 새로운 형태의 섹션 |
| 키워드 애매함 | "AI/ML enhancements" (Release? Study?) |

※ 3GPP 회의록은 정형화되어 있어 unknown은 거의 발생하지 않음

---

**처리 흐름**

```
Orchestrator:
  1. toc.yaml에서 section_type = unknown 발견
  2. 해당 Leaf의 content 일부 읽기 (헤더 + 첫 몇 문단)
  3. LLM으로 section_type 재판단
  4. 결정된 section_type으로 Section Agent 할당

```

---

**재판단 기준**

| 내용 패턴 | section_type |
| --- | --- |
| CR, Maintenance, Editorial 언급 | Maintenance |
| Agreement 중심, 새 기능 정의 | Release |
| TR, Observation, Study 언급 | Study |
| Feature Group, FG 정의 | UE_Features |
| LS 응답, Reply 논의 | LS |

---

**재판단 실패 시**

| 상황 | 처리 |
| --- | --- |
| 여전히 판단 불가 | TechnicalAgent에 기본 할당 + _warning 기록 |
| TechnicalAgent 내에서 | ReleaseSubAgent를 기본으로 사용 |

```yaml
# _warning 예시
_warning:
  type: unknown_section_type
  message: "section_type 판단 실패, 기본값 사용"
  original_title: "New Agenda Item"
  assigned_type: Release

```

---

**프롬프트**

※ 상세 프롬프트는 6장 참조

---

### 다른 섹션 참조

| 내용 | 참조 |
| --- | --- |
| section_type 판단 기준 | 4.2.2 |
| skip 처리 | 4.2.4 |
| Section Agent 상세 | 5.1 |
| SubSection Agent 상세 | 5.2 |
| _error 구조 | 3.3.3 |
| 프롬프트 설계 | 6장 |

---

### 4.4 역할 4: 결과 취합 + 검증

**목적**: 역할 1~3 출력물 수집 → 검증 → extraction_result.yaml 생성

---

**4.4.1 처리 흐름**

**전체 흐름**

```
역할 1~3 출력물
    ↓
┌─────────────────────────────────────────────────┐
│ Orchestrator                                    │
│                                                 │
│  1. 결과 파일 수집                               │
│     - meeting_info.yaml                         │
│     - toc.yaml                                  │
│     - sections/*/*.yaml                         │
│     - annexes/*.yaml                            │
│  2. 통계 집계                                    │
│  3. 검증 수행                                    │
│  4. extraction_result.yaml 생성                 │
│                                                 │
└─────────────────────────────────────────────────┘
    ↓
extraction_result.yaml

```

※ 4.4는 Orchestrator(코드) + LLM 혼합 처리

**입력**

| 파일 | 출처 |
| --- | --- |
| meeting_info.yaml | 역할 1 |
| toc.yaml | 역할 2 |
| sections/{section_id}/_index.yaml | 역할 3 |
| sections/{section_id}/{leaf_id}.yaml | 역할 3 |
| annexes/{annex_id}.yaml | 역할 3 |

**통계 집계**

| 항목 | 집계 방식 |
| --- | --- |
| total_sections | toc.yaml의 Depth 1 섹션 수 (skip: true 제외) |
| total_leaves | 모든 _index.yaml의 leaves 합계 |
| total_items | 모든 {leaf_id}.yaml의 items 합계 |
| by_status | status별 집계 (3.3.2 status 값 기준) |

**media_index.yaml 생성**

| 단계 | 처리 |
| --- | --- |
| 1 | sections/*.yaml에서 media_refs 필드 수집 |
| 2 | resolution.content[].text에서 `![](media/...)` 패턴 추출 |
| 3 | media/ 디렉토리의 파일 목록과 매칭 |
| 4 | Item ↔ Media 연결 관계 기록 |
| 5 | 통계 집계 |

**연결 관계 추출**

| 소스 | 추출 내용 |
| --- | --- |
| Item.media_refs | 명시적으로 기록된 미디어 참조 |
| Item.resolution.content[].text | `![](media/imageN.png)` 패턴 |

**출력**: media_index.yaml (스키마는 3.4 참조)

---

**4.4.2 검증**

**검증 유형**

| 검증 | 주체 | 내용 |
| --- | --- | --- |
| 구조 검증 | 코드 | 파일 존재, 필수 필드 존재 |
| 크로스체크 | LLM | 본문 vs Annex 의미적 대응 |
| 일관성 검증 | 코드 | 통계 합계 일치 |

**구조 검증**

| 대상 | 확인 내용 |
| --- | --- |
| meeting_info.yaml | 필수 필드 존재 (meeting_id, wg_code 등) |
| toc.yaml | 섹션 구조, parent-children 관계 |
| _index.yaml | leaves 배열 존재 |
| {leaf_id}.yaml | items 배열, context 필드 |
| annexes/*.yaml | Annex B, C-1, C-2 파일 존재 |

**크로스체크**

| 비교 | 본문 (body_count) | Annex (annex_count) |
| --- | --- | --- |
| CR | cr_info 필드가 있는 Item 수 | Annex B 항목 수 |
| Outgoing LS | ls_out.reply_tdoc이 존재하는 Item 수 | Annex C-1 항목 수 |
| Incoming LS | section_type: LS인 Item 수 | Annex C-2 항목 수 |

※ 단순 숫자 비교가 아닌 **의미적 대응** 확인 (TDoc 번호 매칭 등)

**일관성 검증**

| 검증 | 확인 내용 |
| --- | --- |
| Item 수 | 각 Leaf의 item_count 합 = total_items |
| Leaf 수 | 각 섹션의 leaf_count 합 = total_leaves |

**검증 결과 상태**

| 상태 | 설명 | 처리 |
| --- | --- | --- |
| passed | 모든 검증 통과 | 정상 완료 |
| warning | 경미한 불일치 (< 10%) | 기록, 처리 계속 |
| failed | 심각한 오류 | Human Review |

---

**4.4.3 출력**

**출력 구조**

```yaml
# extraction_result.yaml
metadata:
  meeting_id: RAN1_120
  generated_at: "2025-02-22T11:00:00Z"
  pipeline_version: "1.0.0"
  source_document: "Final_Minutes_report_RAN1_120_v100.docx"

meeting_info:
  # meeting_info.yaml 내용 포함

processing_summary:
  role_status:
    role_1: completed
    role_2: completed
    role_3: completed
    role_4: completed
  toc_processing:  # 역할 2 배치 처리 정보
    total_sections: 103
    batch_count: 4
    retry_count: 2
    retried_sections: ["9.1.5", "10.2.3"]
  statistics:
    total_sections: 5
    total_leaves: 45
    total_items: 339
  by_section:
    - section_id: "9"
      title: "Release 19"
      status: completed
      leaf_count: 15
      item_count: 120
  by_annex:
    - annex_id: "annex_b"
      title: "List of CRs"
      status: completed
      entry_count: 45
    - annex_id: "annex_c1"
      title: "List of Outgoing LSs"
      status: completed
      entry_count: 12
    - annex_id: "annex_c2"
      title: "List of Incoming LSs"
      status: completed
      entry_count: 8

validation:
  overall_status: passed
  structure:
    status: passed
  crosscheck:
    status: passed
    cr:
      body_count: 45
      annex_count: 45
      match: true
    ls_outgoing:
      body_count: 12
      annex_count: 12
      match: true
    ls_incoming:
      body_count: 8
      annex_count: 8
      match: true
  consistency:
    status: passed

extracted_data_summary:
  by_status:
    Agreed: 280
    Concluded: 40
    No_Consensus: 0
    Deferred: 0
    Noted: 15
    Pending: 4

```

**에러 발생 시**

```yaml
validation:
  overall_status: failed
  # ...

_error:
  has_error: true
  error_type: "validation_failed"
  error_message: "크로스체크 실패: CR 수 불일치"

```

※ _error 구조는 3.3.3 참조
※ Annex 스키마는 3.5 참조

---

## 5 Section Agent

### 5.1 Section Agent

### 5.1.0 공통

**정의**

| 항목 | 내용 |
| --- | --- |
| 역할 | Depth 1 섹션 처리 총괄, Leaf 순회 및 SubSection Agent 호출 |
| 할당 주체 | Orchestrator (section_type 기반) |
| 현재 정의 | 3종 |
| 확장 | 고정이 아님, 새로운 Agent 추가 가능 |

---

**Section Agent 목록 (3종)**

| Section Agent | 담당 section_type | 호출하는 SubSection Agent |
| --- | --- | --- |
| TechnicalAgent | Maintenance, Release, Study, UE_Features | MaintenanceSubAgent, ReleaseSubAgent, StudySubAgent, UEFeaturesSubAgent |
| IncomingLSAgent | LS | LSSubAgent |
| AnnexAgent | Annex (B, C-1, C-2) | AnnexSubAgent |

※ Procedural은 skip 처리되어 Agent 없음 (4.2.4 참조)
※ unknown은 Orchestrator에서 재판단 후 할당 (4.3.7 참조)

---

**공통 처리 흐름**

```
1. toc.yaml에서 담당 섹션의 Leaf 조회 (children: [])
2. 각 Leaf에 대해:
   a. document.md에서 본문 추출
   b. section_type 확인 → SubSection Agent 결정
   c. SubSection Agent 호출
   d. (내용이 크면) 청킹 처리
3. 결과 파일 생성

```

※ 상세 흐름은 4.3.1 참조

---

**처리 주체 구분**

| 단계 | 처리 주체 | 설명 |
| --- | --- | --- |
| Leaf 조회 | 코드 | toc.yaml 기반 children: [] 필터 |
| 본문 추출 | 코드 | 헤더 기반 텍스트 분리 |
| section_type → SubAgent 매핑 | 코드 | 고정 매핑 테이블 |
| SubSection Agent 호출 | 코드 | 매핑된 SubAgent 호출 |
| Item 추출 | **LLM** | SubSection Agent 내부 |
| 청킹 판단 | 코드 | 토큰 수 기반 |
| 청킹 경계 결정 | **LLM** | 의미 단위 분할 (4.3.7 참조) |

※ Section Agent 자체는 대부분 코드 로직, LLM은 SubSection Agent에서 사용

---

**입력**

| 항목 | 설명 |
| --- | --- |
| toc.yaml | 섹션 구조 + section_type 정보 |
| document.md | 변환된 본문 |
| meeting_info | 회의 메타데이터 (역할 1 결과) |

---

**출력**

| Agent | 출력 경로 |
| --- | --- |
| TechnicalAgent | sections/{section_id}/_index.yaml, {leaf_id}.yaml |
| IncomingLSAgent | sections/{section_id}/_index.yaml, {leaf_id}.yaml |
| AnnexAgent | annexes/{annex_id}.yaml |

---

**SubSection Agent 전달 항목**

| 항목 | 설명 |
| --- | --- |
| leaf_id | Leaf 식별자 (예: "9.1.1", "8.1v1") |
| leaf_title | Leaf 제목 |
| leaf_content | Leaf 본문 텍스트 |
| section_type | toc.yaml에서 결정된 유형 |
| parent_context | 상위 섹션 정보 |
| meeting_info | 회의 메타데이터 |

**parent_context 구조**

```yaml
parent_context:
  meeting_id: "RAN1_120"
  section_id: "9"
  section_title: "Release 19"
  parent_id: "9.1"
  parent_title: "AI/ML for NR Air Interface"

```

※ Item의 context (3.3.2)와는 별도 구조임

---

**확장 원칙**

| 상황 | 처리 | 참조 |
| --- | --- | --- |
| 기존 Agent로 처리 가능 | 정상 처리 | - |
| section_type = unknown | Orchestrator가 재판단 후 할당 | 4.3.6 |
| 새 section_type 필요 | 스키마 확장 후 Agent 추가 | 5.3 |

※ 프롬프트는 6장 참조

---

### 5.1.1 TechnicalAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | 기술 논의 섹션의 Leaf 순회 및 SubAgent 호출 |
| 담당 section_type | Maintenance, Release, Study, UE_Features |
| 호출 SubAgent | MaintenanceSubAgent, ReleaseSubAgent, StudySubAgent, UEFeaturesSubAgent |
| 처리 방식 | 코드 (SubAgent 호출만, LLM 판단 없음) |

---

**section_type → SubSection Agent 매핑**

| section_type | SubSection Agent | 주요 추출 대상 |
| --- | --- | --- |
| Maintenance | MaintenanceSubAgent | CR, Agreement |
| Release | ReleaseSubAgent | Agreement, Working Assumption |
| Study | StudySubAgent | Agreement, Conclusion, Observation |
| UE_Features | UEFeaturesSubAgent | Agreement, Feature Group |

※ section_type은 toc.yaml에서 이미 결정됨 (4.2.2 참조)

---

**처리 흐름**

```
1. toc.yaml에서 담당 섹션의 Leaf 조회
2. 각 Leaf의 section_type 확인
3. section_type에 따라 SubSection Agent 결정 (코드 매핑)
4. Leaf 본문 추출 → SubSection Agent 호출
5. 결과 수집 → _index.yaml + {leaf_id}.yaml 생성

```

---

**출력: _index.yaml 예시**

```yaml
# sections/9/_index.yaml
section_id: "9"
title: "Release 19"
section_type: Release
agent: TechnicalAgent

leaves:
  - leaf_id: "9.1.1"
    title: "Beam management"
    section_type: Release
    subsection_agent: ReleaseSubAgent
    status: completed
    item_count: 8
  - leaf_id: "9.1.2"
    title: "Positioning"
    section_type: Release
    subsection_agent: ReleaseSubAgent
    status: completed
    item_count: 5

statistics:
  total_leaves: 25
  total_items: 120
  by_status:
    Agreed: 85
    Concluded: 25
    No_Consensus: 10

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

**상속된 section_type 처리**

| 상황 | 예시 | 처리 |
| --- | --- | --- |
| 동일 유형 | Section 9 (Release) → 9.1.1 (Release) | 그대로 상속 |
| 다른 유형 | Section 8 (Maintenance) → 8.2 (UE_Features) | 개별 section_type 사용 |

※ 4.2.2 상속 규칙 참조

---

### 5.1.2 IncomingLSAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | LS 섹션의 Leaf 순회 및 SubAgent 호출 |
| 담당 section_type | LS |
| 호출 SubAgent | LSSubAgent |
| 처리 방식 | 코드 (SubAgent 호출만, LLM 판단 없음) |
| 특징 | 섹션 자체가 Leaf (children 없음) |

---

**TechnicalAgent와의 차이**

| 항목 | TechnicalAgent | IncomingLSAgent |
| --- | --- | --- |
| Leaf 구조 | 다층 구조 | 섹션 자체가 Leaf |
| SubAgent 종류 | 4종 중 선택 | 1종 고정 |
| section_type | 상속/개별 판단 | LS 고정 |

---

**처리 흐름**

```
1. 섹션 전체가 Leaf (children: [])
2. 본문 추출
3. (내용이 크면) 청킹 처리
4. LSSubAgent 호출
5. 결과 저장

```

---

**출력: _index.yaml 예시**

```yaml
# sections/5/_index.yaml
section_id: "5"
title: "Incoming Liaison Statements"
section_type: LS
agent: IncomingLSAgent

leaves:
  - leaf_id: "5"
    title: "Incoming Liaison Statements"
    section_type: LS
    subsection_agent: LSSubAgent
    status: completed
    item_count: 15

statistics:
  total_leaves: 1
  total_items: 15
  by_status:
    Noted: 8
    Deferred: 5
    Concluded: 2

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 5.1.3 AnnexAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | Annex 섹션 처리 (크로스체크용) |
| 담당 section_type | Annex |
| 호출 SubAgent | AnnexSubAgent |
| 처리 방식 | 코드 (SubAgent 호출만, LLM 판단 없음) |
| 처리 대상 | B, C-1, C-2만 |

※ Annex A, D~H는 skip 처리 (4.2.4 참조)

---

**처리 대상 Annex**

| Annex | 내용 | 크로스체크 대상 |
| --- | --- | --- |
| B | List of CRs | 본문 cr_info |
| C-1 | List of Outgoing LSs | 본문 ls_out |
| C-2 | List of Incoming LSs | Section 5 LS |

---

**TechnicalAgent와의 차이**

| 항목 | TechnicalAgent | AnnexAgent |
| --- | --- | --- |
| 처리 방식 | 섹션별 처리 | 해당 Annex만 처리 |
| 출력 위치 | sections/{section_id}/ | annexes/ |
| SubAgent | 4종 중 선택 | 1종 고정 |
| 목적 | Item 추출 | 크로스체크 데이터 |

---

**처리 흐름**

```
1. toc.yaml에서 Annex B, C-1, C-2 조회
2. 각 Annex 본문 추출
3. AnnexSubAgent 호출 (표 파싱)
4. 결과 저장

```

---

**출력 예시**

```yaml
# annexes/annex_b.yaml
annex_id: "annex_b"
title: "List of CRs agreed at RAN1 #120"
section_type: Annex
agent: AnnexAgent

entries:
  - tdoc_id: "R1-2501501"
    title: "Correction on transition time"
    source: "vivo"
    spec: "38.213"
    cr_number: "0693"
  - tdoc_id: "R1-2501502"
    title: "CR on PSCCH DMRS"
    source: "CATT"
    spec: "38.211"
    cr_number: "0148"

statistics:
  total_entries: 45

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

※ Annex 스키마 상세는 3.5 참조

---

### 5.1.4 에러 처리

| 상황 | 처리 |
| --- | --- |
| Leaf 본문 추출 실패 | _error 기록 → Human Review |
| SubSection Agent 호출 실패 | _error 기록, 다른 Leaf는 계속 처리 |
| 청킹 실패 | _error 기록 → Human Review |

※ _error 구조는 3.3.3 참조
※ 프롬프트는 6장 참조

---

### 다른 섹션 참조

| 내용 | 참조 |
| --- | --- |
| section_type 판단 | 4.2.2 |
| 처리 흐름 상세 | 4.3.1 |
| unknown 처리 | 4.3.6 |
| 청킹 | 4.3.4 |
| SubSection Agent | 5.2 |
| 확장 원칙 | 5.3 |
| 프롬프트 | 6장 |

---

### 5.2 SubSection Agent

### 5.2.0 공통

**정의**

| 항목 | 내용 |
| --- | --- |
| 역할 | Leaf Section의 내용을 처리하여 Item을 추출 |
| 할당 주체 | Section Agent |
| 현재 정의 | 6종 |
| 확장 | 고정이 아님, 새로운 Agent 추가 가능 |

**SubSection Agent 목록 (6종)**

| SubSection Agent | 담당 section_type | 주요 추출 대상 |
| --- | --- | --- |
| MaintenanceSubAgent | Maintenance | CR, Agreement |
| ReleaseSubAgent | Release | Agreement, Working Assumption |
| StudySubAgent | Study | Agreement, Conclusion, Observation |
| UEFeaturesSubAgent | UE_Features | Agreement, Feature Group |
| LSSubAgent | LS | Decision, LS 처리 결과 |
| AnnexSubAgent | Annex (B, C-1, C-2) | 크로스체크용 목록 |

※ Procedural은 skip 처리되어 SubSection Agent 없음 (4.2.4 참조)

---

**공통 책임**

| 단계 | 책임 | 수행 주체 |
| --- | --- | --- |
| 1. 내용 분석 | 전달받은 leaf_content 분석 | LLM |
| 2. Item 경계 판단 | 의미 기반으로 Item 단위 분리 | LLM |
| 3. TDoc 추출 | Moderator Summary, Discussion TDocs, Approved TDocs 추출 | LLM |
| 4. Item 추출 | 각 Item의 상세 정보 추출 | LLM |
| 5. 파일 생성 | {leaf_id}.yaml 생성 | 코드 |

**TDoc 추출 규칙**

| 추출 대상 | 패턴 | 저장 필드 |
| --- | --- | --- |
| Moderator Summary | "Summary #N", "FL summary #N" | input.moderator_summary |
| Discussion TDocs | `Relevant tdocs:` 목록, 본문 내 참조 TDoc | input.discussion_tdocs |
| Approved TDocs | `[approved in R1-xxx]{.mark}`, "is agreed" | output.approved_tdocs |
| Endorsed TDocs | "is endorsed" | output.endorsed_tdocs |

※ TDoc 추출은 Item 추출과 함께 필수로 수행
※ TDoc이 없는 Item은 _warning 기록

---

**Item 경계 판단 원칙 (True Agentic AI)**

| 항목 | 내용 |
| --- | --- |
| 정의 | Item = 하나의 완결된 논의 흐름 |
| 시작 | 논의 트리거 (LS, CR Draft, Technical Question, Moderator Summary 시작) |
| 끝 | 결론 도출 (Agreement, Conclusion, Decision, No consensus, 다음 Summary 시작) |

---

**Item 중복 방지 규칙 (Deduplication)**

| 핵심 원칙 | 설명 |
| --- | --- |
| 1 Topic = 1 Item | 같은 주제의 여러 세션 논의는 하나의 Item으로 병합 |

**Topic 동일성 판단 기준**

| 기준 | 설명 | 예시 |
| --- | --- | --- |
| Summary 제목 | "Summary #N on {Topic}" 또는 "FLS#N on {Topic}" - {Topic} 부분이 동일 | "Summary #1 on beam" + "Summary #2 on beam" → 같은 Topic |
| FL Summary 제목 | "FL summary #N for {Topic}" 또는 "FLS#N on {Topic}" | "FLS#1 on evaluation" + "FLS#2 on evaluation" → 같은 Topic |
| TDoc 연속성 | 동일 TDoc 또는 revision 관계 | R1-2501410 → R1-2501520 (rev of R1-2501410) |
| 기술 주제 | 동일 기술 영역 논의 (LLM 의미 판단) | 같은 파라미터, 같은 기능에 대한 논의 |

**병합 규칙**

| 상황 | 처리 |
| --- | --- |
| Summary #1 → Summary #2 (같은 Topic) | 하나의 Item으로 병합 |
| Summary #1 on A → Summary #1 on B | 별도 Item (다른 Topic) |
| Monday Deferred → Thursday Agreed | status = Agreed (최종값만 기록) |
| 여러 세션에 걸친 논의 | session_info로 히스토리 추적 |

**경계 판단 명확화**

| 구분 | 조건 | 처리 |
| --- | --- | --- |
| 새 Item 경계 | **다른 Topic**으로 전환 | 새 Item 생성 |
| 같은 Item 내 | 같은 Topic의 "Summary #2", Comeback 논의 | 기존 Item에 병합 |

**병합 시 필드 처리**

| 필드 | 처리 방식 |
| --- | --- |
| resolution.status | 최종 상태만 기록 (Deferred → Agreed면 Agreed) |
| resolution.content | 모든 세션의 Agreement/Conclusion 등 누적 |
| session_info.first_discussed | 첫 논의 세션 |
| session_info.concluded | 최종 결론 세션 |
| session_info.comeback | true (여러 세션 걸친 경우) |
| input.moderator_summary | 모든 Summary TDoc 기록 (배열) |

**경계 판단 힌트** (참고용, 하드코딩 규칙 아님)

| 힌트 | 설명 |
| --- | --- |
| Moderator Summary 경계 | "Summary #1", "Summary #2" |
| Topic 전환 | 다른 주제로 넘어감 |
| TDoc 그룹 변화 | 새로운 TDoc 세트 시작 |
| Session 마커 | "From Monday session", "From Tuesday session" |

**Fallback**: 경계 판단이 어려운 경우 → Leaf Section 전체를 1개 Item으로 처리

※ 위는 힌트일 뿐, LLM이 **의미를 파악하여** 판단

---

**입력 (Section Agent로부터)**

| 항목 | 설명 |
| --- | --- |
| leaf_id | Leaf 식별자 |
| leaf_title | Leaf 제목 |
| leaf_content | Leaf 원본 텍스트 |
| section_type | 판단된 section_type |
| parent_context | 상위 섹션 정보 (5.1.1 참조) |
| meeting_info | 회의 메타데이터 |

---

**출력 파일 구조**

```yaml
# sections/{section_id}/{leaf_id}.yaml

leaf_id: "{leaf_id}"
title: "{leaf_title}"
section_type: "{section_type}"
subsection_agent: "{SubSection Agent 이름}"

items:
  - id: "..."
    context: {...}
    resolution: {...}
    # ... Item 상세 (3.3 스키마)

statistics:
  total_items: N
  by_status:
    Agreed: N
    Concluded: N
    # ...

_processing:
  generated_at: "ISO datetime"
  status: completed | partial | failed

```

---

**다른 섹션 참조**

| 내용 | 참조 |
| --- | --- |
| Item 스키마 | 3.3 |
| 마커 패턴 | 3.7 |
| TDoc 참조 패턴 | 3.6 |
| 에러 처리 | 3.3.3 (_error) |
| 프롬프트 | 6장 |

---

### 5.2.1 MaintenanceSubAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | Maintenance 관련 Leaf Section 처리 |
| 담당 section_type | Maintenance |
| 주요 특징 | CR(Change Request) 중심, 완료된 릴리즈 스펙 수정 |

**특징**

| 특징 | 설명 |
| --- | --- |
| CR 중심 | 기존 스펙의 수정/보완이 목적 |
| Moderator Summary 단위 | 논의가 Summary 단위로 정리됨 |
| Session 마커 | "From Monday session" 등으로 세션 구분 |
| Comeback 패턴 | 여러 세션에 걸쳐 논의되는 경우 많음 |

**Item 경계 판단 힌트**

| 우선순위 | 힌트 |
| --- | --- |
| 1 | Moderator Summary 경계 ("Summary on...", "Summary #2 on...") |
| 2 | Topic 전환 (다른 기술 주제로 넘어감) |
| 3 | TDoc 그룹 변화 (새로운 Draft CR 세트 시작) |
| Fallback | Leaf 전체를 1개 Item |

**주요 추출 필드**

| 필드 | 용도 | 참조 |
| --- | --- | --- |
| resolution.content | Agreement, Decision 등 | 3.3.2 |
| cr_info | CR 정보 (Maintenance 핵심) | 3.3.3 |
| session_info | 세션 추적 | 3.3.3 |
| topic | 논의 주제 요약 | 3.3.3 |

**출력 예시**

```yaml
# sections/8/8.1v1.yaml

leaf_id: "8.1v1"
title: "MIMO"
section_type: Maintenance
subsection_agent: MaintenanceSubAgent

items:
  - id: "RAN1_120_8.1v1_001"
    context:
      meeting_id: RAN1_120
      section_id: "8"
      leaf_id: "8.1v1"
      leaf_title: "MIMO"
      section_type: Maintenance

    topic:
      summary: "RRC parameter for PRACH transmission in 2TA enhancement"

    input:
      moderator_summary: "R1-2501422"

    resolution:
      status: Agreed
      content:
        - type: agreement
          text: "Introduce a new parameter to RACH-ConfigTwoTA-r18..."
          marker: "[Agreement]{.mark}"
        - type: decision
          text: "The LS is approved."
          marker: "**Decision:**"

    session_info:
      first_discussed: "Monday"
      concluded: "Tuesday"
      comeback: true

  - id: "RAN1_120_8.1v1_002"
    context:
      meeting_id: RAN1_120
      section_id: "8"
      leaf_id: "8.1v1"
      leaf_title: "MIMO"
      section_type: Maintenance

    topic:
      summary: "Timeline for STxMP"

    input:
      moderator_summary: "R1-2501444"

    resolution:
      status: Agreed
      content:
        - type: agreement
          text: "The following TP is agreed for 38.214 section 6.4..."
          marker: "[Agreement]{.mark}"

    cr_info:
      tdoc_id: "R1-2501564"
      spec: "38.214"
      cr_number: "CR0655"

    session_info:
      first_discussed: "Monday"
      concluded: "Tuesday"
      comeback: true

statistics:
  total_items: 2
  by_status:
    Agreed: 2

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 5.2.2 ReleaseSubAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | Release 관련 Leaf Section 처리 |
| 담당 section_type | Release |
| 주요 특징 | Agreement/Working Assumption 중심, 진행 중인 릴리즈 규격화 |

**특징**

| 특징 | 설명 |
| --- | --- |
| Agreement 중심 | 새로운 스펙 작성 방향 합의가 주요 활동 |
| Working Assumption | 아직 확정되지 않은 가정 |
| FFS 항목 | For Further Study - 추가 검토 필요 사항 |
| Noted 처리 | 개별 TDoc이 "noted" 처리되는 경우 있음 |

**MaintenanceSubAgent와의 차이**

| 항목 | MaintenanceSubAgent | ReleaseSubAgent |
| --- | --- | --- |
| 목적 | 기존 스펙 수정 | 새 스펙 작성 |
| 주요 결과물 | CR | Agreement |
| CR 비율 | 높음 | 낮음 |
| Working Assumption | 드뭄 | 자주 발생 |
| FFS | 드뭄 | 자주 발생 |

**Item 경계 판단 힌트**

| 우선순위 | 힌트 |
| --- | --- |
| 1 | FL Summary 경계 ("FL summary #0", "FL summary #1") |
| 2 | Moderator Summary 경계 |
| 3 | 기술 주제 전환 |
| Fallback | Leaf 전체를 1개 Item |

**주요 추출 필드**

| 필드 | 용도 | 참조 |
| --- | --- | --- |
| resolution.content | Agreement, Working Assumption, FFS 등 | 3.3.2 |
| session_info | 세션 추적 | 3.3.3 |
| topic | 논의 주제 요약 | 3.3.3 |

**출력 예시**

```yaml
# sections/9/9.1.1.yaml

leaf_id: "9.1.1"
title: "Specification support for beam management"
section_type: Release
subsection_agent: ReleaseSubAgent

items:
  - id: "RAN1_120_9.1.1_001"
    context:
      meeting_id: RAN1_120
      section_id: "9"
      leaf_id: "9.1.1"
      leaf_title: "Specification support for beam management"
      section_type: Release

    topic:
      summary: "AI/ML beam management - spatial domain DL beam prediction"

    input:
      moderator_summary: "R1-2501406"

    resolution:
      status: Agreed
      content:
        - type: agreement
          text: "For spatial domain DL beam prediction, support the following..."
          marker: "[Agreement]{.mark}"
        - type: working_assumption
          text: "For UE-sided model, the time gap is configured by RRC"
          marker: "[Working Assumption]{.mark}"
        - type: ffs
          text: "FFS: whether/how to support aperiodic CSI RS"
          marker: "FFS:"

    session_info:
      first_discussed: "Tuesday"
      concluded: "Thursday"
      comeback: false

  - id: "RAN1_120_9.1.1_002"
    context:
      meeting_id: RAN1_120
      section_id: "9"
      leaf_id: "9.1.1"
      leaf_title: "Specification support for beam management"
      section_type: Release

    resolution:
      status: Noted
      content:
        - type: decision
          text: "The document is noted."
          marker: "**Decision:**"

    session_info:
      first_discussed: "Tuesday"
      concluded: "Tuesday"
      comeback: false

statistics:
  total_items: 2
  by_status:
    Agreed: 1
    Noted: 1

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 5.2.3 StudySubAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | Study Item 관련 Leaf Section 처리 |
| 담당 section_type | Study |
| 주요 특징 | TR 작성 목적, Agreement/Observation/Conclusion 혼재 |

**특징**

| 특징 | 설명 |
| --- | --- |
| TR 중심 | TS가 아닌 TR(Technical Report) 작성이 목적 |
| 혼재된 결과 | Agreement, Observation, Conclusion이 모두 나타남 |
| Evaluation 데이터 | 시뮬레이션 파라미터, 성능 지표 정의 |
| Noted 처리 | 개별 TDoc이 "noted" 처리되는 경우 많음 |

**ReleaseSubAgent와의 차이**

| 항목 | ReleaseSubAgent | StudySubAgent |
| --- | --- | --- |
| 목적 | TS 스펙 작성 | TR 보고서 작성 |
| 주요 결과 | Agreement | Agreement, Observation, Conclusion |
| CR | Draft CR 가능 | 거의 없음 |

**Item 경계 판단 힌트**

| 우선순위 | 힌트 |
| --- | --- |
| 1 | Summary 경계 ("Summary #1 on...", "FL Summary #2") |
| 2 | 기술 주제 전환 |
| 3 | Noted TDoc 그룹 |
| Fallback | Leaf 전체를 1개 Item |

**주요 추출 필드**

| 필드 | 용도 | 참조 |
| --- | --- | --- |
| resolution.content | Agreement, Conclusion, Observation, FFS 등 | 3.3.2 |
| tr_info | TR 정보 (Study 핵심) | 3.3.3 |
| session_info | 세션 추적 | 3.3.3 |
| topic | 논의 주제 요약 | 3.3.3 |

**출력 예시**

```yaml
# sections/9/9.7.1.yaml

leaf_id: "9.7.1"
title: "ISAC deployment scenarios"
section_type: Study
subsection_agent: StudySubAgent

items:
  - id: "RAN1_120_9.7.1_001"
    context:
      meeting_id: RAN1_120
      section_id: "9"
      leaf_id: "9.7.1"
      leaf_title: "ISAC deployment scenarios"
      section_type: Study

    topic:
      summary: "ISAC 채널 모델링 calibration 접근법"

    input:
      moderator_summary: "R1-2501076"

    resolution:
      status: Concluded
      content:
        - type: conclusion
          text: "For ISAC channel modelling calibration, RAN1 considers both large-scale and full-scale calibration"
          marker: "[Conclusion]"
        - type: observation
          text: "Large scale parameters do not include fast fading"
          marker: "[Observation]"
        - type: ffs
          text: "FFS: additional calibration for the combined channel"
          marker: "FFS:"

    tr_info:
      tr_number: "TR 38.901"
      update_tdoc: "R1-2501640"

    session_info:
      first_discussed: "Wednesday"
      concluded: "Thursday"
      comeback: false

statistics:
  total_items: 1
  by_status:
    Concluded: 1

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 5.2.4 UEFeaturesSubAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | UE Features 섹션 처리 |
| 담당 section_type | UE_Features |
| 주요 특징 | Feature Group(FG) 정의, Work Item별 정리 |

**특징**

| 특징 | 설명 |
| --- | --- |
| Work Item별 구분 | AI/ML, MIMO, SBFD 등 Work Item별로 섹션 분리 |
| Feature Group 정의 | UE 기능을 FG 단위로 정의 |
| 구조화된 포맷 | FG name, Component, Prerequisite 등 정형화된 구조 |
| Session Notes | 각 서브섹션에 Session Notes TDoc이 있음 |

**다른 SubSection Agent와의 차이**

| 항목 | 다른 SubSection Agent | UEFeaturesSubAgent |
| --- | --- | --- |
| Item 경계 | Moderator Summary 단위 | Work Item 또는 Feature Group 단위 |
| 주요 마커 | [Agreement], [Conclusion] | [Agreement:] + FG 정의 구조 |
| 결과물 | CR, Agreement | Feature Group 정의 |

**Item 경계 판단 힌트**

| 우선순위 | 힌트 |
| --- | --- |
| 1 | Work Item 서브섹션 ("UE features for AI/ML") |
| 2 | Summary 문서 단위 |
| Fallback | 전체 UE Features = 1 Item |

**FG 추출 규칙**

| 상황 | 처리 |
| --- | --- |
| FG 정의가 본문에 있음 | resolution.content에 추출 |
| FG 정의가 Session Notes에만 있음 | 본문 내용만 추출 + 참조 노트 |

※ Session Notes TDoc 내용은 추출 범위 밖 (본문만 처리)

**주요 추출 필드**

| 필드 | 용도 | 참조 |
| --- | --- | --- |
| resolution.content | Agreement (FG 정의 포함) | 3.3.2 |
| input | Summary TDoc | 3.3.3 |
| topic | Work Item 정보 | 3.3.3 |

**출력 예시**

```yaml
# sections/8/8.2.yaml

leaf_id: "8.2"
title: "Rel-18 UE Features"
section_type: UE_Features
subsection_agent: UEFeaturesSubAgent

items:
  - id: "RAN1_120_8.2_001"
    context:
      meeting_id: RAN1_120
      section_id: "8"
      leaf_id: "8.2"
      leaf_title: "Rel-18 UE Features"
      section_type: UE_Features

    topic:
      summary: "Rel-18 UE Features for MIMO"

    input:
      moderator_summary: "R1-2501385"

    resolution:
      status: Agreed
      content:
        - type: agreement
          text: "Introduce following FG for UE 8Tx PUSCH processing capability for codebook: FG name: ..., Component: ..., Prerequisite: 40-7-1, Type: Per FS"
          marker: "[Agreement:]"
        - type: agreement
          text: "Introduce following FG for UE 8Tx PUSCH processing capability for non-codebook"
          marker: "[Agreement:]"

statistics:
  total_items: 1
  by_status:
    Agreed: 1

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 5.2.5 LSSubAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | Incoming LS 섹션 처리 |
| 담당 section_type | LS |
| 주요 특징 | 수신 LS별 처리 결과 추출, 1 LS = 1 Item |

**특징**

| 특징 | 설명 |
| --- | --- |
| LS 단위 처리 | 각 수신 LS가 하나의 Item |
| Decision 중심 | Agreement 대신 Decision 마커 사용 |
| 회신 여부 | Reply LS 작성 여부가 주요 결과 |
| Release/Topic 그룹핑 | LS들이 Release 또는 Topic별로 묶여있음 |

**다른 SubSection Agent와의 차이**

| 항목 | 기술 논의 SubAgent | LSSubAgent |
| --- | --- | --- |
| Item 경계 | Moderator Summary 단위 | 수신 LS 단위 |
| 주요 마커 | [Agreement], [Conclusion] | **Decision:** |
| 결과물 | CR, Agreement | Reply LS 여부 |

**Item 경계 판단 힌트**

| 우선순위 | 힌트 |
| --- | --- |
| 1 | LS TDoc 단위 (각 수신 LS TDoc이 하나의 Item) |
| Fallback | Release 그룹 단위 |

**주요 추출 필드**

| 필드 | 용도 | 참조 |
| --- | --- | --- |
| resolution.content | Decision | 3.3.2 |
| ls_in | Incoming LS 정보 | 3.3.3 |
| ls_out | 응답 정보 | 3.3.3 |

---

**LS 섹션 원본 구조**

```
# Incoming Liaison Statements

{그룹 헤더}                    ← release_category
{LS 헤더}                     ← ls_in 필드들
{Relevant TDocs}              ← input.discussion_tdocs
{Decision}                    ← resolution + handling
...반복...
{CC-only 섹션}                ← cc_only: true
{주중 수신 섹션}               ← received_during_week: true

```

---

**패턴 → 필드 매핑**

| 원본 패턴 | 추출 필드 | 추출 규칙 |
| --- | --- | --- |
| `**Rel-{버전} {주제}**` 또는 `**[Rel-{버전} {주제}]{.underline}**` | release_category | 볼드 그룹 헤더 |
| `**[{TDoc}](link) {title} {wg}, {company}**` | ls_in.* | 쉼표 기준 분리 |
| `**Relevant tdocs:**` 또는 `**Relevant Tdoc(s)**` 아래 목록 | input.discussion_tdocs | **Decision:** 전까지 |
| `"agenda item {번호} ({주제})"` | handling.agenda_item, topic | Decision 내 |
| `"- {이름} ({회사})"` | handling.moderator, moderator_company | Decision 끝 |
| `"To be handled in next meeting {회의}"` | handling.deferred_to | Decision 내 |
| `"cc-ed"` 또는 `"cc-"` 포함 섹션 헤더 | cc_only: true | 섹션 구분 |
| `"during the week"` 포함 섹션 헤더 | received_during_week: true | 섹션 구분 |

---

**LS 헤더 파싱 규칙**

1. 볼드 블록 내 첫 번째 링크에서 tdoc_id 추출
2. 링크 뒤 텍스트에서 마지막 쉼표 찾기
3. 쉼표 앞: 제목 + source_wg (마지막 단어가 source_wg)
4. 쉼표 뒤: source_company
5. 쉼표 없으면 source_company = null

**예시**:

- 원본: `*[R1-2500012](link) LS on UL 8Tx RAN2, Samsung**`
- 추출: tdoc_id=R1-2500012, title="LS on UL 8Tx", source_wg="RAN2", source_company="Samsung"

---

**Relevant TDocs 추출 규칙**

1. 시작 마커: `*Relevant tdocs:**` 또는 `*Relevant Tdoc(s)**` (대소문자 무관)
2. 종료 조건: `*Decision:**` 또는 다음 LS 헤더 또는 다음 그룹 헤더
3. 각 줄 파싱: `[{TDoc}](link) {title} {company}` → 마지막 단어가 company

---

**LS 내 추가 결과 (Conclusion/Agreement)**

일부 LS에서 Decision 뒤에 추가 결과가 있을 수 있음:

```
**Decision:** ... To be handled in agenda item 8.3

**Conclusion**
Based on RAN4 reply LS...

[Agreement]{.mark}
Adopt the following reply...

```

→ 발견 시 resolution.content 배열에 추가

**출력 예시**

```yaml
# sections/5/5.yaml

leaf_id: "5"
title: "Incoming Liaison Statements"
section_type: LS
subsection_agent: LSSubAgent

items:
  - id: "RAN1_120_5_001"
    context:
      meeting_id: RAN1_120
      section_id: "5"
      leaf_id: "5"
      leaf_title: "Incoming Liaison Statements"
      section_type: LS

    ls_in:
      tdoc_id: "R1-2500007"
      title: "LS response on waveform determination for PUSCH"
      source: "RAN2"

    ls_out:
      action: No_Action
      reply_tdoc: null

    resolution:
      status: Noted
      content:
        - type: decision
          text: "No further action necessary from RAN1."
          marker: "**Decision:**"

  - id: "RAN1_120_5_002"
    context:
      meeting_id: RAN1_120
      section_id: "5"
      leaf_id: "5"
      leaf_title: "Incoming Liaison Statements"
      section_type: LS

    ls_in:
      tdoc_id: "R1-2500012"
      title: "LS on UL 8Tx"
      source: "RAN2"

    ls_out:
      action: Replied
      reply_tdoc: "R1-2501500"

    resolution:
      status: Noted
      content:
        - type: decision
          text: "RAN1 response is necessary and to be handled in agenda item 8.1 (MIMO)"
          marker: "**Decision:**"

statistics:
  total_items: 2
  by_status:
    Noted: 2

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 5.2.6 AnnexSubAgent

**역할**

| 항목 | 내용 |
| --- | --- |
| 역할 | Annex 섹션 처리 (크로스체크용) |
| 담당 section_type | Annex |
| 처리 대상 | B, C-1, C-2만 |

※ Annex A, D~H는 skip 처리 (4.2.4 참조)

**처리 대상 Annex**

| Annex | 내용 | 크로스체크 대상 |
| --- | --- | --- |
| B | List of CRs | 본문 cr_info |
| C-1 | List of Outgoing LSs | 본문 ls_out |
| C-2 | List of Incoming LSs | Section 5 LS |

**다른 SubSection Agent와의 차이**

| 항목 | 기술 논의 SubAgent | AnnexSubAgent |
| --- | --- | --- |
| 처리 방식 | Item 추출 | 목록 파싱 |
| 출력 위치 | sections/ | annexes/ |
| 목적 | 논의 결과 추출 | 크로스체크 데이터 |

**출력**

```yaml
# annexes/annex_b.yaml

annex_id: annex_b
title: "List of CRs agreed at RAN1 #120"

entries:
  - tdoc_id: "R1-2501501"
    title: "Correction on transition time..."
    source: "vivo"
    spec: "TS 38.213"
    cr_number: "0693"
  - tdoc_id: "R1-2501502"
    title: "CR on PSCCH DMRS..."
    source: "CATT"
    spec: "TS 38.211"
    cr_number: "0148"

statistics:
  total_entries: 25

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

※ Annex 스키마 상세는 3.7 참조

---

### 5.2.7 에러 처리

| 상황 | 처리 |
| --- | --- |
| Item 경계 판단 실패 | Leaf 전체를 1개 Item으로 처리 |
| 필수 필드 추출 실패 | _error 기록 → Human Review |
| 마커 인식 실패 | 가능한 내용 추출 + _error 기록 |

※ _error 구조는 3.3.3 참조
※ 프롬프트는 6장 참조

---

---

### 5.3 확장 원칙

### 5.3.0 개요

| 항목 | 설명 |
| --- | --- |
| 목적 | 새로운 Agent, section_type, 필드 추가 시 가이드라인 |
| 핵심 | 1장 핵심 원칙 준수 (의미 기반 판단, 일반화, 검증 가능성) |

---

### 5.3.1 확장 대상별 판단 기준

**Section Agent 확장**

| 상황 | 판단 |
| --- | --- |
| 기존 Agent로 처리 가능 | 확장 불필요 ✗ |
| 완전히 새로운 섹션 구조 | 새 Agent 검토 ○ |
| 기존 Agent 로직과 충돌 | 새 Agent 검토 ○ |

※ 현재 Section Agent 3종: 5.1 참조

---

**SubSection Agent 확장**

| 상황 | 판단 |
| --- | --- |
| 기존 Agent로 처리 가능 | 확장 불필요 ✗ |
| 추출 구조가 근본적으로 다름 | 새 Agent 검토 ○ |
| 새로운 필드 구조 필요 | 새 Agent 검토 ○ |

※ 현재 SubSection Agent 6종: 5.2 참조

---

**section_type 확장**

| 상황 | 판단 |
| --- | --- |
| 기존 section_type으로 분류 가능 | 확장 불필요 ✗ |
| 처리 방식이 근본적으로 다름 | 새 section_type 검토 ○ |

※ 현재 section_type 7종: 4.2.2 참조

---

**필드 확장**

| 대상 | 확장 조건 |
| --- | --- |
| resolution.content.type | 기존 type으로 표현 불가능한 새 마커 발견 시 |
| 선택 필드 | 기존 필드로 표현 불가능한 정보 필요 시 |

※ 현재 정의된 필드: 3.3 참조

---

### 5.3.2 확장 시 필수 정의 항목

**Section Agent 추가 시**

| 항목 | 설명 |
| --- | --- |
| 역할 | Agent의 책임 범위 |
| 담당 section_type | 처리할 section_type 목록 |
| 호출 SubSection Agent | 사용할 SubSection Agent |
| 판단 기준 | 의미 기반 힌트 |
| 출력 구조 | _index.yaml 구조 |

---

**SubSection Agent 추가 시**

| 항목 | 설명 |
| --- | --- |
| 역할 | Agent의 책임 범위 |
| 담당 section_type | 처리할 section_type |
| Item 경계 판단 힌트 | 의미 기반 힌트 |
| 사용 필드 | 필수/선택 필드 (3.3 참조) |
| 프롬프트 | 6장 형식 준수 |

---

**section_type 추가 시**

| 항목 | 설명 |
| --- | --- |
| 이름 | PascalCase |
| 판단 기준 | 의미 기반 힌트 |
| 처리 방식 | skip / Item 추출 / 별도 스키마 |
| 담당 Agent | Section Agent + SubSection Agent |

---

**필드 추가 시**

| 대상 | 규칙 |
| --- | --- |
| content.type | snake_case, 원문 마커 기반 |
| 선택 필드 | snake_case, `_info` suffix 권장, optional |

---

### 5.3.3 공통 체크리스트

```
□ 기존 구성요소로 처리 불가능한지 확인
□ 명명 규칙 준수 (section_type: PascalCase, 필드: snake_case)
□ 판단 기준 정의 (의미 기반, 하드코딩 금지)
□ 관련 구성요소 연결 정의 (Agent ↔ section_type ↔ 필드)
□ 스키마 문서 업데이트 (3.3, 4.2.2 등)
□ 프롬프트 작성 (6장)
□ 실제 문서로 검증 (최소 2개 회의록)
□ 하위 호환성 확인 (기존 출력 영향 없음)

```

---

### 5.3.4 금지 사항

| 금지 사항 | 대안 |
| --- | --- |
| 섹션 번호 하드코딩 | 의미 기반 판단 (1장 참조) |
| 특정 회의 종속 로직 | 패턴 기반 힌트 |
| 기존 구성요소 의미 변경 | 새 구성요소 추가 |
| 필수 필드 삭제/변경 | optional 필드로 추가 |
| 검증 없는 배포 | 최소 2개 문서 테스트 |

---

### 5.3.5 확장 예시

**예시 1: 구조 확장 - "Joint Session" 섹션**

```
가정: "Joint Session with RAN2" 섹션 등장

판단:
1. TechnicalAgent로 처리 시도
2. 구조가 맞지 않으면 신규 검토

필요 시 추가:
- section_type: Joint_Session
- Section Agent: TechnicalAgent 확장 또는 JointSessionAgent 신규
- SubSection Agent: 기존 재사용 또는 JointSessionSubAgent 신규
- 선택 필드: joint_info (participating_wgs, host_wg)

```

---

**예시 2: 필드 확장 - 새 마커 "Proposal"**

```
가정: **Proposal:** 마커가 반복 등장

판단:
1. 기존 content.type (agreement, conclusion 등)으로 표현 가능? → 의미 다름
2. 신규 추가 결정

적용:
- content.type에 "proposal" 추가
- 3.3.2 권장 값 목록 업데이트

```

---

**관련 참조**

| 내용 | 참조 |
| --- | --- |
| 핵심 원칙 | 1장 |
| Item 스키마 | 3.3 |
| section_type 판단 기준 | 4.2.2 |
| Section Agent | 5.1 |
| SubSection Agent | 5.2 |
| 프롬프트 | 6장 |
| 에러 처리 | 3.3.3 (_error) |

## 6. 프롬프트 설계

### 6.1 프롬프트 설계 원칙

**개요**

| 항목 | 설명 |
| --- | --- |
| 목적 | LLM이 3GPP 회의록을 정확히 파싱하도록 가이드 |
| 핵심 | 1장 핵심 원칙 반영 (의미 기반, 일반화, 검증 가능) |
| 적용 대상 | TOCAgent, 청킹, SubSection Agent |

---

**원칙 1: 의미 기반 판단 (True Agentic AI)**

| 항목 | 설명 |
| --- | --- |
| 정의 | 하드코딩 규칙 대신 LLM의 문맥 이해에 의존 |
| 적용 | 섹션 경계, Item 경계, Type 판단 |
| 프롬프트 표현 | "~로 판단하라"가 아닌 "~를 참고하여 의미에 따라 판단하라" |

**예시**

```
❌ 하드코딩:
"Section 9는 Release로 처리하라"

✅ 의미 기반:
"섹션 제목에 'Release XX' 패턴이 있으면 Release일 가능성이 높다.
 단, 제목의 전체 의미를 파악하여 최종 판단하라."

```

---

**원칙 2: 힌트 제공 (규칙 아님)**

| 항목 | 설명 |
| --- | --- |
| 정의 | 판단을 돕는 패턴/키워드 제공, 강제하지 않음 |
| 적용 | 마커 패턴, 경계 키워드, 구조 힌트 |
| 프롬프트 표현 | "~이면 ~일 가능성이 높다", "~를 참고하라" |

---

**원칙 3: 출력 스키마 명시**

| 항목 | 설명 |
| --- | --- |
| 정의 | 기대하는 출력 구조를 명확히 제시 |
| 적용 | 모든 프롬프트에 출력 스키마 포함 |
| 참조 | 3.3 Item 스키마, 3.4 Annex 스키마 |

---

**원칙 4: Fallback 전략**

| 상황 | Fallback |
| --- | --- |
| Item 경계 판단 실패 | Leaf 전체를 1개 Item으로 |
| section_type 판단 실패 | unknown으로 표시 |
| content.type 판단 실패 | 가장 유사한 기존 type 사용 |
| 필수 필드 추출 실패 | _error 기록 |

---

**원칙 5: 원문 용어 보존**

| 항목 | 설명 |
| --- | --- |
| 정의 | 3GPP 원문 용어를 그대로 사용 |
| 적용 | 마커, 상태값, 기술 용어 |

```
✅ marker: "[Agreement]{.mark}"  # 원문 그대로
❌ marker: "Agreement"           # 마커 형식 손실

```

---

**원칙 6: 검증 가능성**

| 항목 | 설명 |
| --- | --- |
| 정의 | 추출 결과에 근거 포함 |
| 적용 | marker 필드, source_docs, _error |

---

### 6.2 공통 프롬프트 요소

**개요**

| 항목 | 설명 |
| --- | --- |
| 목적 | 여러 Agent에서 공통으로 사용하는 프롬프트 요소 |
| 원칙 | 패턴 정의는 3장 참조, 프롬프트 지시 방법만 정의 |

---

### 6.2.1 패턴 참조

| 패턴 | 참조 | 프롬프트 용도 |
| --- | --- | --- |
| 마커 패턴 | 3.7 | content.type 결정 |
| TDoc 참조 패턴 | 3.6 | input, cr_info, ls_in 등 필드 매핑 |
| Session 마커 | 3.3.3 session_info | session_info 추출 |

---

### 6.2.1.1 Session 마커 추출

**목적**: session_info 필드 추출을 위한 원문 패턴 인식

**원문 패턴**

| 패턴 | 의미 | 예시 |
| --- | --- | --- |
| `From {요일} session` | 해당 요일 세션 내용 시작 | `From Monday session` |
| `Presented in {요일} session` | 해당 요일에 발표됨 | `Presented in Wednesday session.` |
| `{요일} session (continued)` | 이전 세션에서 이어짐 | `Tuesday session (continued)` |
| `Comeback` / `Come back` | 재논의 예정 | `Comeback on Thursday`, `Come back in RAN1#120bis` |
| `continued from {요일}` | 이전 세션에서 계속 | `continued from Monday` |

**추출 로직**

| 필드 | 추출 방법 |
| --- | --- |
| first_discussed | 첫 번째로 등장하는 요일 |
| concluded | 마지막으로 등장하는 요일 (결론이 있는 세션) |
| comeback | `Comeback`, `continued`, `revisited` 키워드 존재 여부 |

**원문 예시**

```
From Monday session

The following document was discussed:
- [R1-2501410](...)

...논의 내용...

Comeback on Thursday

From Thursday session

[Agreement]{.mark}
For spatial domain DL beam prediction, support the following...

```

**추출 결과**

```yaml
session_info:
  first_discussed: "Monday"
  concluded: "Thursday"
  comeback: true

```

**요일 정규화**

| 원문 변형 | 정규화 값 |
| --- | --- |
| Monday, Mon, monday | Monday |
| Tuesday, Tue, tuesday | Tuesday |
| Wednesday, Wed, wednesday | Wednesday |
| Thursday, Thu, thursday | Thursday |
| Friday, Fri, friday | Friday |

**Fallback 규칙**

| 상황 | 처리 |
| --- | --- |
| 요일 마커 없음 | session_info 필드 전체 생략 |
| 요일 1개만 발견 | first_discussed = concluded = 해당 요일, comeback = false |
| 결론 없이 Comeback만 | concluded 생략, comeback = true |

---

### 6.2.2 프롬프트 지시 원칙

**패턴 인식 → 필드 매핑**

```
패턴을 인식하여 적절한 필드에 매핑하라:
- 마커 패턴 (3.7 참조) → resolution.content.type
- TDoc 패턴 (3.7 참조) → 용도에 따라 input, cr_info, ls_in 등
- Session 마커 → session_info

```

**원문 보존**

```
다음 필드는 원문을 그대로 보존하라:
- marker: 마커 원문 (예: "[Agreement]{.mark}")
- text: 추출된 텍스트 원문
- title: 섹션/Item 제목 원문

```

**새로운 패턴 발견 시**

```
3장에 정의되지 않은 새로운 패턴 발견 시:
1. 기존 패턴과 유사하면 기존 type/필드 사용
2. 명확히 다르면 새 type 생성 (snake_case)
3. marker 필드에 원문 기록하여 추적 가능하게

```

---

### 6.2.3 에러 처리

**_error 생성 조건**

| 상황 | error_type |
| --- | --- |
| 필수 필드 추출 실패 | missing_required_field |
| 마커 인식 실패 | unrecognized_marker |
| 경계 판단 실패 | boundary_detection_failed |
| 내용 파싱 실패 | parsing_failed |

※ _error 구조는 3.3.3 참조

---

### 6.3 TOCAgent 프롬프트

**개요**

| 항목 | 설명 |
| --- | --- |
| 역할 | section_type 판단, Virtual Numbering, skip 여부 결정 |
| 입력 | **toc_raw.yaml** (전처리에서 추출된 TOC 구조) |
| 출력 | toc.yaml |

※ TOC 파싱은 4.0 전처리에서 완료됨 (python-docx 기반)
※ TOCAgent는 이미 구조화된 toc_raw.yaml을 받아 의미 판단만 수행

---

---

### 6.3.1 입력 처리 (toc_raw.yaml)

**입력 구조**

TOCAgent는 전처리(4.0)에서 생성된 toc_raw.yaml을 입력으로 받음:

```yaml
# toc_raw.yaml 예시
entries:
  - text: "1 Opening of the meeting"
    style: "TOC 1"
    depth: 1
    page: 5
    anchor: "opening-of-the-meeting"
  - text: "8.1 Maintenance on Rel-18 work items"
    style: "TOC 2"
    depth: 2
    page: 14
    anchor: "maintenance-on-rel-18-work-items"
  - text: "MIMO"
    style: "TOC 3"
    depth: 3
    page: 14
    anchor: "mimo"
    unnumbered: true

```

**이미 제공되는 정보**

| 필드 | 설명 | TOCAgent 역할 |
| --- | --- | --- |
| text | 섹션 번호 + 제목 | 그대로 사용 |
| style | Word TOC 스타일 | 사용 안 함 |
| depth | 계층 깊이 | 그대로 사용 |
| page | 페이지 번호 | 탐색 범위 힌트 (LLM 경계 판단 전 범위 축소용) |
| anchor | 링크 앵커 | 그대로 사용 |
| unnumbered | 번호 없는 섹션 여부 | Virtual Numbering 트리거 |

**TOCAgent가 추가할 정보**

| 필드 | 설명 | 판단 기준 |
| --- | --- | --- |
| id | 섹션 번호 (또는 가상 번호) | text에서 추출 또는 생성 |
| title | 섹션 제목 | text에서 번호 제외 |
| parent | 상위 섹션 id | depth 기반 계산 |
| children | 하위 섹션 id 목록 | depth 기반 계산 |
| section_type | 콘텐츠 유형 | **의미 기반 판단** |
| skip | 처리 제외 여부 | section_type 기반 |
| virtual | 가상 번호 여부 | unnumbered=true 시 |

**섹션 번호 추출**

```
text: "9.1.1 Beam management"
  → id: "9.1.1"
  → title: "Beam management"

text: "MIMO" (unnumbered: true)
  → id: 가상 번호 부여 필요
  → title: "MIMO"

```

---

---

### 6.3.2 section_type 판단

**판단 기준** (4.2.2 참조)

```
섹션 제목을 분석하여 section_type을 판단하라.
섹션 번호가 아닌 제목의 의미로 판단한다.

판단 우선순위:
1. "Annex" → Annex
2. "Liaison" → LS
3. "Opening", "Closing", "Approval", "Highlights" → Procedural
4. "UE Features" → UE_Features
5. "Study", "SI" → Study
6. "Maintenance", "Pre-Rel" → Maintenance
7. "Release XX" → Release

상속 규칙:
- 제목에 키워드가 있으면 개별 판단
- 없으면 상위 section_type 상속

불확실한 경우:
- unknown으로 표시
- Orchestrator에서 재판단 (4.3.7 참조)

※ Orchestrator의 unknown 재판단:
- TOCAgent가 unknown으로 판단한 경우
- Orchestrator가 Leaf content 일부를 보고 동일 기준으로 재판단
- 상세 흐름은 4.3.7 참조
```

---

### 6.3.3 Virtual Numbering

**번호 없는 섹션 식별**

```
toc_raw.yaml에서 unnumbered: true로 이미 표시됨

입력 예시:
  - text: "MIMO"
    style: "TOC 3"
    depth: 3
    unnumbered: true

TOCAgent는 unnumbered: true인 항목에 가상 번호 부여

```

**Virtual Numbering 생성**

```
번호 없는 섹션에 가상 번호 부여:

형식: {parent_id}v{sequence}
예시:
- 8.1 하위 첫 번째 unnumbered → 8.1v1
- 8.1 하위 두 번째 unnumbered → 8.1v2

출력:
- id: "8.1v1"
  title: "MIMO"
  virtual: true
  parent: "8.1"

```

---

### 6.3.4 skip 판단

**skip 대상** (4.2.4 참조)

```
다음 섹션은 skip: true로 표시:

1. Procedural 섹션:
   - Opening, Closing, Approval 등
   - skip_reason: "Procedural section"

2. 일부 Annex:
   - A, D, E, F, G, H
   - skip_reason: "Not in crosscheck scope"

skip하지 않는 Annex:
- B (CR 목록)
- C-1 (Outgoing LS)
- C-2 (Incoming LS)

```

---

### 6.3.5 출력 스키마

```yaml
# toc.yaml
meeting_id: "{회의 ID}"

sections:
  - id: "{섹션 번호 또는 가상 번호}"
    title: "{섹션 제목}"
    depth: {1-4}
    parent: "{상위 섹션 id}" # null if depth 1
    children: ["{하위 섹션 id}", ...]
    section_type: "{Procedural|Maintenance|Release|Study|UE_Features|LS|Annex|unknown}"
    skip: {true|false}
    skip_reason: "{skip 사유}" # skip: true일 때만
    virtual: {true|false} # 가상 번호일 때만

```

---

### 6.3.6 unknown 재판단 프롬프트 (Orchestrator용)

**적용 시점**: TOCAgent가 section_type을 unknown으로 판단한 경우, Orchestrator가 Leaf content 일부를 보고 재판단

```
# 역할
당신은 3GPP RAN1 회의록의 섹션 유형을 판단하는 전문가입니다.

# 배경
TOC 분석 단계에서 이 섹션의 section_type을 판단하지 못했습니다.
섹션 내용의 일부를 보고 section_type을 결정해주세요.

# 입력
- section_id: {section_id}
- section_title: {section_title}
- content_preview: (첫 2000자)
{content_preview}

# 판단 기준 (내용 패턴 기반)

| 내용 패턴 | section_type |
|-----------|--------------|
| CR, Draft CR, Editorial, Correction 언급 다수 | Maintenance |
| Agreement 중심, 새 기능 정의, Working Assumption | Release |
| TR, Observation, Study, Evaluation 언급 | Study |
| Feature Group, FG 정의, UE capability | UE_Features |
| LS 응답, Reply, "handled in agenda item" | LS |

# 판단 프로세스
1. content_preview에서 위 패턴을 찾는다
2. 가장 많이 나타나는 패턴의 section_type을 선택한다
3. 패턴이 불명확하면 Release를 기본값으로 사용한다

# 출력 형식
다음 형식으로 출력:

section_type: "{Maintenance|Release|Study|UE_Features|LS}"
confidence: {0.0~1.0}
reason: "{판단 근거 1줄}"

# 예시 출력
section_type: "Maintenance"
confidence: 0.8
reason: "Draft CR, editorial correction 패턴이 다수 발견됨"

```

**Fallback 규칙**

| 상황 | 처리 |
| --- | --- |
| confidence < 0.5 | _warning 기록 + Release 기본 할당 |
| 재판단 후에도 판단 불가 | TechnicalAgent에 Release로 할당 + Human Review 트리거 |

---

### 6.3.7 배치 처리 시 프롬프트 구성

※ 이 섹션은 4.2.8 "대용량 TOC 처리"의 프롬프트 구현 가이드입니다.
※ 처리 원칙, 파라미터, 재요청 규칙은 4.2.8 참조

**프롬프트 템플릿**

```
# 역할
당신은 3GPP RAN1 회의록의 목차(TOC)를 분석하는 전문가입니다.

# 작업
주어진 섹션들의 section_type을 판단하세요.

# 중요
**반드시 입력된 모든 섹션에 대해 응답해야 합니다.**
누락 없이 N개 섹션 모두에 대해 출력하세요.

# section_type 판단 기준 (우선순위)
1. "Annex" → Annex
2. "Liaison" → LS
3. "Opening", "Closing", "Approval", "Highlights" → Procedural
4. "UE Features" → UE_Features
5. "Study", "SI" → Study
6. "Maintenance", "Pre-Rel" → Maintenance
7. "Release XX" → Release

키워드가 없으면 부모 컨텍스트에서 상속.
판단 불가 시 unknown.

# 부모 컨텍스트 (이전 배치 결과)
다음은 상위 섹션의 section_type입니다. 상속 판단에 참고하세요:
{parent_context}

# 입력 섹션 ({N}개)
{batch_sections}

# 출력 형식
sections:
  - id: "..."
    section_type: "..."
    type_reason: "..."
    skip: ...
  # ... (총 {N}개)

```

---

### 6.4 청킹 프롬프트

**개요**

| 항목 | 설명 |
| --- | --- |
| 역할 | 대용량 Leaf를 의미 단위로 분할 |
| 호출 주체 | Section Agent 내부 |
| 판단 | 토큰 수 (코드) → 경계 결정 (LLM) |
| 조건 | Leaf 내용이 컨텍스트 한계 초과 시 |

---

### 6.4.1 청킹 필요 판단

```
청킹 판단 기준:

1. 토큰 수 기반 (코드에서 판단)
2. LLM은 청킹 경계만 결정

청킹 원칙:
- 하나의 Item이 쪼개지지 않도록
- 의미 단위로 분할 (True Agentic AI)

```

---

### 6.4.2 section_type별 청킹 경계

```
section_type별 청킹 경계 힌트:

Maintenance, Release, Study:
- Moderator Summary 경계 ("Summary #1 on...", "FL summary #2...")
- 다른 기술 주제로 전환되는 지점
- "From {요일} session" 마커

UE_Features:
- Work Item 경계 ("UE features for AI/ML", "UE features for MIMO")
- Feature Group 그룹 경계

LS:
- 개별 LS 항목 경계 (각 수신 LS TDoc)
- Release 그룹 경계 ("Rel-18", "Rel-19")

Annex:
- 표/목록 경계
- 자연스러운 행 그룹

```

---

### 6.4.3 출력

```yaml
# 청킹 결과
chunks:
  - chunk_id: 1
    start_marker: "Summary #1 on beam management"
    end_marker: "Summary #2 on positioning"
    estimated_items: 3
  - chunk_id: 2
    start_marker: "Summary #2 on positioning"
    end_marker: "[끝]"
    estimated_items: 2

```

---

### 6.4.4 청킹 프롬프트 템플릿

```
# 역할
당신은 3GPP RAN1 회의록의 대용량 섹션을 의미 단위로 분할하는 전문가입니다.

# 작업
주어진 Leaf 내용을 Item이 쪼개지지 않도록 청크로 분할하세요.

# 입력
- leaf_id: {leaf_id}
- leaf_title: {leaf_title}
- section_type: {section_type}
- content_tokens: {토큰 수}
- leaf_content:
{leaf_content 전체}

# 청킹 원칙
1. 하나의 Item이 여러 청크에 쪼개지면 안 됨
2. 의미 단위로 분할 (토큰 수가 아닌 내용 기준)
3. 각 청크는 독립적으로 처리 가능해야 함

# section_type별 청킹 경계 힌트

Maintenance, Release, Study:
- "Summary #N on..." 또는 "FL summary #N..." 경계
- "From {요일} session" 마커
- 기술 주제 전환점

UE_Features:
- "UE features for {Work Item}" 경계
- Feature Group 그룹 전환점

LS:
- 개별 LS TDoc 경계
- Release 그룹 경계 ("Rel-18", "Rel-19")

# 출력 형식
다음 YAML 형식으로 출력:

chunks:
  - chunk_id: 1
    start_marker: "{청크 시작을 식별하는 텍스트}"
    end_marker: "{청크 끝을 식별하는 텍스트}"
    estimated_items: {예상 Item 수}
  - chunk_id: 2
    start_marker: "..."
    end_marker: "..."
    estimated_items: ...

# 주의사항
- start_marker와 end_marker는 원문에서 찾을 수 있는 고유한 텍스트여야 함
- 마지막 청크의 end_marker는 "[섹션 끝]"으로 표시
- 경계 판단이 어려우면 청크를 크게 잡아 Item이 쪼개지지 않도록 함

```

### 6.5 SubSection Agent 프롬프트

**6.5.0 공통**

**개요**

| 항목 | 설명 |
| --- | --- |
| 역할 | Leaf 내용에서 Item 추출 |
| 입력 | leaf_content, section_type, parent_context |
| 출력 | {leaf_id}.yaml (Item 목록) |

※ 예외: AnnexSubAgent는 Item이 아닌 Entry 추출 (3.5 스키마)

---

**Item 경계 판단**

```
Item = 하나의 완결된 논의 흐름

시작 신호:
- Moderator Summary 시작 ("Summary #1 on...")
- FL Summary 시작 ("FL summary #0...")
- 새로운 TDoc 그룹 시작
- 새로운 기술 주제 시작

종료 신호:
- Agreement, Conclusion, Decision 도출
- 다음 Summary 시작
- "No consensus" 결론
- 섹션 끝

**Fallback 규칙 (필수)**

| 조건 | 처리 |
|------|------|
| 마커([Agreement], **Decision:** 등)가 1개 이상 존재 | 반드시 최소 1개 Item 추출 |
| Item 경계 판단 어려움 | Leaf 전체를 1개 Item으로 |
| Moderator Summary 없음 | 볼드 텍스트 또는 마커 기준으로 Item 구분 |
| 같은 Topic의 여러 Summary | 1개 Item으로 병합 (5.2.0 중복 방지 규칙 참조) |

※ 마커가 있는데 Item 0개는 허용되지 않음
※ 경계가 불명확하면 큰 단위로 묶어서 Item 누락 방지

```

---

**필수 필드 추출** (3.3.2 참조)

```
모든 Item에 필수:

id: "{meeting_id}_{leaf_id}_{sequence}"
  예: "RAN1_120_9.1.1_001"

context:
  meeting_id: "{회의 ID}"
  section_id: "{Depth 1 섹션 ID}"
  leaf_id: "{Leaf ID}"
  leaf_title: "{Leaf 제목}"
  section_type: "{section_type}"

resolution:
  status: "Agreed | Concluded | Noted | Deferred | No_Consensus"
  content:
    - type: "{agreement | conclusion | decision | ...}"
      text: "{추출된 텍스트}"
      marker: "{원문 마커}"

```

---

**TDoc 필드 추출** (3.3.3 참조)

모든 기술 논의 Item에 필수:

input:
moderator_summary: "{Summary TDoc}"  # Required
- "Summary #N on..." 형식에서 TDoc 번호 추출
- "FL summary #N for..." 형식에서 TDoc 번호 추출

discussion_tdocs:                     # Required
- "Relevant tdocs:" 섹션의 모든 TDoc
- 본문 내 참조된 논의 문서

승인 결정이 있는 경우:

output:
approved_tdocs:                       # 승인 시 Required
- tdoc_id: "{승인된 TDoc}"
type: "{Draft CR | LS | TP | Summary}"

```
추출 패턴:
- "[approved in R1-xxx]{.mark}" → approved_tdocs
- "is agreed for CR" → approved_tdocs (type: Draft CR)
- "Final LS is approved" → approved_tdocs (type: LS)
- "TP in R1-xxx is agreed" → approved_tdocs (type: TP)

```

endorsed_tdocs:                       # Optional
- "is endorsed" → endorsed_tdocs

**Revision 관계 추출**

discussion_tdocs에서 revision 관계 추출:

- `(rev of R1-xxx)` 패턴 발견 시:
    - tdoc_id: 현재 TDoc
    - revision_of: 괄호 안의 TDoc

예시:
원문: "R1-2501480 (rev of R1-2500832)"
추출:
- tdoc_id: "R1-2501480"
revision_of: "R1-2500832"

**LS Reply 원본 연결**

ls_out 추출 시:

- reply_tdoc: 승인된 Reply LS TDoc
- replies_to: 원본 Incoming LS TDoc (ls_in.tdoc_id와 동일)

**마커 → content.type 매핑** (3.7 참조)

| 마커 패턴 | content.type |
| --- | --- |
| `[Agreement]{.mark-green}` | agreement |
| `[Agreement]{.mark}` | agreement |
| `[Working Assumption]{.mark-yellow}` | working_assumption |
| `[Working Assumption]{.mark}` | working_assumption |
| `[Post-120-...]{.mark-turquoise}` | post_meeting_action |
| `[Conclusion]` | conclusion |
| `**Conclusion**` | conclusion |
| `**Decision:**` | decision |
| `[Observation]` | observation |
| `FFS:` | ffs |

**색상 기반 판단 힌트**

| 색상 | 우선 type | 비고 |
| --- | --- | --- |
| {.mark-green} | agreement | Agreement 또는 승인 TDoc |
| {.mark-yellow} | working_assumption | Working Assumption |
| {.mark-turquoise} | post_meeting_action | 회의 후 작업 |
| {.mark} | 텍스트로 판단 | 색상 미분류 |

※ 색상과 텍스트가 불일치하면 텍스트 기준 (예: 노랑인데 "Agreement" → agreement)

---

**status 결정**

```
resolution.status 결정 기준:

Agreed: Agreement 마커가 있고 합의됨
Concluded: Conclusion 마커가 있고 결론 도출
Noted: "noted", "No further action" 등
Deferred: "Comeback", "postponed" 등
No_Consensus: "No consensus", "Not agreed" 등

여러 마커가 있으면:
- 최종 결론 기준으로 status 결정
- 모든 마커는 content 배열에 포함

```

---

### 6.5.1 MaintenanceSubAgent

**특화 요소**

```
Maintenance 섹션 특징:
- CR(Change Request) 중심
- Moderator Summary 단위로 논의
- Comeback 패턴 빈번

추가 추출 필드:

cr_info: (CR이 있는 경우)
  tdoc_id: "{CR TDoc ID}"
  spec: "{TS/TR 번호}" (예: "38.214")
  cr_number: "{CR 번호}" (예: "CR0655")

session_info:
  first_discussed: "{첫 논의 세션}"
  concluded: "{결론 세션}"
  comeback: {true|false}

CR 정보 추출 힌트:
- "TS 38.xxx", "TR 38.xxx" 패턴
- "CR####" 또는 "CR ####" 패턴
- Draft CR TDoc 참조

**Item 경계 판단 힌트 (Maintenance 특화)**

| 우선순위 | 힌트 |
|----------|------|
| 1 | Moderator Summary 경계 ("Summary on...", "Summary #2 on...") |
| 2 | **볼드 텍스트 토픽** (**DSS**, **MIMO** 등) |
| 3 | Topic 전환 (다른 기술 주제로 넘어감) |
| 4 | TDoc 그룹 변화 (새로운 Draft CR 세트 시작) |
| Fallback | Leaf 전체를 1개 Item |

※ Pre-Rel Maintenance 섹션은 Moderator Summary 없이 볼드 텍스트로 토픽 구분하는 경우 있음

```

---

### 6.5.2 ReleaseSubAgent

**특화 요소**

```
Release 섹션 특징:
- Agreement, Working Assumption 중심
- FFS 항목 빈번
- 새 기능 정의

추가 인식 패턴:

Working Assumption:
- [Working Assumption]{.mark}
- "Working assumption:" 텍스트

FFS (For Further Study):
- "FFS:" 시작
- "For further study" 포함
- 아직 결정되지 않은 사항

Noted 처리:
- 개별 TDoc이 "noted" 처리되는 경우
- status: Noted로 기록

```

---

### 6.5.3 StudySubAgent

**특화 요소**

```
Study 섹션 특징:
- TR(Technical Report) 작성 목적
- Agreement, Observation, Conclusion 혼재
- Evaluation 데이터 포함 가능

추가 추출 필드:

tr_info: (TR 관련 내용이 있는 경우)
  tr_number: "{TR 번호}" (예: "TR 38.901")
  update_tdoc: "{업데이트 TDoc}"

추가 인식 패턴:

Observation:
- [Observation] 마커
- 실험/시뮬레이션 결과 기술

Conclusion:
- [Conclusion] 마커
- Study 결론 (Agreement와 다름)

```

---

### 6.5.4 UEFeaturesSubAgent

**특화 요소**

| 항목 | 내용 |
| --- | --- |
| 섹션 특징 | Feature Group(FG) 정의 중심, Work Item별 구분, 구조화된 포맷 |
| Item 경계 | Work Item 단위 또는 Feature Group 단위 |
| 경계 힌트 | "UE features for {Work Item}" |

**Item 경계 판단 힌트**

| 우선순위 | 힌트 |
| --- | --- |
| 1 | Work Item 서브섹션 ("UE features for AI/ML") |
| 2 | Summary 문서 단위 |
| Fallback | 전체 UE Features = 1 Item |

**FG 정보 추출**

| 항목 | 내용 |
| --- | --- |
| 추출 대상 | FG name, Component, Prerequisite 등 |
| 저장 위치 | resolution.content.text에 포함 |
| 구조 처리 | 별도 필드 분리 안 함, 원문 그대로 보존 |

**FG 원문 패턴 예시**

```
[Agreement:]

Introduce following FG for UE 8Tx PUSCH processing capability for codebook

-   FG name: pusch-8Tx-Codebook
-   Component: 40-8
-   Prerequisite: 40-7-1
-   Type: Per FS (FR1, FR2-1, FR2-2)
-   Need for UE category: No
-   Need for the gNB to know: Yes

```

**추출 결과 매핑**

| 원문 패턴 | 추출 위치 | 비고 |
| --- | --- | --- |
| `[Agreement:]` 이후 전체 | resolution.content.text | 구조 그대로 보존 |
| `FG name:` 값 | text 내 포함 | 별도 필드 분리 안 함 |
| `Component:` 값 | text 내 포함 | 별도 필드 분리 안 함 |
| `Prerequisite:` 값 | text 내 포함 | 별도 필드 분리 안 함 |

**마커 변형**

| 원문 마커 | content.type | content.marker |
| --- | --- | --- |
| `[Agreement:]` | agreement | `[Agreement:]` |
| `[Agreement]{.mark}` | agreement | `[Agreement]{.mark}` |
| `**Agreement:**` | agreement | `**Agreement:**` |

※ FG 구조는 text에 그대로 포함, 별도 필드로 파싱하지 않음
※ 이유: FG 구조가 회의마다 다를 수 있으므로 원문 보존이 안전

**Session Notes 처리**

| 상황 | 처리 |
| --- | --- |
| Session Notes TDoc | 참조만 (내용 추출 X) |
| 본문에 FG 정의 있음 | 추출 |

**주요 추출 필드**

| 필드 | 용도 | 참조 |
| --- | --- | --- |
| resolution.content | Agreement (FG 정의 포함) | 3.3.2 |
| input | Summary TDoc | 3.3.3 |
| topic | Work Item 정보 | 3.3.3 |

**출력 예시**

```yaml
# sections/8/8.2.yaml

leaf_id: "8.2"
title: "Rel-18 UE Features"
section_type: UE_Features
subsection_agent: UEFeaturesSubAgent

items:
  - id: "RAN1_120_8.2_001"
    context:
      meeting_id: RAN1_120
      section_id: "8"
      leaf_id: "8.2"
      leaf_title: "Rel-18 UE Features"
      section_type: UE_Features

    topic:
      summary: "Rel-18 UE Features for MIMO"

    input:
      moderator_summary: "R1-2501385"

    resolution:
      status: Agreed
      content:
        - type: agreement
          text: "Introduce following FG for UE 8Tx PUSCH processing capability for codebook:\\n-   FG name: pusch-8Tx-Codebook\\n-   Component: 40-8\\n-   Prerequisite: 40-7-1\\n-   Type: Per FS (FR1, FR2-1, FR2-2)\\n-   Need for UE category: No\\n-   Need for the gNB to know: Yes"
          marker: "[Agreement:]"
        - type: agreement
          text: "Introduce following FG for UE 8Tx PUSCH processing capability for non-codebook"
          marker: "[Agreement:]"

statistics:
  total_items: 1
  by_status:
    Agreed: 1

_processing:
  generated_at: "2025-02-22T10:30:00Z"
  status: completed

```

---

### 6.5.5 LSSubAgent

**특화 요소**

```
LS 섹션 특징:
- 1 LS = 1 Item
- Decision 마커 중심
- 회신 여부가 주요 결과

Item 경계:
- 각 Incoming LS TDoc이 하나의 Item

추가 추출 필드:

ls_in:
  tdoc_id: "{수신 LS TDoc}"
  title: "{LS 제목}"
  source: "{발신 WG}" (예: "RAN2")

ls_out:
  action: "Replied | No_Action | Deferred"
  reply_tdoc: "{회신 LS TDoc}" (있는 경우)

Decision 패턴:
- "**Decision:**" 이후 내용
- "RAN1 response is necessary"
- "No further action"
- "To be handled in agenda item X"

```

**LS 헤더 파싱 지시**

```
LS 헤더 형식:
**[{TDoc}](link) {title} {source_wg}, {source_company}**

파싱 방법:
1. 볼드 블록 내 첫 링크에서 TDoc 번호 추출
2. 마지막 쉼표를 찾아 앞/뒤 분리
3. 쉼표 앞 텍스트에서 마지막 단어 = source_wg
4. 쉼표 뒤 텍스트 = source_company
5. 쉼표 없으면 source_company는 null

```

---

**Relevant TDocs 추출 지시**

```
"Relevant tdocs:" 또는 "Relevant Tdoc(s)" 발견 시:
- 다음 줄부터 **Decision:** 전까지 모든 TDoc 수집
- 각 줄에서 TDoc 링크, 제목 추출
- input.discussion_tdocs 배열에 저장

```

---

**Decision 내 handling 정보 추출 지시**

```
Decision 문장에서 다음 패턴 찾기:
- "agenda item {번호}" → handling.agenda_item
- "({주제})" → handling.topic (있으면)
- "- {이름} ({회사})" → handling.moderator, moderator_company
- "To be handled in next meeting {회의}" → handling.deferred_to

```

---

**특수 섹션 처리 지시**

```
섹션 헤더에서 키워드로 플래그 설정:
- "cc-ed" 키워드 발견 → 이후 LS들에 cc_only: true
- "during the week" 키워드 발견 → 이후 LS들에 received_during_week: true

```

---

### 6.5.6 AnnexSubAgent

**특화 요소**

```
Annex 섹션 특징:
- 표 파싱 중심
- Item이 아닌 Entry 추출
- 크로스체크 데이터

처리 대상:
- Annex B: CR 목록
- Annex C-1: Outgoing LS 목록
- Annex C-2: Incoming LS 목록

출력 구조: (3.5 참조)

Annex B entries:
  - tdoc_id, title, source, spec, cr_number

Annex C-1 entries:
  - tdoc_id, title, to, cc

Annex C-2 entries:
  - tdoc_id, title, source, handled_in

통계:
  total_entries: {숫자}

```

---

### 6.6 프롬프트 템플릿 예시

**6.6.1 TOCAgent 프롬프트 템플릿**

```
# 역할
당신은 3GPP RAN1 회의록의 목차(TOC)를 분석하는 전문가입니다.

# 작업
주어진 문서에서 TOC를 추출하고, 각 섹션의 section_type을 판단하세요.

# 입력
{document.md 내용}

# TOC 추출 규칙
1. TOC 영역 식별: "Table of Contents" 이후, 본문 시작 전
2. 각 항목에서 추출: id, title, depth, parent, children
3. 링크 형식: [제목](#anchor){.toclink} ... 페이지번호

# section_type 판단 (우선순위)
1. "Annex" → Annex
2. "Liaison" → LS
3. "Opening", "Closing", "Approval" → Procedural
4. "UE Features" → UE_Features
5. "Study", "SI" → Study
6. "Maintenance", "Pre-Rel" → Maintenance
7. "Release XX" → Release

키워드가 없으면 상위 섹션에서 상속.
판단 불가 시 unknown.

# Virtual Numbering
.unnumbered 클래스 또는 번호 없는 섹션:
- 가상 번호 부여: {parent_id}v{sequence}
- virtual: true 표시

# skip 판단
- Procedural 섹션: skip: true
- Annex A, D~H: skip: true
- Annex B, C-1, C-2: skip: false

# 출력 형식
YAML 형식으로 출력:

meeting_id: "{회의 ID}"
sections:
  - id: "..."
    title: "..."
    depth: ...
    parent: ...
    children: [...]
    section_type: "..."
    skip: ...
    virtual: ... # 해당 시에만

```

---

**6.6.2 SubSection Agent 공통 프롬프트 템플릿**

```
# 역할
당신은 3GPP RAN1 회의록에서 기술 논의 결과를 추출하는 전문가입니다.

# 작업
주어진 Leaf 섹션에서 Item을 식별하고 구조화된 정보를 추출하세요.

# 입력
- leaf_id: {leaf_id}
- leaf_title: {leaf_title}
- section_type: {section_type}
- leaf_content:
{leaf_content}

# Item 경계 판단
Item = 하나의 완결된 논의 흐름

시작 신호:
- "Summary #N on...", "FL summary #N..."
- 새로운 TDoc 그룹
- 새로운 기술 주제

종료 신호:
- Agreement, Conclusion, Decision 마커
- 다음 Summary 시작
- 섹션 끝

경계 판단이 어려우면 전체를 1개 Item으로.

# 마커 → content.type
[Agreement]{.mark} → agreement
[Conclusion] → conclusion
**Decision:** → decision
[Working Assumption]{.mark} → working_assumption
[Observation] → observation
FFS: → ffs

# 필수 필드
모든 Item에 필수:
- id: "{meeting_id}_{leaf_id}_{sequence}"
- context: meeting_id, section_id, leaf_id, leaf_title, section_type
- resolution: status, content[]

# status 결정
- Agreement 있고 합의됨 → Agreed
- Conclusion 있음 → Concluded
- "noted" 처리 → Noted
- "Comeback" 등 → Deferred
- 합의 실패 → No_Consensus

# 출력 형식
YAML 형식으로 출력:

leaf_id: "{leaf_id}"
title: "{leaf_title}"
section_type: "{section_type}"
subsection_agent: "{Agent 이름}"

items:
  - id: "..."
    context: {...}
    resolution:
      status: "..."
      content:
        - type: "..."
          text: "..."
          marker: "..."
    # 선택 필드 (해당 시)
    topic: {...}
    input: {...}
    session_info: {...}
    cr_info: {...}
    # ...

statistics:
  total_items: ...
  by_status: {...}

```

---

**다른 섹션 참조**

| 내용 | 참조 |
| --- | --- |
| 핵심 원칙 | 1장 |
| Item 스키마 | 3.3 |
| Annex 스키마 | 3.4 |
| TDoc 참조 패턴 | 3.5 |
| 마커 패턴 | 3.6 |
| section_type 판단 | 4.2.2 |
| Virtual Numbering | 4.2.5 |
| skip 처리 | 4.2.4 |
| 청킹 상세 | 4.3.4 |
| unknown 처리 | 4.3.6 |
| SubSection Agent 상세 | 5.2 |

---

## 7. 검증 및 품질 보증

### 7.1 검증 개요

**목적**

| 항목 | 설명 |
| --- | --- |
| 목적 | 추출 결과의 정합성과 완전성 검증 |
| 수행 시점 | 역할 4 (결과 취합 + 검증) |
| 핵심 원칙 | 이해 가능한 기준 - 검증 결과와 불일치 사유가 명확히 기록됨 |

---

**검증 유형**

| 검증 유형 | 주체 | 목적 |
| --- | --- | --- |
| 구조/필드 검증 | 코드 | 파일 존재, 필수 필드 존재, 형식 검증 |
| 크로스체크 | LLM | 본문 추출 데이터와 Annex 데이터 간 대응 관계 검증 |
| 통계 정합성 | 코드 | 숫자 합계, 개수 일치 검증 |

---

**검증 흐름**

```
역할 3 완료
    ↓
┌─────────────────────────────────────────┐
│           역할 4: 검증 체계              │
├─────────────────────────────────────────┤
│  1. 구조/필드 검증 (코드)                │
│              ↓                          │
│  2. 크로스체크 (LLM)                     │
│     - CR: 본문 vs Annex B               │
│     - Outgoing LS: 본문 vs Annex C-1    │
│     - Incoming LS: Section 5 vs Annex C-2│
│     - Reply LS 일관성                    │
│              ↓                          │
│  3. 통계 정합성 (코드)                   │
└─────────────────────────────────────────┘
    ↓
검증 결과 (passed / warning / failed)
    ↓
[failed] → Human Review 트리거
[warning] → 기록 후 계속
[passed] → 최종 출력 생성

```

---

### 7.2 크로스체크

### 7.2.0 개요

**크로스체크 대상**

| 크로스체크 | 본문 소스 | Annex 소스 | 매칭 기준 |
| --- | --- | --- | --- |
| CR | 본문에서 "is agreed" 패턴 | Annex B | TDoc 번호 |
| Outgoing LS | 본문에서 "LS is approved" 패턴 | Annex C-1 | TDoc 번호 |
| Incoming LS | Section 5 처리 결과 | Annex C-2 | TDoc 번호 |
| Reply LS | Outgoing의 Reply to | Incoming의 Reply in | 상호 참조 |

---

**크로스체크 데이터 소스**

| 데이터 | 소스 파일 | 필드 | 참조 |
| --- | --- | --- | --- |
| 본문 CR | sections/{id}/{leaf}.yaml | cr_info.tdoc_id | 5.2.1 |
| 본문 Outgoing LS | sections/{id}/{leaf}.yaml | ls_out.reply_tdoc | 5.2.5 |
| 본문 Incoming LS | sections/5/{leaf}.yaml | ls_in.tdoc_id | 5.2.5 |
| Annex B | annexes/annex_b.yaml | entries[].tdoc_id | 5.2.6 |
| Annex C-1 | annexes/annex_c1.yaml | entries[].tdoc_id | 5.2.6 |
| Annex C-2 | annexes/annex_c2.yaml | entries[].tdoc_id | 5.2.6 |

※ Annex 데이터는 AnnexSubAgent가 이미 파싱한 결과 사용 (재파싱 안 함)

---

**크로스체크가 LLM인 이유**

| 상황 | 코드로 불가능한 이유 |
| --- | --- |
| TDoc 번호 변형 | "R1-2501501" vs "[R1-2501501]" |
| 부분 매칭 | "TP in R1-2501491 is agreed as alignment CR" |
| 컨텍스트 판단 | Draft CR vs Final CR 구분 |
| 동의어 처리 | "approved" vs "agreed" vs "endorsed" |

---

**불일치 심각도 기준**

| 불일치율 | 심각도 | 처리 |
| --- | --- | --- |
| 5% 미만 | passed | 정상 완료 |
| 5~10% | warning | 기록 후 계속 |
| 10% 초과 | failed | Human Review 트리거 |

---

### 7.2.1 CR 크로스체크

**매칭 로직**

```yaml
CR_crosscheck:
  본문_소스:
    - resolution.status = Agreed인 Item
    - cr_info.tdoc_id 추출

  Annex_B_소스:
    - annexes/annex_b.yaml
    - entries[].tdoc_id

  매칭:
    - TDoc 번호 정규화 (R1-2501501, [R1-2501501] → R1-2501501)
    - 1:1 매칭

```

---

**불일치율 계산**

| 항목 | 계산 |
| --- | --- |
| 분모 | max(본문 CR 개수, Annex B 개수) |
| 분자 | 매칭 실패 개수 (body_only + annex_only) |
| 불일치율 | 분자 / 분모 |

---

**불일치 유형**

| 불일치 유형 | 가능한 원인 | 심각도 |
| --- | --- | --- |
| 본문에만 존재 | Annex B 작성 누락 (문서 자체 오류) | warning |
| Annex B에만 존재 | 본문 추출 누락 | warning |
| 다수 불일치 (10% 초과) | 추출 로직 오류 가능성 | failed |

---

**Draft CR 제외**

| 패턴 | 처리 |
| --- | --- |
| "Draft CR is not pursued" | 크로스체크 대상 제외 |
| "Companies to check draft CR" | 크로스체크 대상 제외 |

---

### 7.2.2 Outgoing LS 크로스체크

**매칭 로직**

```yaml
Outgoing_LS_crosscheck:
  본문_소스:
    - ls_out.action = Replied인 Item
    - ls_out.reply_tdoc 추출

  Annex_C1_소스:
    - annexes/annex_c1.yaml
    - entries[].tdoc_id

  추가_검증:
    - Reply to 필드 일관성

```

---

**불일치율 계산**

| 항목 | 계산 |
| --- | --- |
| 분모 | max(본문 Outgoing LS 개수, Annex C-1 개수) |
| 분자 | 매칭 실패 개수 |
| 불일치율 | 분자 / 분모 |

---

**Reply LS vs 신규 LS 구분**

| 유형 | 특징 |
| --- | --- |
| Reply LS | Reply to 필드에 원본 LS 번호 있음 |
| 신규 LS | Reply to 필드 비어있음 |

---

### 7.2.3 Incoming LS 크로스체크

**매칭 로직**

```yaml
Incoming_LS_crosscheck:
  본문_소스:
    - Section 5에서 처리된 LS
    - ls_in.tdoc_id 추출

  Annex_C2_소스:
    - annexes/annex_c2.yaml
    - entries[].tdoc_id

  특이사항:
    - CC-only LS는 별도 집계

```

---

**CC-only LS 처리**

| 항목 | 내용 |
| --- | --- |
| 정의 | RAN1이 To가 아닌 Cc로만 포함된 LS |
| 본문 | "RAN1 was cc-ed in the following incoming LSs:" |
| Annex C-2 | 포함됨 (To 필드에 RAN1 없음) |
| 크로스체크 | **불일치율 계산에서 제외**, 별도 통계로 기록 |

---

**불일치율 계산 (CC-only 제외)**

| 항목 | 계산 |
| --- | --- |
| Annex C-2 대상 | To 필드에 RAN1 포함된 항목만 (CC-only 제외) |
| 분모 | max(본문 Incoming LS 개수, Annex C-2 대상 개수) |
| 분자 | 매칭 실패 개수 |
| 불일치율 | 분자 / 분모 |

**예시:**

```
본문: 30개
Annex C-2 전체: 45개
  - To: RAN1: 30개
  - CC-only: 15개
Annex C-2 대상: 30개 (CC-only 제외)

불일치율 = 0 / 30 = 0% ✓
CC-only 통계: 15개 (별도 기록)

```

---

**Incoming LS 매칭 로직**

| 단계 | 내용 |
| --- | --- |
| 1 | 본문 LS 섹션에서 추출된 Item의 ls_in.tdoc_number 수집 |
| 2 | Annex C-2에서 To 필드에 RAN1 포함된 항목만 추출 (CC-only 제외) |
| 3 | TDoc 번호로 1:1 매칭 시도 |
| 4 | 매칭 실패 항목은 body_only 또는 annex_only로 분류 |

**Annex C-2 handled_in 필드 활용**

| 조건 | 처리 |
| --- | --- |
| handled_in 존재 | 본문 처리 위치 힌트로 활용 (검증용) |
| handled_in 없음 | TDoc 번호만으로 매칭 |
| handled_in과 실제 위치 불일치 | warning 기록, Human Review 권장 |

※ handled_in은 참고 정보이며, 실제 매칭은 TDoc 번호 기준

---

### 7.2.4 Reply LS 일관성

**연결 구조**

```
Incoming LS (Annex C-2)          Outgoing LS (Annex C-1)
┌─────────────────────┐          ┌─────────────────────┐
│ R1-2500006          │          │ R1-2501606          │
│ Reply in:           │  ──────► │                     │
│ R1-2501606          │          │ Reply to:           │
│                     │  ◄────── │ R2-2410978          │
│ Original LS:        │          │                     │
│ R2-2410978          │          │                     │
└─────────────────────┘          └─────────────────────┘

```

---

**검증 규칙**

| 검증 항목 | 규칙 |
| --- | --- |
| Reply in 존재 | Incoming의 Reply in이 Annex C-1에 존재해야 함 |
| Reply to 존재 | Outgoing의 Reply to가 Annex C-2에 존재해야 함 |
| 양방향 일치 | Incoming.Reply_in = Outgoing.TDoc 상호 참조 |

---

**외부 LS 처리**

| Reply to 형식 | 의미 | 처리 |
| --- | --- | --- |
| R2-XXXXXX | RAN2에서 온 LS에 대한 답변 | Annex C-2의 Original LS로 확인 |
| S2-XXXXXX | SA2에서 온 LS에 대한 답변 | Annex C-2의 Original LS로 확인 |

---

### 7.2.5 크로스체크 출력

```yaml
crosscheck:
  cr:
    status: passed | warning | failed
    body_count: 19
    annex_count: 19
    matched_count: 19
    mismatch_rate: 0.0
    body_only: []
    annex_only: []

  outgoing_ls:
    status: passed
    body_count: 24
    annex_count: 24
    matched_count: 24
    mismatch_rate: 0.0
    by_type:
      reply_ls: 8
      new_ls: 16

  incoming_ls:
    status: passed
    body_count: 30
    annex_count: 45
    annex_target_count: 30  # CC-only 제외
    cc_only_count: 15
    matched_count: 30
    mismatch_rate: 0.0

  reply_consistency:
    status: passed
    total_pairs: 8
    consistent: 8
    inconsistent: []

```

---

### 7.3 Human Review

### 7.3.1 트리거 조건 종합

**전체 트리거 목록**

| 트리거 | 발생 위치 | 조건 | 심각도 |
| --- | --- | --- | --- |
| type_unknown | TOCAgent / Orchestrator | section_type 판단 불가 | warning |
| boundary_unclear | SubSection Agent | Item 경계 판단 불가 | warning |
| validation_failed | Orchestrator | 필수 파일/필드 누락 | failed |
| crosscheck_mismatch | Orchestrator | 불일치율 10% 초과 | failed |
| new_pattern | SubSection Agent | 정의되지 않은 마커 발견 | warning |

---

**트리거별 상세**

**type_unknown**

```yaml
human_review:
  trigger: "type_unknown"
  context:
    section_id: "10"
    section_title: "Other Items"
    content_preview: "첫 500자..."
  options:
    - action: "maintenance"
    - action: "release"
    - action: "study"
    - action: "skip"
  recommendation:
    action: "maintenance"
    confidence: 0.4

```

---

**crosscheck_mismatch**

```yaml
human_review:
  trigger: "crosscheck_mismatch"
  context:
    crosscheck_type: "cr"
    body_count: 20
    annex_count: 15
    mismatch_rate: 0.25
    body_only:
      - tdoc: "R1-2501999"
        leaf_id: "8.1.5"
    annex_only: []
  options:
    - action: "accept_body"
    - action: "accept_annex"
    - action: "manual_review"

```

---

**new_pattern**

```yaml
human_review:
  trigger: "new_pattern"
  context:
    pattern_type: "decision_marker"
    found_text: "[Preliminary Agreement]"
    location:
      leaf_id: "9.2.1"
    similar_patterns:
      - "[Agreement]"
      - "[Working Assumption]"
  options:
    - action: "treat_as_agreement"
    - action: "treat_as_working_assumption"
    - action: "add_new_type"
    - action: "ignore"

```

---

### 7.3.2 처리 옵션

**옵션 유형**

| 옵션 유형 | 설명 | 적용 트리거 |
| --- | --- | --- |
| 선택형 | 제시된 옵션 중 선택 | type_unknown, new_pattern |
| 액션형 | 재처리, 건너뛰기 등 | validation_failed, crosscheck_mismatch |
| 입력형 | 사용자가 직접 값 입력 | boundary_unclear (수동 분리) |

---

**옵션별 후속 처리**

| 옵션 | 후속 처리 |
| --- | --- |
| maintenance/release/study | 해당 SubSection Agent 호출 |
| skip | 처리 건너뛰기, 기록만 |
| reprocess_section | 해당 섹션 역할 3부터 재실행 |
| accept_body | 불일치 기록, 본문 결과 사용 |
| manual_review | 개별 항목 확인 |

---

**재처리 제한**

| 항목 | 제한 |
| --- | --- |
| 최대 재처리 횟수 | 3회 |
| 동일 트리거 반복 | 2회 후 에러 종료 |
| 한도 초과 시 | _error 기록, Human Review로 최종 판단 요청 |

```yaml
# 재처리 한도 초과 시
_error:
  error_type: "reprocess_limit_exceeded"
  error_message: "Maximum reprocess attempts (3) reached"
  human_review_history:
    - id: "HR_001"
      option: "reprocess_section"
    - id: "HR_002"
      option: "reprocess_section"
    - id: "HR_003"
      option: "reprocess_section"

```

---

**결과 기록**

```yaml
human_review_response:
  review_id: "HR_001"
  trigger: "type_unknown"
  selected_option: "maintenance"
  selected_by: "reviewer_name"
  selected_at: "2025-02-22T11:00:00Z"
  additional_notes: "CR 패턴이 명확하여 Maintenance로 판단"

```

---

### 7.4 품질 메트릭

**핵심 메트릭**

| 메트릭 | 계산 | 기준 |
| --- | --- | --- |
| 추출 완성도 | 처리된 Leaf / 전체 Leaf | 100% |
| 크로스체크 일치율 | 매칭 성공 / 전체 대상 | ≥ 90% |
| Human Review 발생률 | HR 트리거 / 전체 Item | ≤ 5% |
| 필수 필드 완성률 | 필수 필드 있음 / 전체 Item | 100% |

---

**메트릭 계산 시점**

| 시점 | 메트릭 |
| --- | --- |
| 역할 4 완료 후 | 추출 완성도, 크로스체크 일치율, 필수 필드 완성률 |
| 전체 완료 후 | Human Review 발생률 |

---

**최종 검증 결과 구조**

```yaml
validation:
  overall_status: passed | warning | failed

  structure:
    status: passed
    files_checked: 47
    fields_checked: 1024

  crosscheck:
    status: passed
    cr: passed
    outgoing_ls: passed
    incoming_ls: passed
    reply_consistency: passed

  consistency:
    status: passed
    total_items: 156
    sum_verified: true

  human_review_summary:
    total_reviews: 2
    resolved: 2
    unresolved: 0

  metrics:
    extraction_completeness: 1.0
    crosscheck_match_rate: 0.95
    human_review_rate: 0.013
    required_field_rate: 1.0

```

---

### 다른 섹션 참조

| 내용 | 참조 |
| --- | --- |
| 역할 4 개요 | 4.4 |
| Item 스키마 | 3.3 |
| Annex 스키마 | 3.4 |
| _error 구조 | 3.3.3 |
| section_type 판단 | 4.2.2 |
| unknown 처리 | 4.3.6 |
| AnnexSubAgent | 5.2.6 |

---