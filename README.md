# spec-trace

3GPP 표준 문서 및 회의 자료 데이터 저장소

## 프로젝트 개요

3GPP RAN1 Working Group의 표준화 데이터를 수집, 정리, 분석하는 프로젝트:
- **Meetings**: 회의 자료 (TSGR1_84b ~ 122)
- **Change Requests**: 표준 변경 요청 (Rel-15 ~ 19)
- **Specifications**: NR 물리계층 표준 문서 (38.211-215)

## 프로젝트 상태

**Phase-1: Raw Data Collection & Preparation** (✅ 100% 완료)
- ✅ Step-1: Meetings Download (62 meetings)
- ✅ Step-2: Change Requests Download (451 CRs)
- ✅ Step-3: Specifications Download (5 specs)
- ✅ Step-4: ZIP Extraction (42 GB)
- ✅ Step-5: Data Cleanup for Parsing (156 MB cleaned)

**Phase-2: Data Parsing** (준비 완료)
- DOC/DOCX 파싱 (121,032 files)
- 메타데이터 추출
- 데이터베이스 적재

## 데이터 구조

```
data/
├── data_raw/              # 원본 다운로드 (ZIP 파일)
│   ├── meetings/RAN1/     (62 meetings, 119,843 files)
│   ├── change-requests/RAN1/ (451 CRs, 105 files)
│   └── specs/RAN1/        (5 specs, 7.7 MB)
│
└── data_extracted/        # 압축 해제 + 정리 완료
    ├── meetings/RAN1/     (129,718 files, 41.84 GB, 156 MB cleaned)
    ├── change-requests/RAN1/ (706 files, 122 MB)
    └── specs/RAN1/        (5 files, 9.9 MB)
```

## 문서

- **프로젝트 가이드**: [CLAUDE.md](./CLAUDE.md)
- **진행 상황**: [progress.md](./progress.md)
- **Phase-1 상세**: [docs/phase-1/README.md](./docs/phase-1/README.md)

## 주의사항

- `data/` 디렉토리는 Git에 추적되지 않습니다 (용량 매우 큼)
- 로컬 환경에서만 사용됩니다

## 라이센스

이 저장소는 3GPP 데이터를 포함하고 있으며, 3GPP의 저작권 정책을 따릅니다.
