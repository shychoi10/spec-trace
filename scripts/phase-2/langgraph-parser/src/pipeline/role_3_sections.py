"""
역할 3: 섹션 처리 (Orchestrator)

명세서 4.3장 참조:
- Section Agent를 통해 각 섹션 병렬 처리
- Depth 1 섹션별로 Section Agent 할당
- skip 섹션 제외
- unknown 섹션은 2차 판단 (4.3.6)
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ..agents.section_agents.technical import TechnicalAgent
from ..agents.section_agents.incoming_ls import IncomingLSAgent
from ..agents.section_agents.annex import AnnexAgent
from ..state import ParserState, SectionResult, AnnexResult
from ..utils.file_io import save_yaml, save_items_yaml
from ..utils.markdown import extract_section, find_leaf_sections, get_next_section


# Section Agent 매핑 (Spec 5.1)
SECTION_AGENT_MAP = {
    "Maintenance": TechnicalAgent,
    "Release": TechnicalAgent,
    "Study": TechnicalAgent,
    "UE_Features": TechnicalAgent,
    "LS": IncomingLSAgent,
    "Annex": AnnexAgent,
}


def _get_depth1_sections(toc: list[dict]) -> list[dict]:
    """Depth 1 섹션 필터링 (skip 제외)

    Args:
        toc: 전체 TOC 목록

    Returns:
        skip=False인 Depth 1 섹션 목록
    """
    return [
        section for section in toc
        if section.get("depth") == 1 and not section.get("skip", False)
    ]


def _get_section_agent(section_type: str):
    """section_type에 따른 Section Agent 반환

    Args:
        section_type: 섹션 타입

    Returns:
        Section Agent 인스턴스
    """
    agent_class = SECTION_AGENT_MAP.get(section_type)
    if agent_class:
        return agent_class()

    # unknown은 TechnicalAgent 기본 할당 (Spec 4.3.6)
    return TechnicalAgent()


def _find_leaves_for_section(
    toc: list[dict],
    section_id: str,
) -> list[dict]:
    """특정 섹션의 Leaf 찾기 (children: [])

    Args:
        toc: 전체 TOC 목록
        section_id: Depth 1 섹션 ID

    Returns:
        해당 섹션의 Leaf 목록
    """
    leaves = []

    for i, section in enumerate(toc):
        # 해당 섹션 또는 하위 섹션인지 확인
        sid = str(section.get("id", ""))
        if sid == section_id or sid.startswith(f"{section_id}.") or sid.startswith(f"{section_id}v"):
            # Leaf인지 확인 (children이 빈 리스트)
            children = section.get("children", [])
            if not children and not section.get("skip", False):
                leaves.append({
                    **section,
                    "_toc_index": i,  # 다음 섹션 찾기용
                })

    return leaves


def _build_id_to_index_map(toc: list[dict]) -> dict[str, int]:
    """섹션 ID → 인덱스 매핑 생성"""
    return {str(section.get("id", "")): i for i, section in enumerate(toc)}


def _process_section(
    section: dict,
    toc: list[dict],
    markdown_content: str,
    meeting_info: dict,
    output_dir: Path,
    id_to_index: dict[str, int],
) -> SectionResult:
    """개별 섹션 처리

    Args:
        section: Depth 1 섹션 정보
        toc: 전체 TOC
        markdown_content: Markdown 내용
        meeting_info: 회의 메타데이터
        output_dir: 출력 디렉토리
        id_to_index: ID → 인덱스 매핑

    Returns:
        SectionResult
    """
    section_id = str(section.get("id", ""))
    section_type = section.get("section_type", "unknown")
    title = section.get("title", "")

    # Annex는 별도 처리
    if section_type == "Annex":
        return SectionResult(
            section_id=section_id,
            title=title,
            section_type=section_type,
            status="skipped",  # AnnexAgent에서 별도 처리
            leaves=[],
            items=[],
        )

    # Section Agent 가져오기
    agent = _get_section_agent(section_type)

    # Leaf 섹션 찾기
    leaves = _find_leaves_for_section(toc, section_id)

    if not leaves:
        return SectionResult(
            section_id=section_id,
            title=title,
            section_type=section_type,
            status="no_leaves",
            leaves=[],
            items=[],
        )

    # Depth 1 섹션 전체 본문 추출 (Section Agent에 전달)
    # 다음 Depth 1 섹션 찾기
    idx = id_to_index.get(section_id, 0)
    next_depth1 = None
    for i in range(idx + 1, len(toc)):
        if toc[i].get("depth") == 1:
            next_depth1 = toc[i]
            break

    # Spec 4.3.1: page 힌트로 탐색 범위 축소
    section_page = section.get("page")

    section_content = extract_section(
        markdown_content=markdown_content,
        section_id=section_id,
        section_title=title,
        next_section_id=str(next_depth1.get("id", "")) if next_depth1 else None,
        next_section_title=next_depth1.get("title", "") if next_depth1 else None,
        page=section_page,
    )

    if not section_content:
        return SectionResult(
            section_id=section_id,
            title=title,
            section_type=section_type,
            status="content_not_found",
            leaves=[{"leaf_id": l.get("id"), "status": "skipped"} for l in leaves],
            items=[],
        )

    # Section Agent로 처리 (leaves를 전달하여 SubSection Agent 호출 위임)
    try:
        result = agent.process(
            section_id=section_id,
            section_content=section_content,
            toc_info={
                "title": title,
                "section_type": section_type,
                "leaves": leaves,
                "meeting_id": meeting_info.get("meeting_id", ""),
            },
        )

        all_items = result.get("items", [])
        leaf_results = result.get("leaves", [])

    except Exception as e:
        return SectionResult(
            section_id=section_id,
            title=title,
            section_type=section_type,
            status="failed",
            leaves=[],
            items=[],
        )

    # 섹션 결과 저장
    section_dir = output_dir / "sections" / section_id
    section_dir.mkdir(parents=True, exist_ok=True)

    # _index.yaml 저장
    index_data = {
        "section_id": section_id,
        "title": title,
        "section_type": section_type,
        "agent": type(agent).__name__,
        "leaves": leaf_results,
        "statistics": {
            "total_leaves": len(leaves),
            "total_items": len(all_items),
            "by_status": _count_by_status(all_items),
        },
        "_processing": {
            "generated_at": datetime.now().isoformat(),
            "status": "completed" if all_items else "no_items",
        },
    }
    save_yaml(index_data, section_dir / "_index.yaml")

    # 개별 Leaf YAML 저장 (Item 간 빈 줄 추가로 가독성 향상)
    for leaf in leaf_results:
        leaf_id = leaf.get("leaf_id", "")
        leaf_items = [item for item in all_items if item.get("context", {}).get("leaf_id") == leaf_id]
        if leaf_items:
            save_items_yaml(leaf_items, section_dir / f"{leaf_id}.yaml")

    return SectionResult(
        section_id=section_id,
        title=title,
        section_type=section_type,
        status="completed" if all_items else "no_items",
        leaves=leaf_results,
        items=all_items,
    )


def _count_by_status(items: list[dict]) -> dict[str, int]:
    """Item들의 status별 카운트"""
    counts: dict[str, int] = {}
    for item in items:
        status = item.get("resolution", {}).get("status", "Unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _process_annexes(
    toc: list[dict],
    markdown_content: str,
    meeting_info: dict,
    output_dir: Path,
) -> list[AnnexResult]:
    """Annex 처리 (B, C-1, C-2만)

    Args:
        toc: 전체 TOC
        markdown_content: Markdown 내용
        meeting_info: 회의 메타데이터
        output_dir: 출력 디렉토리

    Returns:
        AnnexResult 목록
    """
    annex_results = []
    annex_agent = AnnexAgent()

    # Annex 섹션 찾기
    for section in toc:
        if section.get("section_type") != "Annex":
            continue
        if section.get("skip", False):
            continue

        title = section.get("title", "")

        # Annex B, C-1, C-2만 처리
        annex_id = None
        if "Annex B" in title or "List of CRs" in title:
            annex_id = "annex_b"
        elif "C-1" in title or "Outgoing LS" in title:
            annex_id = "annex_c1"
        elif "C-2" in title or "Incoming LS" in title:
            annex_id = "annex_c2"

        if not annex_id:
            continue

        # Annex 내용 추출
        section_id = str(section.get("id", ""))
        section_title = section.get("title", "")

        # 다음 섹션 찾기
        idx = next((i for i, s in enumerate(toc) if str(s.get("id")) == section_id), -1)
        next_section = toc[idx + 1] if idx >= 0 and idx + 1 < len(toc) else None

        # Spec 4.3.1: page 힌트로 탐색 범위 축소
        section_page = section.get("page")

        content = extract_section(
            markdown_content=markdown_content,
            section_id=section_id,
            section_title=section_title,
            next_section_id=str(next_section.get("id", "")) if next_section else None,
            next_section_title=next_section.get("title", "") if next_section else None,
            page=section_page,
        )

        # AnnexAgent로 처리
        try:
            result = annex_agent.process(
                section_id=section_id,
                section_content=content,
                toc_info={
                    "annex_id": annex_id,
                    "title": title,
                    "meeting_info": meeting_info,
                },
            )

            entries = result.get("entries", [])

            # annexes 디렉토리에 저장
            annexes_dir = output_dir / "annexes"
            annexes_dir.mkdir(parents=True, exist_ok=True)
            save_yaml({
                "annex_id": annex_id,
                "title": title,
                "entries": entries,
                "_processing": {
                    "generated_at": datetime.now().isoformat(),
                    "status": "completed",
                },
            }, annexes_dir / f"{annex_id}.yaml")

            annex_results.append(AnnexResult(
                annex_id=annex_id,
                title=title,
                entries=entries,
                status="completed",
            ))
        except Exception as e:
            annex_results.append(AnnexResult(
                annex_id=annex_id,
                title=title,
                entries=[],
                status="failed",
            ))

    return annex_results


def sections_node(state: ParserState) -> dict:
    """섹션 처리 노드 (Orchestrator)

    명세서 4.3장 참조:
    - toc.yaml에서 skip=False인 Depth 1 섹션 추출
    - section_type에 따라 Section Agent 할당
    - 각 Leaf에 대해 SubSection Agent 호출
    - sections/*.yaml, annexes/*.yaml 저장

    Args:
        state: ParserState

    Returns:
        업데이트된 상태
    """
    errors = []
    warnings = []

    toc = state.get("toc", [])
    markdown_content = state.get("markdown_content", "")
    meeting_info = state.get("meeting_info", {})
    output_dir = Path(state.get("output_dir", ""))

    if not toc:
        errors.append({
            "role": "role_3",
            "section_id": None,
            "error_type": "toc_missing",
            "error_message": "TOC가 비어있습니다",
            "timestamp": datetime.now().isoformat(),
        })
        return {
            "current_step": "role_3_failed",
            "errors": errors,
        }

    # ID → 인덱스 매핑 생성
    id_to_index = _build_id_to_index_map(toc)

    # Depth 1 섹션 추출 (skip 제외)
    depth1_sections = _get_depth1_sections(toc)

    if not depth1_sections:
        warnings.append({
            "role": "role_3",
            "section_id": None,
            "warning_type": "no_sections",
            "message": "처리할 Depth 1 섹션이 없습니다",
        })
        return {
            "current_step": "role_3_completed",
            "section_results": [],
            "annex_results": [],
            "warnings": warnings,
        }

    # 섹션별 처리 (현재는 순차, 향후 병렬화 가능)
    section_results = []
    for section in depth1_sections:
        section_type = section.get("section_type", "unknown")

        # Annex는 별도 처리
        if section_type == "Annex":
            continue

        try:
            result = _process_section(
                section=section,
                toc=toc,
                markdown_content=markdown_content,
                meeting_info=meeting_info,
                output_dir=output_dir,
                id_to_index=id_to_index,
            )
            section_results.append(result)
        except Exception as e:
            section_id = str(section.get("id", ""))
            errors.append({
                "role": "role_3",
                "section_id": section_id,
                "error_type": "section_processing_failed",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            section_results.append(SectionResult(
                section_id=section_id,
                title=section.get("title", ""),
                section_type=section.get("section_type", ""),
                status="failed",
                leaves=[],
                items=[],
            ))

    # Annex 처리
    annex_results = _process_annexes(
        toc=toc,
        markdown_content=markdown_content,
        meeting_info=meeting_info,
        output_dir=output_dir,
    )

    # 통계 로깅
    total_items = sum(len(r.get("items", [])) for r in section_results)
    total_leaves = sum(len(r.get("leaves", [])) for r in section_results)

    if total_items == 0:
        warnings.append({
            "role": "role_3",
            "section_id": None,
            "warning_type": "no_items_extracted",
            "message": f"추출된 Item이 없습니다 (섹션 {len(section_results)}개, Leaf {total_leaves}개 처리)",
        })

    return {
        "current_step": "role_3_completed",
        "section_results": section_results,
        "annex_results": annex_results,
        "errors": errors if errors else [],
        "warnings": warnings if warnings else [],
    }
