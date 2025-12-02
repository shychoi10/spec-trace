# Phase-2 Step-1: LangGraph Multi-Agent System

## Overview

3GPP RAN1 Final Minutes 문서에서 구조화된 Issue를 추출하는 Multi-Agent 시스템.

**Status**: ✅ Incoming LS Processing Complete (RAN1 #119, #120)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IncomingLSWorkflow                       │
│  (LangGraph StateGraph - Linear Pipeline)                   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ SectionOverview│   │ BoundaryDetector│  │ IssueSplitter │
│    Agent      │   │               │   │    Agent      │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ TdocsExtractor│   │ TdocsSelector │   │ MetadataExtractor│
│    Agent      │   │    Agent      │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  TdocLinker   │   │DecisionClassifier│ │SummaryGenerator│
└───────────────┘   └───────────────┘   └───────────────┘
                            │
                            ▼
                   ┌───────────────┐
                   │ IssueFormatter│
                   │    Agent      │
                   └───────────────┘
                            │
                            ▼
                   ┌───────────────┐
                   │  Markdown     │
                   │   Output      │
                   └───────────────┘
```

## Sub-Agents

| Agent | 역할 | Input | Output |
|-------|------|-------|--------|
| **SectionOverviewAgent** | Section 요약 생성 (Korean) | Section content | Overview text, statistics, categories |
| **BoundaryDetectorAgent** | Issue 경계 감지 | Section content | Issue boundaries (start/end indices) |
| **IssueSplitterAgent** | Issue별 텍스트 분할 | Content + boundaries | Individual issue texts |
| **TdocsExtractorAgent** | 전체 Tdoc 목록 추출 | Section content | All Tdoc IDs in section |
| **TdocsSelectorAgent** | Issue별 관련 Tdoc 선택 | Issue text + all Tdocs | Relevant Tdocs per issue |
| **MetadataExtractorAgent** | LS 메타데이터 추출 | Issue text | LS ID, Source WG, Companies |
| **TdocLinkerAgent** | Tdoc 상세 정보 연결 | Tdocs + TdocList XLSX | Tdoc titles, authors, types |
| **DecisionClassifierAgent** | Issue Type 분류 | Issue text + decision | Actionable/Non-action/Reference |
| **SummaryGeneratorAgent** | Issue 요약 생성 (Korean) | Issue text | Korean summary |
| **IssueFormatterAgent** | 최종 마크다운 포맷 | All extracted data | Formatted markdown |

## Project Structure

```
scripts/phase-2/langgraph-system/
├── config/
│   ├── meetings/
│   │   ├── RAN1_119.yaml          # Meeting-specific config
│   │   └── RAN1_120.yaml
│   ├── templates/
│   │   └── incoming_ls_template.md # Output template
│   ├── domain_hints.yaml          # Domain knowledge hints
│   └── settings.yaml              # Global settings
├── src/
│   ├── agents/
│   │   ├── sub_agents/            # 10 specialized sub-agents
│   │   ├── base_agent.py          # Abstract base class
│   │   └── incoming_ls_agent.py   # Main coordinator
│   ├── models/
│   │   ├── enums.py               # IssueType, TdocType enums
│   │   └── issue.py               # Issue dataclass
│   ├── utils/
│   │   ├── document_parser.py     # DOCX parsing
│   │   ├── llm_manager.py         # OpenRouter LLM client
│   │   └── workflow_tracer.py     # Execution tracing
│   ├── workflows/
│   │   └── incoming_ls_workflow.py # LangGraph workflow
│   ├── config_loader.py           # YAML config loader
│   └── graph.py                   # Graph composition
├── main.py                        # CLI entry point
├── main_with_trace.py             # With detailed tracing
└── langgraph.json                 # LangGraph Studio config
```

## Configuration

### Meeting Config (`config/meetings/RAN1_120.yaml`)

```yaml
meeting:
  id: "RAN1_120"
  number: 120
  working_group: "RAN1"
  date_range: "2025-01-20 ~ 2025-01-24"
  location: "Athens, Greece"

input:
  final_minutes: "data/data_extracted/meetings/RAN1/TSGR1_120/Report/Final_Minutes_120-e.docx"
  tdoc_list: "data/data_extracted/meetings/RAN1/TSGR1_120/TdocList/TdocsByAgenda120.xlsx"

output:
  directory: "output"
  filename_pattern: "{meeting_id}_incoming_ls.md"

sections:
  incoming_ls:
    enabled: true
    section_title: "Incoming liaison statements"
```

### Global Settings (`config/settings.yaml`)

```yaml
llm:
  provider: "openrouter"
  model: "openai/gpt-4o"
  temperature: 0.2
  max_tokens: 4000

processing:
  chunk_size: 12000
  overlap: 2000
  max_retries: 3
```

## Usage

### Basic Execution

```bash
cd scripts/phase-2/langgraph-system

# Process specific meeting
python main.py --meeting RAN1_120

# Process with detailed tracing
python main_with_trace.py --meeting RAN1_120
```

### Output

Results are saved to `output/{meeting_id}_incoming_ls.md`:

```markdown
# Section 5: Incoming Liaison Statements (RAN1 #120)

## Section Overview
이번 RAN1 #120 회의에서는 RAN2와 RAN3로부터 총 32개의 LS가 접수되었습니다...

**Statistics:**
- Total Primary LS Items: 20
- CC-only Items: 12
- Source Working Groups: ETSI ISG ISAC, RAN2, RAN3, RAN4, SA2

---

### Issue 1: LS response on waveform determination...

**Origin**
- Type: `LS` (Section 5 — Incoming LS)
- LS ID: R1-2500007
- Source WG: RAN2

**Summary**
RAN2는 R1-2409301에 대한 답변으로...

**Relevant Tdocs**
- R1-2500328 — *Discussion on...* (vivo) — `discussion`

**Decision**
No further action necessary from RAN1.

**Issue Type**
- Non-action Issue

---
```

## Results

### RAN1 #120

| Metric | Value |
|--------|-------|
| Total Primary Issues | 20 |
| CC-only Items | 12 |
| Source WGs | 5 (RAN2, RAN3, RAN4, SA2, ETSI ISG ISAC) |
| Processing Time | ~3 min |
| LLM Calls | ~200 |

### RAN1 #119

| Metric | Value |
|--------|-------|
| Total Primary Issues | 18 |
| CC-only Items | 10 |
| Processing Time | ~2.5 min |

## Design Principles

### 1. True Agentic AI (No Regex)

모든 텍스트 분석은 LLM이 수행. Regex/하드코딩 규칙 사용 금지.

```python
# ❌ Wrong
def extract_ls_id(text):
    return re.findall(r"R1-\d{7}", text)

# ✅ Correct
def extract_ls_id(text):
    prompt = "Extract LS ID (R1-XXXXXXX format) from this text..."
    return self.llm.generate(prompt)
```

### 2. Content-Based Naming (No Section Numbers)

파일명, 클래스명에 Section 번호 사용 금지. 콘텐츠 유형으로 명명.

```python
# ❌ Wrong
class Section5Agent:
    output_file = "section5_output.md"

# ✅ Correct
class IncomingLSAgent:
    output_file = "incoming_ls_output.md"
```

### 3. LangGraph StateGraph

Linear pipeline with typed state management.

```python
class IncomingLSState(TypedDict):
    content: str
    boundaries: list[dict]
    issues: list[Issue]
    output: str

workflow = StateGraph(IncomingLSState)
workflow.add_node("detect_boundaries", boundary_detector)
workflow.add_node("split_issues", issue_splitter)
workflow.add_edge("detect_boundaries", "split_issues")
```

## Known Limitations

1. **Single Section Only**: 현재 Incoming LS (Section 5)만 지원
2. **Meeting-Specific Config**: 각 미팅마다 config 파일 필요
3. **LLM Dependency**: OpenRouter API 필요 (비용 발생)

## Next Steps

- [ ] Multi-Section Support (Section 6-9, Annex)
- [ ] Meta Orchestrator (Content-based agent selection)
- [ ] Ground Truth Validation Pipeline
- [ ] Cost Optimization (Caching, Smaller models)

## Related Files

- **Main Script**: [main.py](../../scripts/phase-2/langgraph-system/main.py)
- **Workflow**: [incoming_ls_workflow.py](../../scripts/phase-2/langgraph-system/src/workflows/incoming_ls_workflow.py)
- **Sub-Agents**: [src/agents/sub_agents/](../../scripts/phase-2/langgraph-system/src/agents/sub_agents/)

---

**Last Updated**: 2025-12-02
