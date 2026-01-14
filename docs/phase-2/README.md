# Phase-2: Knowledge Graph Construction

## 개요

3GPP TDoc 메타데이터를 기반으로 Knowledge Graph를 구축하여 표준화 엔지니어 업무를 지원하는 Agent AI의 기반을 마련한다.

## 목표

- **1단계 사용자**: 표준화 엔지니어
- **핵심 기능**: TDoc 검색, 관계 추적, 경쟁사 분석, 히스토리 조회
- **Competency Questions**: 25개 (specs/tdoc-ontology-spec.md 참조)

## 데이터 소스

| 소스 | 형태 | 용도 |
|------|------|------|
| TDoc_List (Excel) | 정형 | 1차 Ontology |
| Final Minutes (Word) | 비정형 | 2차 확장 (향후) |

## Step 구조

```
Phase-2: Knowledge Graph Construction
├── Step-1: Ontology 구축                    ✅ 완료
│   ├── 1-1: Ontology 설계                   ✅ 완료
│   ├── 1-2: 데이터 검증                     ✅ 완료
│   ├── 1-3: 인스턴스 생성                   ✅ 완료
│   └── 1-4: Spec 대비 검증                  ✅ 완료
│
├── Step-2: Database 구축                    ✅ 완료
│   ├── 2-1: Neo4j 적재 (n10s)               ✅ 완료
│   ├── 2-2: Neo4j 적재 (Cypher)             ✅ 완료 (선택됨)
│   ├── 2-3: 적재 방식 비교                  ✅ 완료
│   └── 2-4: CQ 25개 Cypher 검증             ✅ 완료
│
├── Step-3: Query Interface 구축             ← 현재
│   ├── 3-1: 환경 설정                       ⬜ 예정
│   ├── 3-2: Neo4j + LlamaIndex 연동         ⬜ 예정
│   ├── 3-3: Text-to-Cypher 구현             ⬜ 예정
│   └── 3-4: CQ 25개 자연어 검증             ⬜ 예정
│
└── Step-4: Agent 연동                       ⬜ 예정
    └── 4-1: LLM + KG 연동
```

## 문서 구조

```
docs/phase-2/
├── README.md                 # 이 문서
├── step1_ontology.md         # Step-1 상세 가이드
├── step2_database.md         # Step-2 상세 가이드
├── step3_query-interface.md  # Step-3 상세 가이드
└── specs/
    └── tdoc-ontology-spec.md # Ontology 설계 명세

ontology/                     # 작업 폴더 (docs 외부)
├── input/meetings/RAN1/      # 59개 TDoc_List Excel
├── intermediate/             # 중간 결과물
├── output/instances/         # JSON-LD 인스턴스 (125,480개)
├── scripts/                  # 구현 스크립트
└── tdoc-ontology.ttl         # Turtle 스키마

scripts/phase-2/neo4j/        # Neo4j 관련 스크립트
├── load_cypher.py            # Cypher 적재 (선택됨)
├── validate_cq.py            # CQ 25개 검증
└── ...
```

## 진행 상황

| Step | 상태 | 설명 |
|------|------|------|
| Step-1 | ✅ 완료 | Ontology 설계, 인스턴스 125,480개 생성 |
| Step-2 | ✅ 완료 | Neo4j 적재, CQ 25개 Cypher 검증 완료 |
| Step-3 | 🔄 진행 중 | LlamaIndex + OpenRouter 자연어 쿼리 |
| Step-4 | ⬜ 예정 | - |

## Step-3 상세 계획

### 기술 스택

| 구성 요소 | 선택 |
|-----------|------|
| Framework | LlamaIndex |
| LLM Provider | OpenRouter |
| LLM Model | Gemini 2.0 Flash |
| Retriever | TextToCypherRetriever |

### Sub-step

| Sub-step | 내용 | 상태 |
|----------|------|------|
| 3-1 | 환경 설정 (pyproject.toml) | ⬜ |
| 3-2 | Neo4j + LlamaIndex 연동 | ⬜ |
| 3-3 | Text-to-Cypher 구현 | ⬜ |
| 3-4 | CQ 25개 자연어 검증 | ⬜ |

## 주요 통계

| 항목 | 값 |
|------|-----|
| 총 인스턴스 | 125,480개 |
| Neo4j 노드 | 125,478개 |
| Neo4j 관계 | 727,585개 |
| CQ Cypher 검증 | 25/25 Pass |

## 관련 문서

- [프로젝트 전체 진행 상황](../../progress.md)
- [Step-1: Ontology 구축](step1_ontology.md)
- [Step-2: Database 구축](step2_database.md)
- [Step-3: Query Interface 구축](step3_query-interface.md)
- [TDoc Ontology Spec](specs/tdoc-ontology-spec.md)
