# Step-2: Database Construction

## 개요

Step-1에서 생성한 Ontology (TBox + ABox)를 Neo4j에 적재하고 CQ 25개를 Cypher 쿼리로 검증한다.

## Sub-step 구조

| Sub-step | 내용 | 산출물 | 상태 |
|----------|------|--------|------|
| 2-1: Neo4j 적재 (n10s) | neosemantics 플러그인 사용 | 결과 A | ✅ 완료 |
| 2-2: Neo4j 적재 (Cypher) | APOC + 직접 Cypher | 결과 B | ✅ 완료 |
| 2-3: 적재 방식 비교/선택 | 두 방식 비교, 최종 선택 | comparison_report.md | ✅ 완료 |
| 2-4: CQ 25개 검증 | Cypher 쿼리 작성/실행 | cq_validation.log | ✅ 완료 |

---

## Sub-step 2-1: Neo4j 적재 (n10s) ✅

### 환경

- Neo4j 5.26.0 + APOC + n10s (neosemantics)
- Docker Compose로 실행
- 힙 메모리: 4GB

### 결과

| 항목 | 값 |
|------|-----|
| 적재 시간 | 8.70초 |
| 노드 수 | 125,542 |
| 관계 수 | 96 (스키마 관계만) |
| 트리플 로드 | 1,734,449 |

### 문제점

- JSON-LD의 참조(URI 문자열)가 관계로 변환되지 않음
- 모든 속성이 배열로 저장됨 (`["value"]`)
- 실제 그래프 탐색에 부적합

---

## Sub-step 2-2: Neo4j 적재 (직접 Cypher) ✅

### 환경

- Neo4j 5.26.0 + APOC
- Docker Compose로 실행
- 힙 메모리: 2GB

### 결과

| 항목 | 값 |
|------|-----|
| 적재 시간 | ~10초 |
| 노드 수 | 125,478 |
| 관계 수 | 727,585 |

### 관계 통계 (수정 후)

| 관계 타입 | 수 | 비고 |
|----------|------|------|
| SUBMITTED_BY | 152,915 | |
| PRESENTED_AT | 122,257 | |
| BELONGS_TO | 122,257 | |
| HAS_CONTACT | 122,257 | |
| TARGET_RELEASE | 82,626 | |
| RELATED_TO | 78,101 | |
| IS_REVISION_OF | 11,243 | |
| REVISED_TO | 11,092 | **신규** |
| MODIFIES | 10,544 | |
| SENT_TO | 7,598 | |
| ORIGINATED_FROM | 3,316 | **신규** |
| CC_TO | 2,956 | |
| REPLY_TO | 423 | **신규** |
| **총계** | **727,585** | +14,831 |

---

## Sub-step 2-3: 적재 방식 비교/선택 ✅

### 비교 결과

| 항목 | n10s | Cypher | 승자 |
|------|------|--------|------|
| 적재 시간 | 8.70s | 14.19s | n10s |
| 노드 수 | 125,542 | 125,478 | 동등 |
| 관계 수 | 96 | 712,754 | **Cypher** |
| CQ 지원 | ❌ | ✅ | **Cypher** |

### 최종 선택: **직접 Cypher**

**이유**:
1. CQ 25개가 관계 탐색 기반
2. 쿼리 성능 최적화 가능
3. Neo4j의 그래프 의미론 활용

---

## Sub-step 2-4: CQ 25개 Cypher 쿼리 검증 ✅

### 검증 결과

| 구분 | 개수 |
|------|------|
| ✅ Passed | 25 |
| ⚠️ Warning | 0 |
| ❌ Failed | 0 |

**평균 쿼리 시간**: 143.0ms

### CQ별 결과 요약

| CQ# | 설명 | 결과 | 시간 |
|-----|------|------|------|
| CQ1 | 특정 회의에서 특정 Work Item 관련 Tdoc | 78,101 | 113ms |
| CQ2 | 특정 회의에서 특정 Agenda Item 관련 Tdoc | 122,257 | 107ms |
| CQ3 | 특정 회사가 제출한 Tdoc | 121,295 | 94ms |
| CQ4 | 특정 Release에서 논의된 Tdoc | 82,626 | 28ms |
| CQ5 | 승인/합의된 Tdoc | 5,447 | 54ms |
| CQ6 | Tdoc의 Status | 122,257 | 33ms |
| CQ7 | Tdoc의 목적(For) | 98,885 | 33ms |
| CQ8 | Tdoc의 담당자(Contact) | 982 | 33ms |
| CQ9 | Agenda 목록 | 1,335 | 30ms |
| CQ10 | Tdoc의 revision 체인 | 11,243 | 44ms |
| CQ11 | LS 발신/수신 정보 | 7,598 | 19ms |
| CQ12 | LS Reply 관계 | 3,236 | 43ms |
| CQ13 | CR이 수정하는 Spec | 10,544 | 18ms |
| CQ14 | CR 카테고리/영향 범위 | 9,396 | 42ms |
| CQ15 | 연기된 Tdoc | 318 | 37ms |
| CQ16 | 들어온 LS 목록 | 1,844 | 78ms |
| CQ17 | 회사별 Work Item 기고 | 92,687 | 70ms |
| CQ18 | Agenda별 회사 기고 | 216 | 95ms |
| CQ19 | Work Item별 회사 기고 수 | 5 rows | 102ms |
| CQ20 | 회사별 채택율 | 5 rows | 147ms |
| CQ21 | 같은 Agenda의 다른 회사 기고 | 69M+ | 1,863ms |
| CQ22 | 회사별 주력 기술 영역 | 10 rows | 120ms |
| CQ23 | 여러 회의에 걸친 기고 | 10 rows | 146ms |
| CQ24 | 회의별 기고 결과 요약 | 10 rows | 165ms |
| CQ25 | 미결(not treated) Tdoc | 53,884 | 63ms |

---

## 환경 설정

### Docker Compose

```yaml
services:
  neo4j-cypher:
    image: neo4j:5.26.0
    ports:
      - "7475:7474"
      - "7688:7687"
    environment:
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_server_memory_heap_max__size=2G
    volumes:
      - ../../../ontology:/import:ro
```

### 실행 방법

```bash
# 시작
cd scripts/phase-2/neo4j
docker compose up -d neo4j-cypher

# 데이터 적재
python3 load_cypher.py

# CQ 검증
python3 validate_cq.py

# 종료
docker compose down
```

---

## 파일 구조

```
scripts/phase-2/neo4j/
├── docker-compose.yml          # Neo4j 환경
├── Dockerfile.n10s             # n10s 커스텀 이미지
├── plugins/                    # n10s 플러그인 JAR
├── load_n10s.py               # n10s 적재 스크립트
├── load_cypher.py             # Cypher 적재 스크립트 (선택됨)
├── validate_cq.py             # 참조 CQ 25개 검증
└── test_cq_practical.py       # 실전 CQ 테스트

logs/phase-2/neo4j/
├── n10s_load.log              # n10s 적재 로그
├── cypher_load.log            # Cypher 적재 로그
├── cq_validation.log          # CQ 검증 로그
└── comparison_report.md       # 비교 리포트
```

---

## 관련 문서

- [Phase-2 Overview](README.md)
- [Step-1: Ontology 구축](step1_ontology.md)
- [TDoc Ontology Spec](specs/tdoc-ontology-spec.md)
- [비교 리포트](../../logs/phase-2/neo4j/comparison_report.md)
