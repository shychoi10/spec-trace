"""
Unified LangGraph Orchestrator - 통합 Multi-Section 파이프라인

🚨 제1 원칙 (First Principles) 준수:
1. True Agentic AI: MetaSectionAgent가 LLM으로 Section 분류
2. Content-based Naming: Section 번호 없음
3. General Design: 동적 워크플로우 라우팅 (Conditional Edge)
4. 기존 코드 보호: 기존 Workflow를 Subgraph로 통합

이 Orchestrator는 하나의 LangGraph로 전체 파이프라인을 구현합니다:

Flow:
    1. parse_all_sections: DOCX에서 모든 Heading 1 Section 추출
    2. classify_sections: MetaSectionAgent로 각 Section 분류 (LLM)
    3. route_to_workflow: 분류에 따라 적절한 Workflow로 라우팅 (Conditional)
       - incoming_ls → process_incoming_ls
       - maintenance → process_maintenance
       - other → skip_section
    4. aggregate_outputs: 모든 결과 집계
    5. generate_summary: 최종 요약 생성
"""

import logging
from pathlib import Path
from typing import Any, Literal, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..agents import MetaSectionAgent
from ..models import SectionClassification, SectionMetadata, SectionType, Release, Technology
from ..utils.document_parser import AllSectionsParser, HeadingSection
from ..utils.llm_manager import LLMManager

# Import existing workflows for subgraph integration
from .incoming_ls_workflow import IncomingLSWorkflow
from .maintenance_workflow import MaintenanceWorkflow

logger = logging.getLogger(__name__)


class SectionResult(TypedDict):
    """개별 Section 처리 결과"""
    title: str
    section_type: str
    release: Optional[str]
    technology: Optional[str]
    output_file: str
    items_count: int
    status: str


class UnifiedOrchestratorState(TypedDict):
    """통합 Orchestrator State"""

    # Input
    docx_path: str
    output_dir: str
    meeting_id: str
    meeting_number: str

    # Section 타입 필터 (None이면 모두 처리)
    section_types_filter: Optional[list[str]]

    # Parsed sections
    all_sections: list[dict]  # HeadingSection을 dict로 변환
    classified_sections: list[dict]  # 분류 완료된 섹션들

    # Current processing
    current_section_idx: int
    current_section: Optional[dict]
    current_classification: Optional[dict]

    # Results
    section_results: list[SectionResult]

    # Final output
    summary: str
    total_processed: int
    total_skipped: int

    # Metadata
    processing_notes: list[str]


class UnifiedOrchestrator:
    """
    통합 LangGraph Orchestrator

    🚨 이 클래스는 하나의 LangGraph로 전체 파이프라인을 구현합니다.
    - MetaSectionAgent로 Section 타입 분류 (LLM)
    - Conditional Edge로 동적 워크플로우 라우팅
    - 기존 IncomingLSWorkflow, MaintenanceWorkflow를 내부적으로 호출
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.llm = LLMManager()

        # MetaSectionAgent (Section 분류용)
        self.meta_agent = MetaSectionAgent(self.llm, self.config)

        # Sub-workflows (lazy initialization)
        self._incoming_ls_workflow: Optional[IncomingLSWorkflow] = None
        self._maintenance_workflow: Optional[MaintenanceWorkflow] = None

        # LangGraph 빌드
        self.app = self._build_graph()

    @property
    def incoming_ls_workflow(self) -> IncomingLSWorkflow:
        """IncomingLS Workflow (lazy init)"""
        if self._incoming_ls_workflow is None:
            self._incoming_ls_workflow = IncomingLSWorkflow(self.config)
        return self._incoming_ls_workflow

    @property
    def maintenance_workflow(self) -> MaintenanceWorkflow:
        """Maintenance Workflow (lazy init)"""
        if self._maintenance_workflow is None:
            self._maintenance_workflow = MaintenanceWorkflow(self.config)
        return self._maintenance_workflow

    def _build_graph(self) -> StateGraph:
        """통합 LangGraph 빌드"""
        workflow = StateGraph(UnifiedOrchestratorState)

        # 노드 추가
        workflow.add_node("parse_all_sections", self._parse_all_sections)
        workflow.add_node("classify_sections", self._classify_sections)
        workflow.add_node("select_next_section", self._select_next_section)
        workflow.add_node("process_incoming_ls", self._process_incoming_ls)
        workflow.add_node("process_maintenance", self._process_maintenance)
        workflow.add_node("skip_section", self._skip_section)
        workflow.add_node("aggregate_outputs", self._aggregate_outputs)
        workflow.add_node("generate_summary", self._generate_summary)

        # Entry point
        workflow.set_entry_point("parse_all_sections")

        # Linear edges
        workflow.add_edge("parse_all_sections", "classify_sections")
        workflow.add_edge("classify_sections", "select_next_section")

        # Conditional routing based on section type
        workflow.add_conditional_edges(
            "select_next_section",
            self._route_section,
            {
                "incoming_ls": "process_incoming_ls",
                "maintenance": "process_maintenance",
                "skip": "skip_section",
                "done": "aggregate_outputs",
            }
        )

        # After processing, go back to select next
        workflow.add_edge("process_incoming_ls", "select_next_section")
        workflow.add_edge("process_maintenance", "select_next_section")
        workflow.add_edge("skip_section", "select_next_section")

        # Final edges
        workflow.add_edge("aggregate_outputs", "generate_summary")
        workflow.add_edge("generate_summary", END)

        return workflow.compile()

    def _parse_all_sections(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """Step 1: 모든 Heading 1 Section 추출"""
        docx_path = state.get("docx_path", "")

        logger.info(f"[Orchestrator] Step 1: Parsing all sections from {docx_path}")

        try:
            parser = AllSectionsParser(docx_path, self.llm)
            sections = parser.extract_all_heading1_sections()

            # HeadingSection을 dict로 변환 (JSON serializable)
            sections_dict = []
            for s in sections:
                sections_dict.append({
                    "title": s.title,
                    "content": s.content,
                    "content_preview": s.content_preview,
                })

            state["all_sections"] = sections_dict
            state["processing_notes"] = [f"Parsed {len(sections_dict)} sections"]
            logger.info(f"[Orchestrator] Found {len(sections_dict)} sections")

        except Exception as e:
            logger.error(f"[Orchestrator] Parse failed: {e}")
            state["all_sections"] = []
            state["processing_notes"] = [f"Parse error: {e}"]

        return state

    def _classify_sections(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """Step 2: 각 Section을 LLM으로 분류"""
        all_sections = state.get("all_sections", [])
        section_types_filter = state.get("section_types_filter")

        logger.info(f"[Orchestrator] Step 2: Classifying {len(all_sections)} sections")

        classified = []
        for section in all_sections:
            title = section.get("title", "")
            preview = section.get("content_preview", "")

            # MetaSectionAgent로 분류 (LLM 기반)
            classification = self.meta_agent.classify(
                section_title=title,
                content_preview=preview
            )

            # 필터 적용
            should_process = True
            if section_types_filter:
                should_process = str(classification.section_type) in section_types_filter

            classified.append({
                "title": title,
                "content": section.get("content", ""),
                "content_preview": preview,
                "section_type": str(classification.section_type),
                "release": str(classification.release) if classification.release else None,
                "technology": str(classification.technology) if classification.technology else None,
                "confidence": classification.confidence,
                "should_process": should_process,
            })

            logger.info(
                f"[Orchestrator] Classified '{title[:30]}...' as {classification.section_type} "
                f"(process: {should_process})"
            )

        state["classified_sections"] = classified
        state["current_section_idx"] = 0
        state["section_results"] = []
        state["processing_notes"].append(f"Classified {len(classified)} sections")

        return state

    def _select_next_section(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """현재 처리할 Section 선택"""
        idx = state.get("current_section_idx", 0)
        classified = state.get("classified_sections", [])

        if idx < len(classified):
            state["current_section"] = classified[idx]
            state["current_classification"] = classified[idx]
            logger.info(f"[Orchestrator] Selected section {idx + 1}/{len(classified)}: {classified[idx].get('title', '')[:40]}")
        else:
            state["current_section"] = None
            state["current_classification"] = None

        return state

    def _route_section(self, state: UnifiedOrchestratorState) -> Literal["incoming_ls", "maintenance", "skip", "done"]:
        """Section 타입에 따라 라우팅 결정"""
        current = state.get("current_section")

        if current is None:
            return "done"

        if not current.get("should_process", False):
            return "skip"

        section_type = current.get("section_type", "")

        if section_type == "incoming_ls":
            return "incoming_ls"
        elif section_type == "maintenance":
            return "maintenance"
        else:
            return "skip"

    def _process_incoming_ls(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """Incoming LS Section 처리"""
        current = state.get("current_section", {})
        output_dir = state.get("output_dir", "")
        meeting_id = state.get("meeting_id", "unknown")
        docx_path = state.get("docx_path", "")

        logger.info(f"[Orchestrator] Processing Incoming LS: {current.get('title', '')[:40]}")

        try:
            # IncomingLSWorkflow는 docx_path를 받아서 처리
            # 새 구조: meetings/{meeting_id}/incoming_ls.md
            output_file = Path(output_dir) / "meetings" / meeting_id / "incoming_ls.md"

            result = self.incoming_ls_workflow.run(docx_path)

            # 결과 저장
            markdown = result.get("markdown_output", "")
            if markdown:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown)

            issues_count = len(result.get("issues", []))

            state["section_results"].append({
                "title": current.get("title", ""),
                "section_type": "incoming_ls",
                "release": None,
                "technology": None,
                "output_file": str(output_file),
                "items_count": issues_count,
                "status": "success",
            })

            logger.info(f"[Orchestrator] Incoming LS completed: {issues_count} issues")

        except Exception as e:
            logger.error(f"[Orchestrator] Incoming LS failed: {e}")
            state["section_results"].append({
                "title": current.get("title", ""),
                "section_type": "incoming_ls",
                "release": None,
                "technology": None,
                "output_file": "",
                "items_count": 0,
                "status": f"error: {e}",
            })

        # 다음 섹션으로
        state["current_section_idx"] = state.get("current_section_idx", 0) + 1
        return state

    def _process_maintenance(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """Maintenance Section 처리"""
        current = state.get("current_section", {})
        output_dir = state.get("output_dir", "")
        meeting_id = state.get("meeting_id", "unknown")
        meeting_number = state.get("meeting_number", "unknown")

        title = current.get("title", "")
        release_str = current.get("release")
        tech_str = current.get("technology")

        logger.info(f"[Orchestrator] Processing Maintenance: {title[:40]} (release={release_str}, tech={tech_str})")

        try:
            # SectionMetadata 생성
            release = None
            technology = None

            if release_str:
                try:
                    release = Release(release_str)
                except ValueError:
                    pass

            if tech_str:
                try:
                    technology = Technology(tech_str)
                except ValueError:
                    pass

            classification = SectionClassification(
                section_type=SectionType.MAINTENANCE,
                release=release,
                technology=technology,
                confidence=current.get("confidence", 0.8)
            )

            metadata = SectionMetadata(
                title=title,
                classification=classification,
                content_preview=current.get("content_preview", "")[:500]
            )

            # 출력 파일명 생성 - 새 구조: meetings/{meeting_id}/{suffix}.md
            suffix = metadata.get_output_filename_suffix()
            output_file = Path(output_dir) / "meetings" / meeting_id / f"{suffix}.md"

            # MaintenanceWorkflow 실행
            result = self.maintenance_workflow.run_and_save(
                section_text=current.get("content", ""),
                output_path=str(output_file),
                section_metadata=metadata,
                meeting_number=meeting_number
            )

            items_count = len(result.get("issues", []))

            state["section_results"].append({
                "title": title,
                "section_type": "maintenance",
                "release": release_str,
                "technology": tech_str,
                "output_file": str(output_file),
                "items_count": items_count,
                "status": "success",
            })

            logger.info(f"[Orchestrator] Maintenance completed: {items_count} issues → {output_file.name}")

        except Exception as e:
            logger.error(f"[Orchestrator] Maintenance failed: {e}")
            state["section_results"].append({
                "title": title,
                "section_type": "maintenance",
                "release": release_str,
                "technology": tech_str,
                "output_file": "",
                "items_count": 0,
                "status": f"error: {e}",
            })

        # 다음 섹션으로
        state["current_section_idx"] = state.get("current_section_idx", 0) + 1
        return state

    def _skip_section(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """Section 스킵 (지원하지 않는 타입)"""
        current = state.get("current_section", {})

        logger.info(f"[Orchestrator] Skipping: {current.get('title', '')[:40]} (type: {current.get('section_type')})")

        # 다음 섹션으로
        state["current_section_idx"] = state.get("current_section_idx", 0) + 1
        return state

    def _aggregate_outputs(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """모든 결과 집계"""
        results = state.get("section_results", [])

        processed = len([r for r in results if r.get("status") == "success"])
        skipped = len(state.get("classified_sections", [])) - len(results)

        state["total_processed"] = processed
        state["total_skipped"] = skipped

        logger.info(f"[Orchestrator] Aggregated: {processed} processed, {skipped} skipped")

        return state

    def _generate_summary(self, state: UnifiedOrchestratorState) -> UnifiedOrchestratorState:
        """최종 요약 생성"""
        results = state.get("section_results", [])
        meeting_id = state.get("meeting_id", "unknown")

        lines = [
            f"# Processing Summary: {meeting_id}",
            "",
            f"**Total Sections Found**: {len(state.get('classified_sections', []))}",
            f"**Sections Processed**: {state.get('total_processed', 0)}",
            f"**Sections Skipped**: {state.get('total_skipped', 0)}",
            "",
            "## Results",
            "",
        ]

        for r in results:
            status_icon = "✅" if r.get("status") == "success" else "❌"
            lines.append(f"- {status_icon} **{r.get('title', 'Unknown')[:50]}**")
            lines.append(f"  - Type: {r.get('section_type')}")
            if r.get("release"):
                lines.append(f"  - Release: {r.get('release')}")
            if r.get("technology"):
                lines.append(f"  - Technology: {r.get('technology')}")
            lines.append(f"  - Items: {r.get('items_count', 0)}")
            if r.get("output_file"):
                lines.append(f"  - Output: {Path(r.get('output_file', '')).name}")
            lines.append("")

        state["summary"] = "\n".join(lines)

        logger.info("[Orchestrator] Summary generated")

        return state

    def run(
        self,
        docx_path: str,
        output_dir: str,
        meeting_id: str = "unknown",
        meeting_number: Optional[str] = None,
        section_types: Optional[list[str]] = None,
    ) -> UnifiedOrchestratorState:
        """
        통합 파이프라인 실행

        Args:
            docx_path: DOCX 파일 경로
            output_dir: 출력 디렉토리
            meeting_id: 미팅 ID (예: "RAN1_120")
            meeting_number: 미팅 번호 (예: "120"), None이면 meeting_id에서 추출
            section_types: 처리할 Section 타입 필터 (None이면 모두 처리)

        Returns:
            최종 state
        """
        # meeting_number 자동 추출
        if meeting_number is None:
            parts = meeting_id.split("_")
            meeting_number = parts[-1] if len(parts) >= 2 else "unknown"

        initial_state: UnifiedOrchestratorState = {
            "docx_path": docx_path,
            "output_dir": output_dir,
            "meeting_id": meeting_id,
            "meeting_number": meeting_number,
            "section_types_filter": section_types,
            "all_sections": [],
            "classified_sections": [],
            "current_section_idx": 0,
            "current_section": None,
            "current_classification": None,
            "section_results": [],
            "summary": "",
            "total_processed": 0,
            "total_skipped": 0,
            "processing_notes": [],
        }

        logger.info(f"[Orchestrator] Starting unified pipeline: {meeting_id}")

        result = self.app.invoke(initial_state)

        logger.info(
            f"[Orchestrator] Completed: {result.get('total_processed', 0)} processed, "
            f"{result.get('total_skipped', 0)} skipped"
        )

        return result

    def get_graph_visualization(self) -> bytes:
        """그래프 시각화 PNG 반환"""
        return self.app.get_graph().draw_mermaid_png()

    def get_mermaid_code(self) -> str:
        """Mermaid 코드 반환"""
        return self.app.get_graph().draw_mermaid()


def create_unified_orchestrator(config: Optional[dict] = None) -> UnifiedOrchestrator:
    """UnifiedOrchestrator 팩토리 함수"""
    return UnifiedOrchestrator(config)
