"""
LangGraph Studio 호환 그래프 정의

LangGraph Studio에서 시각화하려면 컴파일된 그래프를 export해야 합니다.
이 파일은 Studio에서 직접 import할 수 있는 그래프를 제공합니다.

Usage (LangGraph Studio):
    langgraph dev --config langgraph.json

Usage (Python):
    from src.graph import graph, create_graph
    result = graph.invoke({"docx_path": "path/to/file.docx"})
"""

import sys
from pathlib import Path
from typing import Any, Optional

# LangGraph Studio에서 실행될 때 모듈 경로 설정
SCRIPT_DIR = Path(__file__).parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.workflows.incoming_ls_workflow import IncomingLSState, IncomingLSWorkflow


def create_graph(config: Optional[dict] = None) -> CompiledStateGraph:
    """
    LangGraph Studio 호환 그래프 생성

    Args:
        config: 설정 딕셔너리

    Returns:
        컴파일된 StateGraph
    """
    workflow = IncomingLSWorkflow(config)
    return workflow.app


# LangGraph Studio에서 사용할 기본 그래프 인스턴스
# langgraph.json에서 참조: "./src/graph.py:graph"
graph = create_graph()


# 추가: 그래프 시각화를 위한 헬퍼 함수
def get_graph_visualization() -> str:
    """
    그래프 구조를 Mermaid 다이어그램으로 반환

    Returns:
        Mermaid 다이어그램 문자열
    """
    return """
```mermaid
graph TD
    A[__start__] --> B[parse_document]
    B --> C[extract_meeting_number]
    C --> D[process_section]
    D --> E[generate_output]
    E --> F[__end__]

    subgraph "parse_document"
        B1[Load DOCX] --> B2[Extract paragraphs]
        B2 --> B3[🧠 LLM: Find Incoming LS section]
    end

    subgraph "extract_meeting_number"
        C1[🧠 LLM: Extract meeting number]
    end

    subgraph "process_section (LSAgent)"
        D1[🤖 BoundaryDetector] --> D2[🤖 MetadataExtractor]
        D2 --> D3[🤖 TdocLinker]
        D3 --> D4[🤖 DecisionClassifier]
        D4 --> D5[🤖 SummaryGenerator]
        D5 --> D6[Section Overview]
    end

    subgraph "generate_output"
        E1[SectionOutput → Markdown]
    end
```
"""


def print_graph_ascii():
    """그래프 구조를 ASCII로 출력"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           INCOMING LS WORKFLOW - LANGGRAPH                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌─────────────┐                                            ║
║  │  __start__  │                                            ║
║  └──────┬──────┘                                            ║
║         │                                                    ║
║         ▼                                                    ║
║  ┌─────────────────────┐                                    ║
║  │   parse_document    │  🧠 LLM: Incoming LS 섹션 추출      ║
║  │   (25.03s)          │                                    ║
║  └──────────┬──────────┘                                    ║
║             │                                                ║
║             ▼                                                ║
║  ┌─────────────────────────┐                                ║
║  │ extract_meeting_number  │  🧠 LLM: 미팅 번호 추출         ║
║  │ (1.49s)                 │                                ║
║  └───────────┬─────────────┘                                ║
║              │                                               ║
║              ▼                                               ║
║  ┌─────────────────────────────────────────────────┐        ║
║  │           process_section (LSAgent)             │        ║
║  │           (122.44s)                             │        ║
║  │  ┌────────────────────────────────────────┐    │        ║
║  │  │ 🤖 BoundaryDetector                    │    │        ║
║  │  │    └─→ Issue 경계 탐지                  │    │        ║
║  │  │ 🤖 MetadataExtractor                   │    │        ║
║  │  │    └─→ LS ID, Title, Source WG         │    │        ║
║  │  │ 🤖 TdocLinker                          │    │        ║
║  │  │    └─→ 관련 Tdoc 연결                   │    │        ║
║  │  │ 🤖 DecisionClassifier                  │    │        ║
║  │  │    └─→ Issue Type 분류                  │    │        ║
║  │  │ 🤖 SummaryGenerator                    │    │        ║
║  │  │    └─→ 한국어 요약 생성                  │    │        ║
║  │  └────────────────────────────────────────┘    │        ║
║  └───────────────────┬─────────────────────────────┘        ║
║                      │                                       ║
║                      ▼                                       ║
║  ┌─────────────────────┐                                    ║
║  │   generate_output   │  SectionOutput → Markdown          ║
║  │   (0.00s)           │                                    ║
║  └──────────┬──────────┘                                    ║
║             │                                                ║
║             ▼                                                ║
║  ┌─────────────┐                                            ║
║  │   __end__   │                                            ║
║  └─────────────┘                                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    print_graph_ascii()
    print("\n" + get_graph_visualization())
