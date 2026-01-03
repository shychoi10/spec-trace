"""
역할 4: 결과 취합 + extraction_result.yaml 생성

명세서 4.4장 참조:
- Step-6: 결과 취합 + extraction_result.yaml 저장
- Step-7: 크로스체크 검증 (Annex B/C vs 본문)
"""

from datetime import datetime
from pathlib import Path

from ..state import ParserState
from ..utils.file_io import save_yaml


def _count_by_section_type(section_results: list) -> dict[str, int]:
    """section_type별 Item 카운트"""
    counts: dict[str, int] = {}
    for result in section_results:
        section_type = result.get("section_type", "unknown")
        item_count = len(result.get("items", []))
        counts[section_type] = counts.get(section_type, 0) + item_count
    return counts


def _count_by_status(section_results: list) -> dict[str, int]:
    """status별 섹션 카운트"""
    counts: dict[str, int] = {}
    for result in section_results:
        status = result.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def validation_node(state: ParserState) -> dict:
    """역할 4: 결과 취합 + extraction_result.yaml 생성

    명세서 4.4.3 참조:
    - 역할 1~3 출력물 수집
    - 통계 집계
    - extraction_result.yaml 생성

    크로스체크는 Step-7에서 구현 예정

    Args:
        state: ParserState

    Returns:
        업데이트된 상태 (current_step, validation_result)
    """
    meeting_info = state.get("meeting_info", {}) or {}
    toc = state.get("toc", []) or []
    section_results = state.get("section_results", []) or []
    annex_results = state.get("annex_results", []) or []
    output_dir = Path(state.get("output_dir", ""))
    errors = state.get("errors", []) or []
    warnings = state.get("warnings", []) or []

    # 통계 집계
    total_items = sum(len(r.get("items", [])) for r in section_results)
    total_sections = len(section_results)
    total_toc_entries = len(toc)
    total_annexes = len(annex_results)
    total_annex_entries = sum(len(a.get("entries", [])) for a in annex_results)

    # extraction_result.yaml 생성
    result = {
        "metadata": {
            "meeting_id": meeting_info.get("meeting_id", ""),
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "source_document": meeting_info.get("document_title", ""),
        },
        "statistics": {
            "toc": {
                "total_entries": total_toc_entries,
            },
            "sections": {
                "total_sections": total_sections,
                "total_items": total_items,
                "by_section_type": _count_by_section_type(section_results),
                "by_status": _count_by_status(section_results),
            },
            "annexes": {
                "total_annexes": total_annexes,
                "total_entries": total_annex_entries,
            },
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "validation": {
            "status": "pending",  # Step-7에서 구현
            "crosscheck": None,   # Step-7에서 구현
        },
    }

    # extraction_result.yaml 저장
    save_yaml(result, output_dir / "extraction_result.yaml")

    return {
        "current_step": "completed",
        "validation_result": result,
    }
