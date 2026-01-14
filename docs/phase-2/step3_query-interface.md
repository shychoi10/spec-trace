# Step-3: Query Interface 구축

## 개요

Neo4j Knowledge Graph에 대한 자연어 Query Interface를 LlamaIndex + OpenRouter(Gemini)로 구축한다.

## 기술 스택

| 구성 요소 | 선택 | 버전/모델 |
|-----------|------|-----------|
| **Framework** | LlamaIndex | latest |
| **LLM Provider** | OpenRouter | API |
| **LLM Model** | Gemini 2.0 Flash | `google/gemini-2.0-flash-exp:free` |
| **Graph Store** | Neo4j | 5.26.0 (Step-2에서 구축) |
| **Retriever** | TextToCypherRetriever | LlamaIndex 내장 |

## Sub-step 구조

| Sub-step | 내용 | 산출물 | 상태 |
|----------|------|--------|------|
| 3-1 | 환경 설정 | pyproject.toml, 의존성 설치 | ⬜ |
| 3-2 | Neo4j + LlamaIndex 연동 | 기본 연결 테스트 | ⬜ |
| 3-3 | Text-to-Cypher 구현 | 자연어 쿼리 인터페이스 | ⬜ |
| 3-4 | CQ 25개 검증 | 정확도 리포트 | ⬜ |

---

## Sub-step 3-1: 환경 설정

### 추가 패키지

```toml
# pyproject.toml에 추가
"llama-index>=0.12.0",
"llama-index-llms-openrouter>=0.4.0",
"llama-index-graph-stores-neo4j>=0.4.0",
"neo4j>=5.26.0",
```

### 환경 변수 (이미 설정됨)

```bash
# .env
OPENROUTER_API_KEY=***  # ✅ 설정됨
```

### 디렉토리 구조

```
scripts/phase-2/query-interface/
├── config.py                 # 설정 (Neo4j, OpenRouter)
├── graph_store.py            # Neo4j PropertyGraphStore 래퍼
├── query_engine.py           # Text-to-Cypher 엔진
├── validate_cq_nl.py         # CQ 25개 자연어 검증
└── interactive.py            # 대화형 쿼리 인터페이스
```

---

## Sub-step 3-2: Neo4j + LlamaIndex 연동

### 연동 아키텍처

```
[User Query (자연어)]
        │
        ▼
[OpenRouter LLM (Gemini)]
        │
        ▼
[TextToCypherRetriever]
        │
        ▼ (생성된 Cypher)
[Neo4jPropertyGraphStore]
        │
        ▼ (쿼리 결과)
[Response Synthesizer]
        │
        ▼
[Natural Language Response]
```

### 기본 연결 코드

```python
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.openrouter import OpenRouter
from llama_index.core import PropertyGraphIndex

# LLM 설정
llm = OpenRouter(
    model="google/gemini-2.0-flash-exp:free",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Neo4j 연결
graph_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="password123",
    url="bolt://localhost:7688",
)

# PropertyGraphIndex 생성 (기존 그래프 사용)
index = PropertyGraphIndex.from_existing(
    property_graph_store=graph_store,
    llm=llm,
)
```

---

## Sub-step 3-3: Text-to-Cypher 구현

### Retriever 선택

| Retriever | 용도 | 우리 케이스 |
|-----------|------|-------------|
| LLMSynonymRetriever | 키워드/동의어 기반 노드 검색 | ❌ (LlamaIndex가 생성한 속성 필요) |
| VectorContextRetriever | 벡터 유사도 기반 검색 | ❌ (임베딩 없음) |
| **TextToCypherRetriever** | 자연어 → Cypher 변환 | ✅ **선택** |
| CypherTemplateRetriever | 템플릿 기반 Cypher | △ (보조) |

### TextToCypherRetriever 설정

```python
from llama_index.core.indices.property_graph import TextToCypherRetriever

retriever = TextToCypherRetriever(
    graph_store=graph_store,
    llm=llm,
    # 스키마 정보 제공 (정확도 향상)
    allowed_output_fields=["t", "m", "c", "w", "a", "r", "s"],
)
```

### 스키마 프롬프트 최적화

LLM이 정확한 Cypher를 생성하도록 Neo4j 스키마 정보를 프롬프트에 포함:

```
Node Labels: Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup

Relationships:
- (Tdoc)-[:PRESENTED_AT]->(Meeting)
- (Tdoc)-[:SUBMITTED_BY]->(Company)
- (Tdoc)-[:HAS_CONTACT]->(Contact)
- (Tdoc)-[:BELONGS_TO]->(AgendaItem)
- (Tdoc)-[:RELATED_TO]->(WorkItem)
- (Tdoc)-[:TARGET_RELEASE]->(Release)
- (Tdoc)-[:IS_REVISION_OF]->(Tdoc)
- (Tdoc)-[:REVISED_TO]->(Tdoc)
- (CR)-[:MODIFIES]->(Spec)
- (LS)-[:SENT_TO]->(WorkingGroup)
- (LS)-[:CC_TO]->(WorkingGroup)
- (LS)-[:ORIGINATED_FROM]->(WorkingGroup)
- (LS)-[:REPLY_TO]->(Tdoc)

Key Properties:
- Tdoc: tdocNumber, title, type, status, for
- Company: companyName, aliases
- Meeting: meetingNumber
- WorkItem: workItemCode
- AgendaItem: agendaNumber, description
```

---

## Sub-step 3-4: CQ 25개 검증

### 검증 방법

| 단계 | 내용 |
|------|------|
| 1 | CQ를 자연어로 쿼리 |
| 2 | 생성된 Cypher 확인 |
| 3 | 결과와 Step-2 Cypher 결과 비교 |
| 4 | 정확도 측정 |

### CQ 자연어 버전 (예시)

| CQ# | Cypher 버전 (Step-2) | 자연어 버전 (Step-3) |
|-----|---------------------|---------------------|
| CQ1 | `MATCH (t:Tdoc)-[:PRESENTED_AT]->...` | "RAN1#120 회의에서 NR_enh_MIMO 관련 Tdoc 목록은?" |
| CQ3 | `MATCH (t:Tdoc)-[:SUBMITTED_BY]->...` | "Samsung이 제출한 Tdoc 목록은?" |
| CQ5 | `WHERE t.status IN ['approved', 'agreed']` | "승인된 Tdoc 목록은?" |
| CQ10 | `MATCH (t)-[:IS_REVISION_OF]->...` | "R1-2412345의 이전 revision은?" |
| CQ19 | Aggregation query | "Work Item별 회사 기고 수는?" |

### 평가 기준

| 기준 | 설명 | 목표 |
|------|------|------|
| **Cypher 정확도** | 생성된 Cypher가 문법적으로 올바른가 | 100% |
| **결과 일치도** | Step-2 Cypher 결과와 동일한가 | ≥90% |
| **응답 시간** | 쿼리 생성 + 실행 시간 | <5초 |

### 검증 리포트 형식

```markdown
# CQ 자연어 검증 리포트

## 요약
- 검증 일시: 2025-01-XX
- 모델: google/gemini-2.0-flash-exp:free
- 총 CQ: 25개
- 성공: XX개
- 실패: XX개

## 상세 결과

### CQ1: 특정 회의에서 특정 Work Item 관련 Tdoc
- 자연어: "RAN1#120에서 NR_enh_MIMO 관련 문서는?"
- 생성 Cypher: `MATCH ...`
- 결과 일치: ✅
- 응답 시간: 1.2s
```

---

## 파일 구조 (최종)

```
scripts/phase-2/query-interface/
├── config.py                 # 설정
├── graph_store.py            # Neo4j 연결
├── query_engine.py           # Text-to-Cypher
├── validate_cq_nl.py         # CQ 검증
├── interactive.py            # 대화형 인터페이스
└── schema_prompt.txt         # 스키마 프롬프트

logs/phase-2/query-interface/
└── cq_nl_validation.log      # 검증 로그
```

---

## 예상 이슈 및 대응

| 이슈 | 원인 | 대응 |
|------|------|------|
| Cypher 문법 오류 | LLM 한계 | 스키마 프롬프트 강화, few-shot 예시 추가 |
| 잘못된 관계 방향 | 스키마 이해 부족 | 관계 방향 명시적 기술 |
| 복잡한 집계 쿼리 실패 | 멀티홉 추론 한계 | CypherTemplateRetriever 병행 |
| 응답 지연 | OpenRouter 지연 | 캐싱, 배치 처리 |

---

## 관련 문서

- [Phase-2 Overview](README.md)
- [Step-1: Ontology 구축](step1_ontology.md)
- [Step-2: Database 구축](step2_database.md)
- [TDoc Ontology Spec](specs/tdoc-ontology-spec.md)

## 참고 자료

- [LlamaIndex Neo4j PropertyGraphIndex](https://developers.llamaindex.ai/python/examples/property_graph/property_graph_neo4j/)
- [LlamaIndex OpenRouter Integration](https://docs.llamaindex.ai/en/stable/examples/llm/openrouter/)
- [Neo4j Labs - LlamaIndex](https://neo4j.com/labs/genai-ecosystem/llamaindex/)
