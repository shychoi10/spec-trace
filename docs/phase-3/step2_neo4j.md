# Step-2: Neo4j Loading

## 개요

JSON-LD 인스턴스를 Neo4j에 적재하고 Phase-2 데이터와 관계를 생성한다.

## Sub-step

| Sub-step | 내용 | 상태 |
|----------|------|------|
| 2-1 | Resolution 노드 적재 | ✅ 완료 |
| 2-2 | Summary/SessionNotes 노드 적재 | ✅ 완료 |
| 2-3 | 관계 생성 (MADE_AT, PRESENTED_AT) | ✅ 완료 |

## 노드

| 노드 | 수량 |
|------|------|
| Resolution (총계) | 24,400 |
| - Agreement | 20,787 |
| - Conclusion | 2,670 |
| - WorkingAssumption | 943 |
| Summary | 3,370 |
| SessionNotes | 662 |

## 관계

| 관계 | 설명 | 수량 |
|------|------|------|
| `RESOLUTION_BELONGS_TO` | Resolution → AgendaItem | 24,400 |
| `MADE_AT` | Resolution → Meeting | 24,646 |
| `REFERENCES` | Resolution → Tdoc | 15,229 |
| `PRESENTED_AT` | Summary/SessionNotes → Meeting | 4,032 |
| `MODERATED_BY` | Summary → Company | 3,343 |
| `CHAIRED_BY` | SessionNotes → Company | 662 |

## 스크립트

| 스크립트 | 용도 |
|----------|------|
| `scripts/phase-3/neo4j/01_load_decisions.py` | Resolution 노드 및 관계 적재 |
| `scripts/phase-3/neo4j/02_load_roles.py` | Summary/SessionNotes 노드 및 관계 적재 |

## 실행 방법

```bash
# Resolution 적재
python scripts/phase-3/neo4j/01_load_decisions.py

# Role 적재
python scripts/phase-3/neo4j/02_load_roles.py
```

## Bug Fix: Meeting ID 형식 불일치 (2026-01-22)

### 문제

e-meeting에 `-e` 접미사가 붙어 매칭 실패:
- JSON-LD: `RAN1#100b`
- Neo4j Meeting: `RAN1#100b-e`

### 해결

`STARTS WITH` 매칭으로 변경:

```cypher
-- Before
MATCH (m:Meeting) WHERE r.meetingNum IN m.meetingNumber

-- After
MATCH (m:Meeting) WHERE ANY(num IN m.meetingNumber
  WHERE num = r.meetingNum OR num STARTS WITH r.meetingNum + '-')
```

### 결과

| 관계 | Before | After |
|------|--------|-------|
| MADE_AT (Resolution) | 68.2% (16,629) | 100%+ (24,646) |
| PRESENTED_AT (Summary) | 50.4% (1,698) | 100% (3,370) |
| PRESENTED_AT (SessionNotes) | 60.3% (399) | 100% (662) |

## canonicalMeetingNumber 속성 (2026-01-26)

### 개요

COVID-era e-meeting 처리를 위한 `canonicalMeetingNumber` 속성 추가.

### 정규화 규칙

```
meetingNumber: RAN1#100-e  →  canonicalMeetingNumber: RAN1#100
meetingNumber: RAN1#101    →  canonicalMeetingNumber: RAN1#101
```

### COVID 특수 케이스 (Spec Section 5.6)

| meetingNumber | canonicalMeetingNumber | 설명 |
|---------------|------------------------|------|
| RAN1#100 | RAN1#100 | 대면 회의 (COVID로 중단) |
| RAN1#100-e | RAN1#100 | e-meeting 연속 (동일 canonical) |

**처리 원칙**: 두 Meeting 노드 모두 유지, canonicalMeetingNumber로 그룹화 가능.

### 검증 쿼리

```cypher
-- canonicalMeetingNumber 존재 확인
MATCH (m:Meeting) WHERE m.canonicalMeetingNumber IS NOT NULL
RETURN count(m) AS total
// 결과: 59

-- COVID 케이스 확인
MATCH (m:Meeting) WHERE m.meetingNumber IN ['RAN1#100', 'RAN1#100-e']
RETURN m.meetingNumber, m.canonicalMeetingNumber
// 결과: 둘 다 canonicalMeetingNumber = 'RAN1#100'
```

## Bug Fix: Meeting ID 형식 변환 (2026-01-27)

### 문제

Phase-3 JSON-LD의 `madeAt`에서 추출한 Meeting ID가 underscore 형식(`RAN1_100`)인데,
Phase-2 JSON-LD의 `canonicalMeetingNumber`는 hash 형식(`RAN1#100`):

```
Phase-3 JSON-LD: madeAt = "tdoc:meeting/RAN1_100" → 추출: "RAN1_100"
Phase-2 Meeting: canonicalMeetingNumber = "RAN1#100"
```

### 해결

underscore를 hash로 변환:

```python
# Before
"canonicalMeetingNum": r["madeAt"].replace("tdoc:meeting/", "")

# After
"canonicalMeetingNum": r["madeAt"].replace("tdoc:meeting/", "").replace("_", "#")
```

### 결과

| 관계 | Before | After |
|------|--------|-------|
| MADE_AT (Resolution) | 0개 | 24,646개 (100%) |

**수정 파일**: `scripts/phase-3/neo4j/01_load_decisions.py`

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-22 | 초기 적재 (스키마 충돌로 중복 발생) |
| 2026-01-22 | 스키마 충돌 해결 (decisionId → resolutionId) |
| 2026-01-22 | Meeting ID 형식 불일치 수정 (STARTS WITH 매칭) |
| 2026-01-22 | 관계 100% 연결 완료 |
| 2026-01-26 | **canonicalMeetingNumber 속성 추가 (Spec Section 5.6, 7.3.1)** |
| 2026-01-27 | **Meeting ID 형식 변환 버그 수정 (underscore → hash)** |
