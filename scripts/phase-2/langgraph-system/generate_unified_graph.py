#!/usr/bin/env python3
"""
통합 LangGraph Orchestrator 시각화 생성 스크립트

생성물:
1. unified_orchestrator_graph.png - PNG 이미지
2. unified_orchestrator_graph.md - Mermaid 다이어그램
"""

import sys
from pathlib import Path

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "phase-2" / "langgraph-system"))

from src.workflows.unified_orchestrator import UnifiedOrchestrator

OUTPUT_DIR = PROJECT_ROOT / "output" / "phase-2" / "langgraph-system"


def main():
    """통합 Orchestrator 그래프 시각화 생성"""
    print("=" * 60)
    print("통합 LangGraph Orchestrator 시각화 생성")
    print("=" * 60)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Orchestrator 인스턴스 생성 (시각화만 목적이므로 설정 최소화)
    print("\n[1/3] UnifiedOrchestrator 인스턴스 생성...")
    orchestrator = UnifiedOrchestrator(
        config={
            "output_dir": str(OUTPUT_DIR),
            "llm": {"model": "gemini-2.0-flash"},
        }
    )

    # PNG 그래프 생성
    print("[2/3] PNG 그래프 생성...")
    png_path = OUTPUT_DIR / "unified_orchestrator_graph.png"
    try:
        png_data = orchestrator.get_graph_visualization()
        if png_data:
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"  ✅ PNG 저장: {png_path}")
            print(f"  📏 크기: {len(png_data):,} bytes")
        else:
            print("  ⚠️ PNG 생성 실패 (graphviz 필요)")
    except Exception as e:
        print(f"  ❌ PNG 생성 오류: {e}")

    # Mermaid 다이어그램 생성
    print("[3/3] Mermaid 다이어그램 생성...")
    mermaid_path = OUTPUT_DIR / "unified_orchestrator_graph.md"
    try:
        mermaid_code = orchestrator.get_mermaid_code()
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write("# Unified LangGraph Orchestrator\n\n")
            f.write("## 아키텍처 개요\n\n")
            f.write("통합 Orchestrator는 다음과 같은 흐름으로 동작합니다:\n\n")
            f.write("1. **parse_all_sections**: DOCX에서 모든 Heading 1 섹션 추출\n")
            f.write("2. **classify_sections**: MetaSectionAgent가 각 섹션 타입 분류\n")
            f.write("3. **select_next_section**: 처리할 다음 섹션 선택\n")
            f.write("4. **조건부 라우팅**: 섹션 타입에 따라 적절한 워크플로우로 분기\n")
            f.write("   - `incoming_ls` → IncomingLSWorkflow\n")
            f.write("   - `maintenance` → MaintenanceWorkflow\n")
            f.write("   - `other` → skip_section\n")
            f.write("5. **aggregate_outputs**: 모든 처리 결과 집계\n")
            f.write("6. **generate_summary**: 최종 요약 리포트 생성\n\n")
            f.write("## LangGraph 다이어그램\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n\n")
            f.write("## 노드 설명\n\n")
            f.write("| 노드 | 역할 | 출력 |\n")
            f.write("|------|------|------|\n")
            f.write("| parse_all_sections | DOCX 파싱 | 모든 Heading 1 섹션 |\n")
            f.write("| classify_sections | LLM 기반 섹션 분류 | SectionClassification[] |\n")
            f.write("| select_next_section | 다음 처리 대상 선택 | current_section |\n")
            f.write("| process_incoming_ls | LS 워크플로우 실행 | IncomingLSOutput |\n")
            f.write("| process_maintenance | Maintenance 워크플로우 실행 | MaintenanceOutput |\n")
            f.write("| skip_section | 지원하지 않는 섹션 스킵 | - |\n")
            f.write("| aggregate_outputs | 결과 집계 | all_outputs[] |\n")
            f.write("| generate_summary | 최종 리포트 생성 | summary.md |\n")
        print(f"  ✅ Mermaid 저장: {mermaid_path}")
    except Exception as e:
        print(f"  ❌ Mermaid 생성 오류: {e}")

    print("\n" + "=" * 60)
    print("시각화 생성 완료!")
    print("=" * 60)

    # ASCII 다이어그램 출력
    print("\n📊 통합 Orchestrator 구조:\n")
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │                    UnifiedOrchestrator                          │
    │                    (LangGraph StateGraph)                       │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  parse_all_sections   │
                        │  (DOCX → Sections)    │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  classify_sections    │
                        │  (MetaSectionAgent)   │
                        │  [LLM 기반 분류]       │
                        └───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      select_next_section      │
                    │    (다음 처리 대상 선택)       │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┬───────────────┐
                    │               │               │               │
                    ▼               ▼               ▼               ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────┐      │
        │process_       │ │process_       │ │skip_section   │      │
        │incoming_ls    │ │maintenance    │ │(other)        │      │
        │               │ │               │ │               │      │
        │[IncomingLS    │ │[Maintenance   │ │               │      │
        │ Workflow]     │ │ Workflow]     │ │               │      │
        └───────────────┘ └───────────────┘ └───────────────┘      │
                │               │               │                   │
                └───────────────┴───────────────┘                   │
                                │                                   │
                                ▼                                   │
                        ┌───────────────┐                           │
                        │ (loop back to │ ◄─────────────────────────┘
                        │  select_next) │     (more sections)
                        └───────────────┘
                                │
                                │ (done)
                                ▼
                    ┌───────────────────────┐
                    │   aggregate_outputs   │
                    │   (결과 집계)          │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   generate_summary    │
                    │   (최종 리포트)        │
                    └───────────────────────┘
                                │
                                ▼
                            __end__
    """)


if __name__ == "__main__":
    main()
