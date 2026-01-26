# Step-1: Report Parsing & JSON-LD Generation

## 개요

Final Report (DOCX/DOCM)를 파싱하여 Resolution과 Role 정보를 추출하고 JSON-LD 형식으로 변환한다.

## Sub-step

| Sub-step | 내용 | 상태 |
|----------|------|------|
| 1-1 | Final Report 파싱 | ✅ 완료 |
| 1-2 | Resolution/Role 추출 | ✅ 완료 |
| 1-3 | JSON-LD 인스턴스 생성 | ✅ 완료 |

## 파이프라인

```
Final Reports (DOCX/DOCM)
        │
        ▼
┌─────────────────────────────┐
│  1. TOC → Agenda Mapping    │
│  2. Section Building        │
│  3. Decision Extraction     │
│  4. Role Extraction         │
└─────────────────────────────┘
        │
        ▼
JSON-LD Instances (28,432개)
```

## Resolution ID 명명 규칙

```
{TYPE}-{MEETING}-{AGENDA}-{SEQ}
```

| 요소 | 설명 | 예시 |
|------|------|------|
| `TYPE` | Resolution 유형 | `AGR`, `CON`, `WA` |
| `MEETING` | 회의 번호 | `100`, `112` |
| `AGENDA` | Agenda Item 번호 | `5.1`, `9.1.1` |
| `SEQ` | 순번 (3자리) | `001`, `002` |

**예시**: `AGR-112-7.2-001` = RAN1#112 회의, Agenda 7.2의 첫 번째 Agreement

## 출력 파일

| 파일 | 인스턴스 수 | 용량 |
|------|-------------|------|
| `resolutions_agreements.jsonld` | 20,787 | 17.4 MB |
| `resolutions_conclusions.jsonld` | 2,670 | 1.9 MB |
| `resolutions_working_assumptions.jsonld` | 943 | 0.9 MB |
| `summaries.jsonld` | 3,370 | 1.1 MB |
| `session_notes.jsonld` | 662 | 0.2 MB |
| **총계** | **28,432** | **21.5 MB** |

## 스크립트

| 스크립트 | 용도 |
|----------|------|
| `scripts/phase-3/report-parser/` | Final Report 파싱 모듈 |
| `scripts/phase-3/ontology/01_generate_jsonld.py` | JSON-LD 생성 |

## 파일 위치

```
ontology/
├── versions/
│   └── tdoc-ontology-v2.0.0-phase3.ttl   # TTL Schema
│
└── output/
    ├── instances/phase-3/                 # JSON-LD Instances
    └── parsed_reports/v2/                 # Parsed Reports
```

## Bug Fixes

### Spec 용어 준수 (Decision → Resolution)

- `tdoc:Decision` → `tdoc:Resolution`
- `tdoc:decisionId` → `tdoc:resolutionId`
- `tdoc:decisionBelongsTo` → `tdoc:resolutionBelongsTo`

### Parser Bug Fixes

1. **Inline Agreement 패턴 누락**: `DECISION_PATTERNS_INLINE` 추가
2. **TOC Annex 조기 진입**: `toc` 스타일 단락 스킵
3. **DOCM 처리 동기화**: `_extract_decisions_docm()` 동일 로직 적용

## UNKNOWN 값 분석

| 데이터 유형 | UNKNOWN 비율 | 원인 |
|------------|--------------|------|
| Resolution | 0.1% | 섹션 위치 매칭 실패 |
| Session Notes | 3.0% | "Agenda Item X.X" 패턴 미인식 |
| FL/Moderator Summary | 80~97% | 원본에 Agenda 번호 없음 |

**결론**: FL/Moderator Summary의 UNKNOWN은 원본 Final Report 자체에 Agenda 번호가 없어 파싱으로 해결 불가

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-21 | 초기 파싱 완료 (24,114 decisions) |
| 2026-01-21 | Parser 버그 수정 (TOC Annex, Inline patterns) |
| 2026-01-21 | DOCM 처리 수정 (+1,478 → 24,400) |
| 2026-01-21 | Spec 용어 수정 (Decision → Resolution) |
