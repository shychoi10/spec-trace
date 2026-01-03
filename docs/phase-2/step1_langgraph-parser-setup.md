# Step-1: LangGraph Parser 프로젝트 구조 + State + Models

## 목표

명세서(Tdoc_parser_specs.md)를 기반으로 **3GPP Final Minutes Report 파서**의 기반 구조를 구축한다.

**최종 목표**: 모든 RAN1 회의록(TSGR1_84b ~ 122)을 파싱하여 GraphDB 구축용 YAML 파일 생성

**Step-1 목표**:
- 프로젝트 디렉토리 구조 생성
- Pydantic 데이터 모델 정의 (명세서 3장 기반)
- LangGraph State 정의
- 설정 파일 및 의존성 정의

---

## 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| LLM | OpenRouter + Gemini | google/gemini-2.0-flash-001 |
| API 키 관리 | .env + python-dotenv | OPENROUTER_API_KEY |
| 가상환경 | 기존 프로젝트 .venv 사용 | Python 3.11.14 |
| 문서 변환 | **python-docx** | .docx 직접 파싱 (하이라이트 마커 보존) |

> **Note**: pandoc은 하이라이트를 `{.mark}`로 변환하지 못해 Agreement 마커 인식 불가 → python-docx 채택

---

## 프로젝트 구조

```
scripts/phase-2/langgraph-parser/
├── src/
│   ├── __init__.py
│   ├── state.py                      # ParserState 정의
│   ├── graph.py                      # LangGraph 그래프 정의
│   │
│   ├── pipeline/                     # 역할별 노드 (LangGraph 노드)
│   │   ├── __init__.py
│   │   ├── role_0_preprocess.py      # 역할 0: python-docx 변환
│   │   ├── role_1_metadata.py        # 역할 1: 메타데이터 추출
│   │   ├── role_2_toc.py             # 역할 2: TOC 파싱 + section_type
│   │   ├── role_3_sections.py        # 역할 3: 섹션 처리 (Orchestrator)
│   │   └── role_4_validation.py      # 역할 4: 검증 + 크로스체크
│   │
│   ├── agents/                       # 명세서 5장 Agent 구조
│   │   ├── __init__.py
│   │   │
│   │   ├── section_agents/           # Section Agent (3종)
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseSectionAgent
│   │   │   ├── technical.py          # TechnicalAgent
│   │   │   ├── incoming_ls.py        # IncomingLSAgent
│   │   │   └── annex.py              # AnnexAgent
│   │   │
│   │   └── subsection_agents/        # SubSection Agent (6종)
│   │       ├── __init__.py
│   │       ├── base.py               # BaseSubSectionAgent
│   │       ├── maintenance.py        # MaintenanceSubAgent
│   │       ├── release.py            # ReleaseSubAgent
│   │       ├── study.py              # StudySubAgent
│   │       ├── ue_features.py        # UEFeaturesSubAgent
│   │       ├── ls.py                 # LSSubAgent
│   │       └── annex.py              # AnnexSubAgent
│   │
│   ├── models/                       # Pydantic 데이터 모델
│   │   ├── __init__.py
│   │   ├── meeting.py                # MeetingInfo
│   │   ├── toc.py                    # TOCSection, SectionType
│   │   ├── item.py                   # Item, Resolution, Context
│   │   └── annex.py                  # AnnexB, AnnexC1, AnnexC2
│   │
│   ├── prompts/                      # 프롬프트 템플릿
│   │   ├── __init__.py
│   │   ├── metadata_prompt.py
│   │   ├── toc_prompt.py
│   │   └── subsection_prompts/
│   │       └── ...
│   │
│   └── utils/                        # 유틸리티
│       ├── __init__.py
│       ├── docx_converter.py         # python-docx 변환 (하이라이트 마커 보존)
│       ├── markdown.py               # Markdown 파싱
│       ├── tdoc.py                   # TDoc 정규화
│       └── file_io.py                # YAML 파일 I/O
│
├── config/
│   └── settings.yaml                 # 설정 파일
│
└── main.py                           # 실행 진입점
```

---

## Agent 매핑 (명세서 5장)

### section_type → Section Agent 매핑

| section_type | Section Agent | 비고 |
|--------------|---------------|------|
| Maintenance | TechnicalAgent | 기술 논의 |
| Release | TechnicalAgent | 기술 논의 |
| Study | TechnicalAgent | 기술 논의 |
| UE_Features | TechnicalAgent | 기술 논의 |
| LS | IncomingLSAgent | LS 처리 |
| Annex (B, C-1, C-2) | AnnexAgent | 크로스체크 |
| Procedural | - | skip 처리 |
| Annex (기타) | - | skip 처리 |
| unknown | - | Human Review |

### Section Agent → SubSection Agent 매핑

| Section Agent | section_type | SubSection Agent |
|---------------|--------------|------------------|
| TechnicalAgent | Maintenance | MaintenanceSubAgent |
| TechnicalAgent | Release | ReleaseSubAgent |
| TechnicalAgent | Study | StudySubAgent |
| TechnicalAgent | UE_Features | UEFeaturesSubAgent |
| IncomingLSAgent | LS | LSSubAgent |
| AnnexAgent | Annex | AnnexSubAgent |

---

## 데이터 모델 (명세서 3장)

### MeetingInfo

```python
class MeetingInfo(BaseModel):
    meeting_id: str           # RAN1_120
    tsg: str                  # RAN
    wg: str                   # WG1
    wg_code: str              # RAN1
    meeting_number: str       # 120
    version: str              # 1.0.0
    location: str             # Athens, Greece
    start_date: str           # 2025-02-17
    end_date: str             # 2025-02-21
    source: str               # MCC Support
    document_for: str         # Approval
```

### SectionType (7종)

```python
class SectionType(str, Enum):
    PROCEDURAL = "Procedural"
    MAINTENANCE = "Maintenance"
    RELEASE = "Release"
    STUDY = "Study"
    UE_FEATURES = "UE_Features"
    LS = "LS"
    ANNEX = "Annex"
    UNKNOWN = "unknown"
```

### TOCSection

```python
class TOCSection(BaseModel):
    id: str                   # 9.1.1, 8.1v1
    title: str
    depth: int
    parent: Optional[str]
    children: List[str]
    section_type: SectionType
    type_reason: str
    skip: bool
    skip_reason: Optional[str] = None
    virtual: bool = False
```

### Item

```python
class Item(BaseModel):
    id: str                   # RAN1_120_9.1.1_001
    context: ItemContext
    resolution: Resolution

    # 선택 필드
    topic: Optional[Topic] = None
    input: Optional[Input] = None
    session_info: Optional[SessionInfo] = None
    cr_info: Optional[CRInfo] = None
    tr_info: Optional[TRInfo] = None
    ls_in: Optional[LSInInfo] = None
    ls_out: Optional[LSOutInfo] = None

    # 메타데이터
    error: Optional[ErrorInfo] = None
    processing: Optional[ProcessingInfo] = None
    warning: Optional[WarningInfo] = None
```

---

## ParserState (LangGraph)

```python
class ParserState(TypedDict):
    # 입력
    input_path: str
    output_dir: str

    # 전처리 결과 (역할 0)
    markdown_content: str      # 서식 마커 포함 본문
    toc_raw: list[dict]        # python-docx에서 직접 추출한 TOC 구조
    meeting_id: str

    # 역할 1 결과
    meeting_info: Optional[dict]

    # 역할 2 결과
    toc: Optional[list[dict]]  # toc_raw + section_type 판단 결과

    # 역할 3 결과
    section_results: Annotated[list[SectionResult], add]
    annex_results: Annotated[list[dict], add]

    # 역할 4 결과
    validation_result: Optional[dict]

    # 상태 관리
    current_step: str
    errors: Annotated[list[dict], add]
    warnings: Annotated[list[dict], add]
```

---

## 설정 파일

### config/settings.yaml

```yaml
llm:
  provider: "openrouter"
  model: "google/gemini-2.0-flash-001"
  max_tokens: 4096
  temperature: 0
  base_url: "https://openrouter.ai/api/v1"

paths:
  input_base: "data/data_extracted/meetings/RAN1"
  output_base: "output/phase-2/langgraph-parser/results"
  converted_base: "output/phase-2/langgraph-parser/converted"

processing:
  chunk_size: 50000
  parallel_sections: false
```

### 출력 파일 구조 (역할 0)

```
/converted/{meeting_id}/
├── document.md          # 서식 마커 포함 본문 ([text]{.mark} 등)
├── toc_raw.yaml         # python-docx에서 직접 추출한 TOC 구조
└── media/               # 이미지 파일 (선택)
```

**toc_raw.yaml 스키마**:
```yaml
- id: "9.1.1"
  title: "MIMO"
  depth: 3              # Word 스타일에서 결정 (TOC 1 → depth 1)
  page: 14              # 페이지 번호 (참고용)
```

---

## 의존성

**기존 설치됨:**
- langgraph>=1.0.3
- langchain-google-genai>=3.1.0
- langchain>=1.0.8
- python-dotenv>=1.2.1

**추가 필요:**
- pyyaml>=6.0
- **python-docx>=1.1.0** (DOCX 직접 파싱, 하이라이트 마커 보존)

**설치:**
```bash
cd /home/sihyeon/workspace/spec-trace
uv add pyyaml python-docx
```

---

## 완료 조건

1. 모든 디렉토리/파일 생성됨
2. pyyaml 설치 성공
3. `from src.models import MeetingInfo, TOCSection, Item` 성공
4. `from src.state import ParserState` 성공
5. `from src.graph import create_parser_graph` 성공 (빈 그래프라도)
6. 명세서 3장의 모든 필드가 모델에 반영됨

---

## 다음 Step

- **Step-2**: 역할 0 preprocess 노드 구현 + python-docx 변환 테스트

---

**Last Updated**: 2025-12-30
**Status**: ✅ Complete
