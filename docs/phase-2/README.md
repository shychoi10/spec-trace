# Phase-2: RAN1 Graph DB Construction

## Goal

3GPP RAN1 문서들의 관계를 Graph DB로 저장하여 검색 및 분석 가능하게 만들기.

## Steps Overview

```
Phase-2: Graph DB Construction
├── Step-1: LangGraph Multi-Agent System     [✅ Complete]
│   └── Incoming LS Processing (15 meetings)
├── Step-2: Multi-Section Expansion          [🔄 In Progress]
│   └── Maintenance Section Processing (3 sections)
├── Step-3: Graph DB Schema Design           [⏳ Planned]
├── Step-4: Data Population                  [⏳ Planned]
└── Step-5: Query & Analysis Interface       [⏳ Planned]
```

## Current Focus: Step-2 Multi-Section Expansion

**범용 Multi-Section 처리 아키텍처** - Meta Agent + Generic Workflow

- **Status**: 🔄 In Progress
- **Target**: Maintenance Sections (3개: Rel-18, Pre-Rel-18 NR, Pre-Rel-18 E-UTRA)
- **Architecture**: MetaSectionAgent → Generic Workflow 라우팅
- **Documentation**: [step2_multi-section-expansion.md](step2_multi-section-expansion.md)

### Step-1 (Complete): Incoming LS Processing

- **Status**: ✅ Complete
- **Tested**: RAN1 #110-121 (15개 미팅)
- **LLM**: Google Gemini API (gemini-2.5-flash)
- **Documentation**: [step1_langgraph-system.md](step1_langgraph-system.md)

### Architecture

```
Input (Final Minutes DOCX)
    ↓
[Document Parser] → Section extraction
    ↓
[IncomingLSWorkflow] → 10 Sub-agents pipeline
    ↓
[Structured Output] → Markdown with Issues
    ↓
[Future: Graph DB] → Neo4j/similar
```

### Key Design Principles

1. **True Agentic AI**: 모든 분석은 LLM이 수행 (No Regex)
2. **Content-Based Naming**: Section 번호가 아닌 콘텐츠 유형으로 명명
3. **Meeting-Agnostic**: 설정만 바꾸면 다른 미팅에도 적용 가능

## Tech Stack

- **Framework**: LangGraph (Agentic AI workflow)
- **LLM**: Google Gemini API (gemini-2.5-flash) - 직접 호출
- **Language**: Python 3.11
- **Package Manager**: uv

## Directory Structure

```
scripts/phase-2/langgraph-system/    # Main implementation
docs/phase-2/                        # Documentation
output/                              # Generated outputs (gitignored)
logs/                                # Execution logs (gitignored)
```

## Quick Start

```bash
# Setup (프로젝트 루트에서)
# .env 파일에 GOOGLE_API_KEY 설정

# Run
cd scripts/phase-2/langgraph-system
python main.py --meeting RAN1_121

# Batch run (모든 미팅)
python batch_run.py
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [step1_langgraph-system.md](step1_langgraph-system.md) | Step-1: Incoming LS Processing 상세 가이드 |
| [step2_multi-section-expansion.md](step2_multi-section-expansion.md) | Step-2: Multi-Section Expansion 상세 가이드 |

---

**Last Updated**: 2025-12-03
