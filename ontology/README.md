# TDoc Ontology

3GPP TDoc Knowledge Graph를 위한 온톨로지 스키마 및 인스턴스 저장소.

## 디렉토리 구조

```
ontology/
├── tdoc-ontology.ttl           # 현재 활성 스키마 (v2.0.0)
├── versions/                   # 스키마 버전 히스토리
│   ├── README.md
│   ├── tdoc-ontology-v1.0.0-phase2.ttl
│   └── tdoc-ontology-v2.0.0-phase3.ttl
│
├── input/                      # 파싱 원본 데이터
│
├── intermediate/               # 중간 처리 결과
│   └── phase-2/
│       ├── NORMALIZATION_REPORT.md
│       ├── company_aliases.json
│       ├── company_aliases_significant.json
│       ├── company_raw.json
│       └── reference_summary.json
│
└── output/
    ├── instances/              # JSON-LD 인스턴스
    │   ├── phase-2/            # TDoc 메타데이터 (84.6 MB)
    │   │   ├── agenda_items.jsonld
    │   │   ├── companies.jsonld
    │   │   ├── contacts.jsonld
    │   │   ├── meetings.jsonld
    │   │   ├── releases.jsonld
    │   │   ├── specs.jsonld
    │   │   ├── tdocs.jsonld
    │   │   ├── work_items.jsonld
    │   │   └── working_groups.jsonld
    │   │
    │   └── phase-3/            # Decision/Role 데이터 (20.8 MB)
    │       ├── decisions_agreements.jsonld
    │       ├── decisions_conclusions.jsonld
    │       ├── decisions_working_assumptions.jsonld
    │       ├── summaries.jsonld
    │       └── session_notes.jsonld
    │
    ├── parsed_reports/         # 파싱 결과
    │   └── phase-3/            # Final Report 파싱 (58개 파일)
    │       └── RAN1_*.json
    │
    └── reports/                # 검증 리포트
        └── phase-2/
            ├── SPEC_VERIFICATION_REPORT.md
            └── VALIDATION_REPORT.md
```

## Phase별 산출물

### Phase-2: TDoc 메타데이터 온톨로지
- **스키마**: v1.0.0 (11 클래스, 44 속성)
- **인스턴스**: 125,480개 (84.6 MB)
- **스크립트**: `scripts/phase-2/ontology/`

### Phase-3: Decision/Role 확장 온톨로지
- **스키마**: v2.0.0 (+5 클래스, +8 속성)
- **인스턴스**: 28,146개 (20.8 MB)
- **스크립트**: `scripts/phase-3/ontology/`, `scripts/phase-3/report-parser/`

## 버전 히스토리

| 버전 | Phase | 날짜 | 변경 사항 |
|------|-------|------|----------|
| v1.0.0 | Phase-2 | 2026-01-14 | 초기 온톨로지 (TDoc 메타데이터) |
| v2.0.0 | Phase-3 | 2026-01-21 | Decision/Role 확장 |

## 관련 문서

- **Phase-2 Spec**: `docs/phase-2/specs/tdoc-ontology-spec(Tdoc_list).md`
- **Phase-3 Spec**: `docs/phase-3/specs/tdoc_ontology_specs(Final_report)`
- **버전 히스토리**: `ontology/versions/README.md`
