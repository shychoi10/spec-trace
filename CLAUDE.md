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

## Phase-2: RAN1 Graph DB 구축

### 최종 목표
**RAN1 Graph DB 구축** - 3GPP RAN1 문서들의 관계를 Graph DB로 저장하여 검색 및 분석 가능하게 만들기

### 핵심 아키텍처

**Multi-Agent System (Tool Calling 패턴)**:
```
Meta Orchestrator (Section 분석 → Agent 선택)
    ├─ LS Analyst Agent (Liaison Statement 전문)
    │   - 감지: "LS on", "Reply LS", "incoming LS"
    │   - 분할: Decision 기반
    │   - 출력: Issue (Actionable/Non-action/Reference)
    │
    ├─ Study Item Agent (Work/Study Item 전문)
    │   - 감지: "Agreement", "Working assumption", "FFS"
    │   - 분할: Summary 기반
    │   - 출력: Issue (계층 구조)
    │
    └─ General Agent (폴백용)
        - 기타 패턴 처리
        - 동적 학습 트리거
```

### 설계 원칙
- **일반화된 Agent**: Section 번호에 종속되지 않음
- **Tool Calling 패턴**: 콘텐츠 분석 → 키워드 점수 → Agent 동적 선택
- **자율적 의사결정**: Agent가 분할 패턴, 출력 형식 결정

---

## 🚨 콘텐츠 기반 네이밍 원칙 (CRITICAL - 반드시 준수)

### 핵심 원칙
**모든 코드, 파일명, 변수명은 Section 번호가 아닌 콘텐츠 유형으로 명명해야 합니다.**

3GPP 문서에서 콘텐츠의 위치(Section 번호)는 미팅마다 달라질 수 있습니다.
따라서 "Section 5"가 아닌 "Incoming LS"로 식별해야 합니다.

### 절대 금지 사항 ❌
1. **파일명에 Section 번호 사용 금지**
   - ❌ `section5_workflow.py`
   - ✅ `incoming_ls_workflow.py`

2. **클래스명에 Section 번호 사용 금지**
   - ❌ `Section5State`, `Section5Workflow`
   - ✅ `IncomingLSState`, `IncomingLSWorkflow`

3. **출력 파일명에 Section 번호 사용 금지**
   - ❌ `RAN1_120_section5_output.md`
   - ✅ `RAN1_120_incoming_ls_output.md`

4. **설정 키에 Section 번호 사용 금지**
   - ❌ `section5_hints`
   - ✅ `incoming_ls_hints`

5. **주석/docstring에 Section 번호 하드코딩 금지**
   - ❌ "Section 5 처리"
   - ✅ "Incoming LS 처리 (콘텐츠 기반)"

### 올바른 콘텐츠 기반 명명 예시

| 콘텐츠 유형 | ✅ 올바른 이름 | ❌ 잘못된 이름 |
|------------|---------------|---------------|
| Incoming Liaison Statements | `incoming_ls_*` | `section5_*` |
| Reports and Work Plan | `reports_work_plan_*` | `section6_*` |
| Draft Liaison Statements | `draft_ls_*` | `section7_*` |
| Maintenance | `maintenance_*` | `section8_*` |
| Work Items | `work_items_*` | `section9_*` |

### 이 원칙이 중요한 이유

1. **문서 구조의 가변성**: RAN1#120에서는 Incoming LS가 Section 5이지만, 다른 미팅에서는 다른 번호일 수 있음
2. **재사용성**: 콘텐츠 기반 코드는 어떤 미팅에서도 동작
3. **유지보수성**: Section 번호 변경에 영향받지 않음
4. **일반화**: Multi-Agent 시스템이 다양한 미팅에 적용 가능

### 코드 리뷰 체크리스트

새 코드 작성 시 반드시 확인:
- [ ] 파일명에 `section[0-9]` 패턴이 없는가?
- [ ] 클래스/함수명에 Section 번호가 없는가?
- [ ] 출력 파일명이 콘텐츠 기반인가?
- [ ] 설정 키가 콘텐츠 유형으로 되어 있는가?
- [ ] 주석에 Section 번호 대신 콘텐츠 유형이 사용되었는가?

---

## 🚨 True Agentic AI 원칙 (CRITICAL)

### 핵심 원칙
**모든 텍스트 분석, 분류, 추출은 반드시 LLM이 수행해야 합니다.**

### 절대 금지 사항 ❌
1. **정규식(Regex) 사용 금지**: 텍스트 패턴 매칭에 regex 사용 금지
2. **하드코딩된 규칙 금지**: if-else 기반 분류 로직 금지
3. **Rule-based 폴백 금지**: LLM 실패 시에도 regex fallback 사용 금지
4. **키워드 매칭 금지**: 단순 문자열 검색 기반 분류 금지

### 허용 사항 ✅
1. **LLM 프롬프트**: 모든 분석은 LLM에게 프롬프트로 요청
2. **JSON 파싱**: LLM 응답의 구조화된 출력 파싱 (json.loads)
3. **데이터 변환**: LLM 출력의 타입 변환 (str→enum, dict→dataclass)
4. **파일 I/O**: 파일 읽기/쓰기 작업

### 위반 예시 vs 올바른 구현

```python
# ❌ 잘못된 구현 (regex 사용)
def _fallback_extract(self, text: str) -> list[str]:
    pattern = r"R1-\d{7}"
    return re.findall(pattern, text)

# ✅ 올바른 구현 (LLM 전용)
def _extract_tdocs(self, text: str) -> list[str]:
    prompt = f"Extract all Tdoc IDs (R1-XXXXXXX format) from:\n{text}"
    response = self.llm.generate(prompt)
    return self._parse_tdoc_list(response)
```

### 적용 범위
- **BoundaryDetector**: Issue 경계 감지 → LLM 전용
- **MetadataExtractor**: 메타데이터 추출 → LLM 전용
- **TdocLinker**: Tdoc 추출 및 분류 → LLM 전용
- **DecisionClassifier**: Issue Type 분류 → LLM 전용
- **SummaryGenerator**: 요약 생성 → LLM 전용
- **DocumentParser**: Section 추출 → LLM 전용

### 이 원칙의 이유
1. **일관성**: LLM이 모든 분석을 수행하여 일관된 품질 보장
2. **유연성**: 새로운 패턴도 프롬프트 수정만으로 대응 가능
3. **정확성**: 컨텍스트 기반 분석으로 더 높은 정확도
4. **유지보수성**: regex 패턴 관리 불필요

### 기술 스택
- **Framework**: LangGraph (Agentic AI 워크플로우)
- **LLM**: GPT-4o (via OpenRouter)
- **Input**: Final Minutes DOCX, TDoc List XLSX
- **Process**: DOCX → Section → Agent 처리 → Structured Features → Graph DB

### 현재 진행 상황 (Step-1: LangGraph Trials)
- ✅ Section 5: 100% Coverage (20/20 Issues)
- ✅ Meeting Number 자동 추출 (LLM 기반)
- ✅ Section Overview 생성 (Korean summary + categories)
- ✅ BaseAgent, MetaOrchestrator 구현
- ⏳ Multi-Agent 아키텍처 완성중

### 문서 및 경로
- **Phase-2 개요**: `docs/phase-2/README.md`
- **Step-1 상세 가이드**: `docs/phase-2/step-1-langgraph-trials.md`
- **스크립트**: `scripts/phase-2/step-1-langgraph-trials/`
- **Agent 구현**: `scripts/phase-2/step-1-langgraph-trials/agents/`
- **로그**: `logs/phase-2/step-1-langgraph-trials/`
- **출력**: `output/phase-2/step-1-langgraph-trials/`

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
- **Step**: Phase 내의 순차적 작업 단위 (예: Step-1, Step-2, ..., Step-6)
- **Sub-step**: Step 내의 세부 작업 (예: Sub-step 6-1, Sub-step 6-2, Sub-step 6-3)
- **Layer**: 파싱의 기술적 깊이 (예: Layer-1 Structural, Layer-2 Semantic)
  - **중요**: Layer는 파싱 레벨을 나타내는 기술 용어로만 사용

**구조 예시**:
```
Phase-1: Data Collection & Preparation
  └─ Step-6: Data Transformation for Parsing
       ├─ Sub-step 6-1: Transform (DOC→DOCX, PPT→PPTX)
       ├─ Sub-step 6-2: Schema Validation
       └─ Sub-step 6-3: Multi-Format Strategy
```

---

## Phase-1 구조

Phase-1은 6개의 독립적인 Step으로 구성:

```
Phase-1: Raw Data Collection & Preparation
├── Step-1: Meetings Download                [✅ COMPLETE]
├── Step-2: Change Requests Download         [✅ COMPLETE]
├── Step-3: Specifications Download          [✅ COMPLETE]
├── Step-4: ZIP Extraction                   [✅ COMPLETE]
├── Step-5: Data Cleanup for Parsing         [✅ COMPLETE]
└── Step-6: Data Transformation for Parsing  [✅ COMPLETE]
     ├─ Sub-step 6-1: Transform (DOC→DOCX, PPT→PPTX) [✅ Complete]
     ├─ Sub-step 6-2: Schema Validation      [✅ Complete]
     └─ Sub-step 6-3: Multi-Format Strategy  [✅ Complete]
```

**Status**: 6/6 Steps Complete (100%) | Phase-1 Complete

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
- **데이터**: `data/data_extracted/` (119,797 ZIPs → 42.5 GB, 99.988% success)
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