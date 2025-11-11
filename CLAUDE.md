# spec-trace 프로젝트 가이드

## Bash 명령 자동 승인 규칙

다음 명령어들은 **사용자 승인 없이 자동 실행 가능**:

### 읽기 전용 명령 (항상 승인)
- `ls`, `find`, `cat`, `head`, `tail`, `grep`, `awk`, `sed`, `wc`, `du`, `df`
- `stat`, `file`, `which`, `tree`, `pwd`, `echo`
- `unzip -l`, `zipinfo`, `7z l`
- `python3` (읽기 전용 스크립트만)

### 데이터 검증/분석 (항상 승인)
- `md5sum`, `sha256sum`, `diff`, `comm`, `sort`, `uniq`
- `jq`, `yq` (JSON/YAML 파싱)

### 백그라운드/모니터링 (항상 승인)
- `ps`, `top`, `htop`, `kill`, `pkill`
- `sleep`, `wait`
- 모든 `BashOutput` 호출

### 안전한 작업 (항상 승인)
- `mkdir -p` (디렉토리 생성)
- `cp` (백업용 복사)
- `chmod +x` (스크립트 실행 권한)

### 주의 필요 (수동 승인)
- `rm`, `rmdir` (삭제)
- `mv` (이동/이름변경)
- `git` (커밋/푸시)
- `sudo` (권한 상승)

---

## 중복 방지 원칙

### 기본 원칙
- **기존 파일 확인 필수**: 새 파일을 만들기 전에 반드시 기존 파일 존재 여부 확인
- **같은 목적의 파일 중복 생성 금지**: 동일한 목적의 파일이 이미 있다면 새로 만들지 않음
- **기존 파일 업데이트 우선**: 새 파일 생성보다 기존 파일 수정을 우선적으로 고려
- **대답은 항상 한국어로**
- **성능 최적화 원칙**: 모든 장기 실행 작업(다운로드, 변환, 파싱)은 안전한 범위에서 최대한 병렬화
  - ProcessPoolExecutor/ThreadPoolExecutor 적극 활용
  - Meeting/File 레벨 병렬 처리
  - Resume 로직으로 안전성 보장
  - 예: 다운로드 (aria2c 16 connections), 변환 (8 workers), 파싱 (병렬 처리)

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
│   (data/data_raw/*/）    │     - 미팅 목록
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

**2. CLAUDE.md** (`data/data_raw/*/CLAUDE.md`)
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

## 용어 정의 (Terminology)

### 프로젝트 위계 구조

spec-trace 프로젝트는 다음과 같은 계층 구조를 사용합니다:

```
Phase (최상위 - 프로젝트 단계)
 └─ Step (중간 - 작업 순서)
     └─ Sub-step (하위 - 세부 작업)
          └─ Layer (기술 깊이 - 파싱 레벨만 사용)
```

**용어 설명**:
- **Phase**: 프로젝트의 큰 단계 (예: Phase-1 Data Preparation, Phase-2 DB Construction)
- **Step**: Phase 내의 순차적 작업 단위 (예: Step-1, Step-2, ..., Step-7)
- **Sub-step**: Step 내의 세부 작업 (예: Sub-step 6-1, Sub-step 6-2, Sub-step 6-3)
- **Layer**: 파싱의 기술적 깊이 (예: Layer-1 Structural, Layer-2 Semantic)
  - **중요**: Layer는 파싱 레벨을 나타내는 기술 용어로만 사용

**구조 예시**:
```
Phase-1: Data Collection & Preparation
  ├─ Step-6: Data Transformation for Parsing
  │    ├─ Sub-step 6-1: Transform (DOC→DOCX, PPT→PPTX)
  │    ├─ Sub-step 6-2: Schema Validation
  │    └─ Sub-step 6-3: Multi-Format Strategy
  └─ Step-7: Document Parsing (Layer-1)
       ├─ Sub-step 7-1: DOCX Basic Parser
       ├─ Sub-step 7-2: XLSX Integration
       ├─ Sub-step 7-3: Advanced Features
       └─ Sub-step 7-4: Full Scale Parsing
```

---

## Phase-1 구조

Phase-1은 7개의 독립적인 Step으로 구성:

```
Phase-1: Raw Data Collection & Preparation
├── Step-1: Meetings Download                [✅ COMPLETE]
├── Step-2: Change Requests Download         [✅ COMPLETE]
├── Step-3: Specifications Download          [✅ COMPLETE]
├── Step-4: ZIP Extraction                   [✅ COMPLETE]
├── Step-5: Data Cleanup for Parsing         [✅ COMPLETE]
├── Step-6: Data Transformation for Parsing  [✅ COMPLETE]
│    ├─ Sub-step 6-1: Transform (DOC→DOCX, PPT→PPTX) [✅ Complete]
│    ├─ Sub-step 6-2: Schema Validation      [✅ Complete]
│    └─ Sub-step 6-3: Multi-Format Strategy  [✅ Complete]
└── Step-7: Document Parsing (Layer-1)       [⏳ PLANNED]
     ├─ Sub-step 7-1: DOCX Basic Parser      [⏳ Planned]
     ├─ Sub-step 7-2: XLSX Integration       [⏳ Planned]
     ├─ Sub-step 7-3: Advanced Features      [⏳ Planned]
     └─ Sub-step 7-4: Full Scale Parsing     [⏳ Planned]
```

**Status**: 6/7 Steps Complete (86%) | Step-6 Complete | Step-7 Ready

### 각 Step의 필수 문서 구조

**모든 Step은 동일한 4가지 구성 요소를 가짐**:

1. **상세 가이드** (`docs/phase-1/stepN_*.md`)
   - 완전한 기술 문서 (Single Source of Truth)
   - 다운로드 절차, 성능 분석, Troubleshooting

2. **빠른 참조** (`data/data_raw/*/RAN1/CLAUDE.md`)
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
- **데이터**: `data/data_raw/change-requests/RAN1/` (1,845 CRs, 520 files, 82% coverage)
- **범위**: **8 specs** (Tier 1: 38.211-215, Tier 2: 38.201-202, Tier 4: 38.291)
- **로그**: `logs/phase-1/change-requests/RAN1/`
- **결과**:
  - 5 Releases 크롤링 완료 (Rel-15~19)
  - 509 URLs 추출 (병렬 처리, 3분)
  - 520 files 다운로드 (509 + 11 hardlinks)
  - 1,476/1,845 CRs 커버리지 (80.0%)
  - Missing: 369 CRs (Portal/FTP 누락, 3GPP 시스템 한계)

### Step-3: Specifications Download (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step3_specifications-download.md`
- **빠른 참조**: `data/data_raw/specs/RAN1/CLAUDE.md`
- **스크립트**: `scripts/phase-1/specs/RAN1/download_latest_specs.py`
- **데이터**: `data/data_raw/specs/RAN1/` (8 specs, 9.2 MB)
- **범위**: Tier 1-4 (Tier 1: 38.211-215, Tier 2: 38.201-202, Tier 4: 38.291)
- **버전**: j10 (Tier 1+4), j00 (Tier 2)
- **로그**: `logs/phase-1/specs/RAN1/`
- **Note**: 모든 Tier (1,2,4)의 CR 다운로드 완료 (1,845 CRs total)

### Step-4: ZIP Extraction (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step4_extraction.md`
- **빠른 참조**: `data/data_extracted/CLAUDE.md`
- **스크립트**: `scripts/phase-1/{meetings,change-requests,specs}/RAN1/extract_*.py`
- **데이터**: `data/data_extracted/` (120,294 ZIPs → 42.5 GB, 99.93% success)
- **로그**: `logs/phase-1/{meetings,change-requests,specs}/RAN1/extraction.log`

### Step-5: Data Cleanup for Parsing (✅ COMPLETE)
- **상세 가이드**: `docs/phase-1/step5_data-cleanup-for-parsing.md`
- **목적**: Phase-2 파싱을 위한 데이터 정리
- **결과**:
  - 59 meetings 처리 (62개 중 3개는 FTP에서 비어있음)
  - 156 MB cleanup 완료
  - Archive 폴더: 0개 (100% 제거)
  - 중복 Draft: 0개 (100% 제거)
  - 깨끗한 구조: 58/59 미팅 (98.3%)
  - Known Issue: TSGR1_100 Report 폴더 누락
- **스크립트**: `scripts/phase-1/data-cleanup/RAN1/cleanup_reports_phase*.py`
- **로그**: `logs/phase-1/data-cleanup/RAN1/`