# spec-trace

3GPP 표준 문서 및 회의 자료 데이터 저장소

## 프로젝트 개요

3GPP RAN1 Working Group의 표준화 데이터를 수집, 정리, 분석하는 프로젝트:
- **Meetings**: 회의 자료 (TSGR1_84b ~ 122)
- **Change Requests**: 표준 변경 요청 (Rel-15 ~ 19, 1,845 CRs)
- **Specifications**: NR 물리계층 표준 문서 (8 specs: Tier 1/2/4)

## 프로젝트 구조

### 용어 위계
spec-trace 프로젝트는 명확한 계층 구조를 따릅니다:

```
Phase (프로젝트 단계)
 └─ Step (작업 순서)
     └─ Sub-step (세부 작업)
          └─ Layer (파싱 깊이 - 기술 용어)
```

**예시**:
- **Phase-1**: Data Collection & Preparation
  - **Step-6**: Document Parsing
    - **Sub-step 6-1**: Transform
    - **Layer-1 Parsing**: 구조 추출
    - **Layer-2 Parsing**: 의미 확장

상세한 용어 정의는 [CLAUDE.md](./CLAUDE.md#용어-정의-terminology)를 참조하세요.

---

## 프로젝트 상태

**Phase-1: Data Collection & Preparation** (🚧 86% 진행 중)
- ✅ Step-1: Meetings Download (62 meetings, 119,843 files)
- ✅ Step-2: Change Requests Download (1,845 CRs, 520 files)
- ✅ Step-3: Specifications Download (8 specs, 9.2 MB)
- ✅ Step-4: ZIP Extraction (42.5 GB extracted)
- ✅ Step-5: Data Cleanup for Parsing (156 MB cleaned)
- ✅ Step-6: Data Transformation for Parsing - 완료
  - ✅ Sub-step 6-1: Transform (DOC→DOCX, PPT→PPTX) - 완료
  - ✅ Sub-step 6-2: Schema Validation (25 samples)
  - ✅ Sub-step 6-3: Multi-Format Strategy - 완료
- ⏳ Step-7: Document Parsing (Layer-1) - 준비 완료
  - ⏳ Sub-step 7-1: DOCX Basic Parser
  - ⏳ Sub-step 7-2: XLSX Integration
  - ⏳ Sub-step 7-3: Advanced Features
  - ⏳ Sub-step 7-4: Full Scale Parsing

**Phase-2: Database Construction** (⏳ 계획됨)
- Vector DB (Qdrant): 의미 기반 검색
- Graph DB (Neo4j): 관계 추적
- Hybrid DB 구축

## 데이터 구조

```
data/
├── data_raw/              # 원본 다운로드 (ZIP 파일)
│   ├── meetings/RAN1/     (62 meetings, 119,843 files)
│   ├── change-requests/RAN1/ (1,845 CRs, 520 files)
│   └── specs/RAN1/        (8 specs, 9.2 MB)
│
├── data_extracted/        # 압축 해제 + 정리 완료
│   ├── meetings/RAN1/     (129,718 files, 41.84 GB, 156 MB cleaned)
│   ├── change-requests/RAN1/ (~3,000 files, ~500 MB)
│   └── specs/RAN1/        (8 files, 9.2 MB)
│
└── data_transformed/      # Transform 완료 (파싱 준비)
    └── meetings/RAN1/     (DOC→DOCX, PPT→PPTX 변환 완료)
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
