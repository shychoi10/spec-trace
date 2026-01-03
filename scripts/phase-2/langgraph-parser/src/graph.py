"""
LangGraph 그래프 정의

명세서 2장 참조: 파이프라인 흐름도
역할 0 → 역할 1 → 역할 2 → 역할 3 → 역할 4
"""

from langgraph.graph import StateGraph, END

from .state import ParserState
from .pipeline import (
    preprocess_node,
    metadata_node,
    toc_node,
    sections_node,
    validation_node,
)


def create_parser_graph() -> StateGraph:
    """파서 그래프 생성

    Returns:
        컴파일된 LangGraph 그래프

    파이프라인 흐름:
        역할 0 (preprocess) → 역할 1 (metadata) → 역할 2 (toc)
            → 역할 3 (sections) → 역할 4 (validation) → END
    """
    # 그래프 빌더 생성
    builder = StateGraph(ParserState)

    # 노드 추가
    builder.add_node("preprocess", preprocess_node)
    builder.add_node("metadata", metadata_node)
    builder.add_node("toc", toc_node)
    builder.add_node("sections", sections_node)
    builder.add_node("validation", validation_node)

    # 엣지 추가 (순차 실행)
    builder.set_entry_point("preprocess")
    builder.add_edge("preprocess", "metadata")
    builder.add_edge("metadata", "toc")
    builder.add_edge("toc", "sections")
    builder.add_edge("sections", "validation")
    builder.add_edge("validation", END)

    # 그래프 컴파일
    graph = builder.compile()

    return graph


def get_graph_visualization() -> str:
    """그래프 시각화 (Mermaid 형식)

    Returns:
        Mermaid 다이어그램 문자열
    """
    return """
graph TD
    A[Start] --> B[역할 0: preprocess]
    B --> C[역할 1: metadata]
    C --> D[역할 2: toc]
    D --> E[역할 3: sections]
    E --> F[역할 4: validation]
    F --> G[End]

    subgraph "역할 3: sections (병렬)"
        E --> E1[TechnicalAgent]
        E --> E2[IncomingLSAgent]
        E --> E3[AnnexAgent]
        E1 --> E1a[SubSection Agents]
        E2 --> E2a[LSSubAgent]
        E3 --> E3a[AnnexSubAgent]
    end
"""
