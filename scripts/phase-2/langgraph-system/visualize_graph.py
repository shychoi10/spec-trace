"""
LangGraph 워크플로우 시각화 스크립트

사용법:
    python visualize_graph.py [--validated]

    --validated: ValidatedIncomingLSWorkflow 사용 (기본: IncomingLSWorkflow)
"""

import sys
sys.path.insert(0, "/home/sihyeon/workspace/spec-trace/scripts/phase-2/langgraph-system")

from pathlib import Path


def visualize_basic_workflow():
    """기본 워크플로우 (검증 없음) 시각화"""
    from src.workflows.incoming_ls_workflow import IncomingLSWorkflow

    workflow = IncomingLSWorkflow()
    graph = workflow.app

    print("=" * 60)
    print("IncomingLSWorkflow Graph Structure")
    print("=" * 60)

    # 그래프 정보 출력
    print("\n📊 Graph Info:")
    print(f"  - Type: {type(graph).__name__}")

    # Mermaid 다이어그램 생성
    try:
        mermaid = graph.get_graph().draw_mermaid()
        print("\n📈 Mermaid Diagram:")
        print("-" * 40)
        print(mermaid)
        print("-" * 40)

        # 파일로 저장
        output_path = Path(__file__).parent / "graph_basic.mermaid"
        with open(output_path, "w") as f:
            f.write(mermaid)
        print(f"\n✅ Saved to: {output_path}")

    except Exception as e:
        print(f"⚠️ Mermaid generation failed: {e}")

    # PNG 이미지 생성 시도
    try:
        png_path = Path(__file__).parent / "graph_basic.png"
        png_data = graph.get_graph().draw_mermaid_png()
        with open(png_path, "wb") as f:
            f.write(png_data)
        print(f"✅ PNG saved to: {png_path}")
    except Exception as e:
        print(f"⚠️ PNG generation failed (requires playwright): {e}")


def visualize_validated_workflow():
    """검증 포함 워크플로우 시각화"""
    from src.workflows.validated_incoming_ls_workflow import ValidatedIncomingLSWorkflow

    workflow = ValidatedIncomingLSWorkflow()
    graph = workflow.app

    print("=" * 60)
    print("ValidatedIncomingLSWorkflow Graph Structure")
    print("=" * 60)

    # 그래프 정보 출력
    print("\n📊 Graph Info:")
    print(f"  - Type: {type(graph).__name__}")

    # Mermaid 다이어그램 생성
    try:
        mermaid = graph.get_graph().draw_mermaid()
        print("\n📈 Mermaid Diagram:")
        print("-" * 40)
        print(mermaid)
        print("-" * 40)

        # 파일로 저장
        output_path = Path(__file__).parent / "graph_validated.mermaid"
        with open(output_path, "w") as f:
            f.write(mermaid)
        print(f"\n✅ Saved to: {output_path}")

    except Exception as e:
        print(f"⚠️ Mermaid generation failed: {e}")

    # PNG 이미지 생성 시도
    try:
        png_path = Path(__file__).parent / "graph_validated.png"
        png_data = graph.get_graph().draw_mermaid_png()
        with open(png_path, "wb") as f:
            f.write(png_data)
        print(f"✅ PNG saved to: {png_path}")
    except Exception as e:
        print(f"⚠️ PNG generation failed (requires playwright): {e}")


def print_manual_diagram():
    """수동으로 그래프 구조 출력"""
    print("\n" + "=" * 60)
    print("📐 Manual Graph Diagrams")
    print("=" * 60)

    print("\n### 1. IncomingLSWorkflow (Basic)")
    print("""
┌─────────────────┐
│   START         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ parse_document  │  DOCX → Incoming LS 섹션 추출 (LLM)
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ extract_meeting_number  │  미팅 번호 추출 (LLM)
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ process_section │  LSAgent로 Issue 처리
│                 │  ├─ BoundaryDetector
│                 │  ├─ MetadataExtractor
│                 │  ├─ TdocLinker
│                 │  ├─ SummaryGenerator
│                 │  └─ OverviewGenerator
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ generate_output │  Markdown 출력 생성
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      END        │
└─────────────────┘
""")

    print("\n### 2. ValidatedIncomingLSWorkflow (With Validation Loop)")
    print("""
┌─────────────────┐
│     START       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ parse_document  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ validate_parse  │────▶│ (retry if fail) │
└────────┬────────┘     └─────────────────┘
         │ (pass)
         ▼
┌─────────────────────────┐
│ extract_meeting_number  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ process_section │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐     ┌─────────────────┐
│ validate_processing  │────▶│ (retry if fail) │
└────────┬─────────────┘     └─────────────────┘
         │ (pass)
         ▼
┌─────────────────┐
│ generate_output │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ final_validation │  원본 DOCX vs 출력 비교
│                  │  ├─ Count Match
│                  │  ├─ ID Match
│                  │  ├─ Field Completeness
│                  │  └─ Content Quality
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│      END        │
└─────────────────┘
""")


if __name__ == "__main__":
    # 수동 다이어그램 항상 출력
    print_manual_diagram()

    # 실제 그래프 시각화
    if "--validated" in sys.argv:
        visualize_validated_workflow()
    else:
        visualize_basic_workflow()

    print("\n" + "=" * 60)
    print("💡 Tips:")
    print("  - Mermaid 파일을 https://mermaid.live 에서 확인 가능")
    print("  - PNG 생성은 playwright 설치 필요: pip install playwright")
    print("=" * 60)
