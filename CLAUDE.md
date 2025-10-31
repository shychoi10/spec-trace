# spec-trace 프로젝트 가이드

## 중복 방지 원칙

### 기본 원칙
- **기존 파일 확인 필수**: 새 파일을 만들기 전에 반드시 기존 파일 존재 여부 확인
- **같은 목적의 파일 중복 생성 금지**: 동일한 목적의 파일이 이미 있다면 새로 만들지 않음
- **기존 파일 업데이트 우선**: 새 파일 생성보다 기존 파일 수정을 우선적으로 고려
- **대답은 항상 한국어로**

---

## 문서 구조 (Documentation Structure)

### 파일 간 관계

```
┌─────────────────────┐
│   Agent 파일        │  → 실행 방법 + docs 참조
│   (.claude/agents/) │
└──────────┬──────────┘
           │ references
           ↓
┌─────────────────────┐
│   docs 폴더         │  ← 완전한 기술 가이드 (Single Source of Truth)
│   (docs/)           │     - 상세 기술 설명
└──────────┬──────────┘     - Performance 분석
           ↑                - Lessons learned
           │ references     - Troubleshooting
┌──────────┴──────────┐
│   CLAUDE.md         │  → 빠른 참조 (Quick Reference)
│   (data_raw/*/）    │     - 미팅 목록
└─────────────────────┘     - 현재 상태
```

### 파일별 역할

**1. Agent 파일** (`.claude/agents/*.md`)
- **목적**: Agent 정의 + 실행 가이드
- **내용**:
  - Agent 설명 (when to use, examples)
  - 스크립트 실행 명령
  - 기본 설정
- **특징**: 간결하게, 상세 내용은 docs 참조

**2. CLAUDE.md** (`data_raw/*/CLAUDE.md`)
- **목적**: Quick Reference Spec
- **내용**:
  - 미팅/파일 목록
  - 다운로드 범위
  - 현재 상태
- **특징**: 빠른 참조용, 상세 설명은 docs 참조

**3. docs** (`docs/**/*.md`)
- **목적**: Single Source of Truth (완전한 기술 문서)
- **내용**:
  - 전체 프로세스 상세 설명
  - 기술적 배경 및 근거
  - 성능 통계 및 분석
  - Lessons learned
  - Troubleshooting
- **특징**: 모든 상세 내용의 유일한 소스

---

## 문서 관리 원칙

### DRY (Don't Repeat Yourself)
- 같은 내용을 여러 파일에 중복하지 않음
- 참조 링크 사용 (예: "See docs/... for details")

### Single Source of Truth
- 상세 기술 설명은 **docs 폴더에만** 작성
- Agent와 CLAUDE.md는 docs를 참조

### Clear Hierarchy
```
Agent/CLAUDE.md (간단) → docs (상세)
```

### 유지보수 가이드라인

1. **기술 내용 업데이트**: docs만 수정
2. **실행 명령 변경**: Agent + docs 동시 업데이트
3. **상태 정보 변경**: CLAUDE.md 수정
4. **새 기능 추가**: docs 먼저 작성 → Agent/CLAUDE.md 참조 추가

---

## Phase-1 구조 (5-Step Workflow)

Phase-1은 5개의 독립적인 Step으로 구성:

```
Phase-1: Raw Data Collection & Preparation
├── Step-1: Meetings Download         [✅ COMPLETE]
├── Step-2: Change Requests Download  [✅ COMPLETE]
├── Step-3: Specifications Download   [✅ COMPLETE]
├── Step-4: ZIP Extraction            [✅ COMPLETE]
└── Step-5: Data Cleanup for Parsing  [⏳ PLANNED]
```

**Status**: Steps 1-4 Complete (100%) | Step-5 Planned

### 각 Step의 필수 문서 구조

**모든 Step은 동일한 4가지 구성 요소를 가짐**:

1. **상세 가이드** (`docs/phase-1/stepN_*.md`)
   - 완전한 기술 문서 (Single Source of Truth)
   - 다운로드 절차, 성능 분석, Troubleshooting

2. **빠른 참조** (`data_raw/*/RAN1/CLAUDE.md`)
   - 타겟 목록 (meetings/CRs/specs)
   - 현재 상태, 빠른 명령어
   - 상세 가이드 참조 링크

3. **실행 스크립트** (`scripts/*/RAN1/`)
   - Python 실행 스크립트
   - 다단계 워크플로우는 번호 prefix (01-05)

4. **작업 로그** (`logs/*/RAN1/`)
   - 실행 로그, 검증 리포트
   - aria2c 입력 파일

---

## 주요 문서 위치

### Phase-1 Overview
- **전체 개요**: `docs/phase-1/README.md`
- **진행 상황**: `progress.md` (root)

### Step-1: Meetings Download (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step1_meetings-download.md`
- **빠른 참조**: `data/data_raw/meetings/RAN1/CLAUDE.md`
- **Agent**: `.claude/agents/3gpp-meeting-downloader.md`
- **스크립트**: `scripts/phase-1/meetings/RAN1/`
- **데이터**: `data/data_raw/meetings/RAN1/` (62 meetings, 119,843 files)
- **로그**: `logs/phase-1/meetings/RAN1/`

### Step-2: Change Requests Download (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step2_change-requests-download.md`
- **빠른 참조**: `data/data_raw/change-requests/RAN1/CLAUDE.md`
- **스크립트**: `scripts/phase-1/change-requests/RAN1/` (5-step pipeline: 01-05)
- **데이터**: `data/data_raw/change-requests/RAN1/` (451 CRs, 105 unique files, 100%)
- **로그**: `logs/phase-1/change-requests/RAN1/`

### Step-3: Specifications Download (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step3_specifications-download.md`
- **빠른 참조**: `data/data_raw/specs/RAN1/CLAUDE.md`
- **스크립트**: `scripts/phase-1/specs/RAN1/download_latest_specs.py`
- **데이터**: `data/data_raw/specs/RAN1/` (5 specs, 7.7 MB, version j10)
- **로그**: `logs/phase-1/specs/RAN1/`

### Step-4: ZIP Extraction (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step4_extraction.md`
- **빠른 참조**: `data/data_extracted/CLAUDE.md`
- **스크립트**: `scripts/phase-1/{meetings,change-requests,specs}/RAN1/extract_*.py`
- **데이터**: `data/data_extracted/` (119,797 ZIPs → 42 GB, 99.93% success)
- **로그**: `logs/phase-1/{meetings,change-requests,specs}/RAN1/extraction.log`

### Step-5: Data Cleanup for Parsing (⏳ PLANNED)
- **상세 가이드**: `docs/phase-1/step5_data-cleanup-for-parsing.md`
- **목적**: Phase-2 파싱을 위한 데이터 정리
- **타겟**:
  - System metadata: 40 MB (__MACOSX, .DS_Store)
  - Report archives: 70-100 MB (Draft 버전들)
  - Temp files: <1 MB (*.tmp, empty dirs)
- **절약**: 110-140 MB 예상
- **스크립트**: `scripts/phase-1/data-cleanup/RAN1/` (계획 중)
- **로그**: `logs/phase-1/data-cleanup/RAN1/` (계획 중)