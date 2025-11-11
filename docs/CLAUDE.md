# spec-trace 문서 가이드 (Documentation Guide)

## 목적

이 문서는 `docs/` 폴더의 모든 기술 문서에 대한 네비게이션과 개요를 제공합니다.

---

## 용어 정의 (Terminology)

### 프로젝트 위계 구조

```
Phase (프로젝트 단계)
 └─ Step (작업 순서)
     └─ Sub-step (세부 작업)
          └─ Layer (파싱 깊이 - 기술 용어)
```

**용어 설명**:
- **Phase**: 프로젝트의 큰 단계 (예: Phase-1 Data Preparation, Phase-2 DB Construction)
- **Step**: Phase 내의 순차적 작업 단위 (예: Step-1, Step-2, ..., Step-7)
- **Sub-step**: Step 내의 세부 작업 (예: Sub-step 6-1, Sub-step 6-2, Sub-step 6-3)
- **Layer**: 파싱의 기술적 깊이 (예: Layer-1 Structural, Layer-2 Semantic)
  - **중요**: Layer는 파싱 레벨을 나타내는 기술 용어로만 사용

---

## Phase-1: Data Collection & Preparation

**목표**: 3GPP 표준화 데이터 수집 및 파싱 준비

**전체 상태**: 🚧 86% 진행 중 (7개 Step 중 6개 완료)

### Step-by-Step 가이드

#### ✅ Step-1: Meetings Download (COMPLETE)
**문서**: [step1_meetings-download.md](./phase-1/step1_meetings-download.md)

**요약**:
- 3GPP FTP에서 RAN1 회의 자료 다운로드 (TSGR1_84 ~ 122)
- 62개 미팅, 119,843개 파일
- aria2c 기반 병렬 다운로드
- 출력: `data/data_raw/meetings/RAN1/`

**주요 내용**:
- FTP 구조 분석 및 타겟 설정
- 2단계 워크플로우 (generate list → download)
- 성능 최적화 (16 connections, 5 splits)

---

#### ✅ Step-2: Change Requests Download (COMPLETE)
**문서**: [step2_change-requests-download.md](./phase-1/step2_change-requests-download.md)

**요약**:
- 3GPP Portal에서 NR 물리계층 스펙 (Tier 1+2+4) CR 다운로드
- 1,845 CRs, 520 파일 (Rel-15 ~ 19)
- 5단계 파이프라인 (crawl → generate → download → verify → link)
- 출력: `data/data_raw/change-requests/RAN1/`

**주요 내용**:
- Portal 크롤링 및 메타데이터 수집
- FTP URL 매핑 및 중복 처리
- 다운로드 검증 로직

---

#### ✅ Step-3: Specifications Download (COMPLETE)
**문서**: [step3_specifications-download.md](./phase-1/step3_specifications-download.md)

**요약**:
- NR 물리계층 스펙 최신 버전 다운로드
- 8개 스펙 (Tier 1/2/4), 9.2 MB
- 자동 버전 감지 (j10 = v19.1.0)
- 출력: `data/data_raw/specs/RAN1/`

**주요 내용**:
- FTP 디렉토리 파싱 및 버전 추출
- Python requests 기반 단순 다운로드
- 다운로드 상태 추적

---

#### ✅ Step-4: ZIP Extraction (COMPLETE)
**문서**: [step4_extraction.md](./phase-1/step4_extraction.md)

**요약**:
- 다운로드된 ZIP 파일 압축 해제
- 3개 Sub-steps (Meetings, CRs, Specs)
- 119,687/119,766 ZIPs 처리 (99.93%), 42 GB
- 출력: `data/data_extracted/`

**Sub-steps**:
- **Sub-step 4-1**: Meetings Extraction (중첩 압축 해제, 병렬 처리)
- **Sub-step 4-2**: Change Requests Extraction (단순 압축 해제)
- **Sub-step 4-3**: Specifications Extraction (제자리 압축 해제)

**주요 내용**:
- ThreadPoolExecutor 병렬 처리 (8 workers)
- 손상된 ZIP 처리 (79개, 0.07%)
- Resume capability

---

#### ✅ Step-5: Data Cleanup for Parsing (COMPLETE)
**문서**: [step5_data-cleanup-for-parsing.md](./phase-1/step5_data-cleanup-for-parsing.md)

**요약**:
- 파싱 준비를 위한 데이터 정리
- 3개 Sub-steps (시스템 메타데이터, 회의 리포트, 임시 파일)
- 156 MB 절약, 98.3% 미팅 정리 완료
- 출력: 깨끗한 `data/data_extracted/`

**Sub-steps**:
- **Sub-step 5-1**: System Metadata Cleanup (40 MB, ZERO risk)
  - `__MACOSX/` 디렉토리 제거
  - `.DS_Store` 파일 제거
- **Sub-step 5-2**: Meeting Reports Cleanup (70-100 MB, LOW-MED risk)
  - `Report/Archive/` Draft 버전 정리
  - 6-Category 분석 및 조건부 삭제
- **Sub-step 5-3**: Duplicate/Temp Cleanup (<1 MB, LOW risk)
  - 임시 파일 제거
  - 빈 디렉토리 정리

**주요 내용**:
- 파싱 대상 명확화 (DOC/DOCX 98% coverage)
- Risk-based cleanup strategy
- 59개 미팅 처리 (3개 FTP 비어있음)

---

#### ✅ Step-6: Data Transformation for Parsing (COMPLETE)
**문서**: [step6_data-transformation-for-parsing.md](./phase-1/step6_data-transformation-for-parsing.md)

**요약**:
- 문서를 파싱 가능한 형태로 변환 (전처리)
- DOC→DOCX, PPT→PPTX 변환, 스키마 검증, 전략 수립
- 상태: 완료 (전체 3개 Sub-step 100%)
- 출력: `data/data_transformed/`
- 성공률: 99.99% (13개 TIMEOUT 파일, 0.01%)

**Sub-steps**:
- **✅ Sub-step 6-1**: Transform (DOC→DOCX, PPT→PPTX 변환 완료)
  - 상태: 완료 (59/59 meetings, 99.99%)
  - DOC/PPT 직접 파싱 불가 연구 완료
  - LibreOffice headless 변환 사용
  - 병렬 처리: 8 workers
  - Known Issue: 13개 TIMEOUT (0.01%, LTE 레거시 스펙)
- **✅ Sub-step 6-2**: Schema Validation (완료)
  - 25개 샘플 검증 (18/25 성공, 72%)
  - Schema v2.0 필드 coverage 분석
  - MUST HAVE vs OPTIONAL 분류
- **✅ Sub-step 6-3**: Multi-Format Strategy (완료)
  - PPTX 전략: 메타데이터만 추출 (99.5% standalone)
  - XLSX 전략: 3-tier classification (simulation/rrc/admin)
  - 폴더 레벨 파싱 전략 수립

**주요 내용**:
- **DOC/PPT 변환 필요성 입증**: 직접 파싱 불가능
- **Multi-Format Strategy 수립**: PPTX/XLSX 처리 방안
- **TDoc Folder Composition 분석**: 119,565 폴더
- **Schema v2.0 검증 완료**: 실제 데이터 기반
- **TIMEOUT 재시도**: 120초 timeout에도 13개 실패 (LTE 스펙, 무시 가능)

---

#### ⏳ Step-7: Document Parsing (Layer-1) (READY TO START)
**문서**: [step7_document-parsing.md](./phase-1/step7_document-parsing.md)

**요약**:
- 변환된 문서를 JSON Layer-1 포맷으로 파싱
- 4개 Document Types (TDocs, Report, CRs, Specs)
- 전제 조건: ✅ Step-6 완료 (Transform, Schema, Strategy)
- 출력: `data/data_parsed/`
- 상태: 이전 작업 정리 완료 (2025-11-10), 새로 시작 준비됨

**Sub-steps**:
- **⏳ Sub-step 7-1**: DOCX Basic Parser (계획됨)
  - 메타데이터 + 텍스트 + 참조 추출
  - 50개 샘플 테스트
  - 1-2일 예상
- **⏳ Sub-step 7-2**: XLSX Integration (계획됨)
  - XLSX 분류 로직 구현 (simulation/rrc/admin)
  - 30개 multi-format 폴더 테스트
  - 1-2일 예상
- **⏳ Sub-step 7-3**: Advanced Features (계획됨)
  - 표, 수식, 이미지 추출
  - 40개 rich-content TDoc 테스트
  - 2-3일 예상
- **⏳ Sub-step 7-4**: Full Scale Parsing (계획됨)
  - 전체 119,565 폴더 파싱
  - 병렬 처리, 에러 핸들링
  - 2-3일 예상

**Output Schema v2.0**:
- MUST HAVE: tdoc_id, location, source_company
- SHOULD HAVE: title, agenda_item, document_for
- OPTIONAL: proposals, observations, release
- RARE: work_item, meeting, date
- Supplementary: pptx_files[], xlsx_files[]

---

## 문서 버전 관리

| 문서 | 버전 | 마지막 업데이트 | 상태 |
|------|------|----------------|------|
| step1_meetings-download.md | 1.0 | 2025-10-30 | ✅ Complete |
| step2_change-requests-download.md | 1.0 | 2025-10-30 | ✅ Complete |
| step3_specifications-download.md | 1.0 | 2025-10-30 | ✅ Complete |
| step4_extraction.md | 1.2 | 2025-11-10 | ✅ Complete (Advanced recovery 추가) |
| step5_data-cleanup-for-parsing.md | 1.1 | 2025-11-04 | ✅ Complete (용어 수정) |
| step6_data-transformation-for-parsing.md | 1.2 | 2025-11-10 | ✅ Complete (TIMEOUT retry 추가) |
| step7_document-parsing.md | 1.0 | 2025-11-04 | ⏳ Planned (Step-6/7 분리) |

---

## Phase-2: Database Construction (계획됨)

**목표**: Vector DB + Graph DB Hybrid 구축

**상태**: ⏳ Phase-1 완료 후 시작

**예정 내용**:
- Vector DB (Qdrant): 의미 기반 검색
- Graph DB (Neo4j): 관계 추적
- Hybrid 쿼리 인터페이스

---

## 빠른 참조 (Quick Reference)

### 현재 작업
- **Step-6**: Transform 완료 (100%)
- **다음 단계**: Step-7 Document Parsing 준비 완료

### 데이터 위치
- **원본 다운로드**: `data/data_raw/`
- **압축 해제**: `data/data_extracted/`
- **변환 중**: `data/data_transformed/`
- **파싱 결과**: `data/data_parsed/` (예정)

### 주요 통계
- **Meetings**: 62개, 119,843 파일 → 129,718 파일 (압축 해제)
- **Change Requests**: 1,845 CRs, 520 파일 → ~3,000 파일 (압축 해제)
- **Specifications**: 8 스펙, 9.2 MB → 9.9 MB (압축 해제)
- **총 용량**: ~42 GB (extracted)

---

**Document Version**: 1.1
**Last Updated**: 2025-11-10
**Maintainer**: Claude + User
