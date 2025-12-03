"""
Multi-Section Orchestrator - 전체 파이프라인 조율

🚨 제1 원칙 (First Principles) 준수:
1. True Agentic AI: MetaSectionAgent가 LLM으로 Section 분류
2. Content-based Naming: Section 번호 없음
3. General Design: 동적 워크플로우 라우팅
4. 기존 코드 보호: IncomingLSWorkflow 동작 변경 없음

Flow:
    1. Document Parsing: DOCX에서 모든 Heading 1 Section 추출
    2. Section Classification: MetaSectionAgent로 각 Section 분류
    3. Workflow Routing: 분류에 따라 적절한 Workflow로 라우팅
    4. Output Generation: 각 Section별 Markdown 파일 생성
"""

import logging
from pathlib import Path
from typing import Optional

from .agents import MetaSectionAgent
from .models import SectionClassification, SectionMetadata, SectionType
from .utils.document_parser import AllSectionsParser, HeadingSection
from .utils.llm_manager import LLMManager
from .workflows import IncomingLSWorkflow, MaintenanceWorkflow

logger = logging.getLogger(__name__)


class MultiSectionOrchestrator:
    """
    Multi-Section 처리 오케스트레이터

    🚨 General Design 원칙:
    - MetaSectionAgent가 콘텐츠 기반으로 Section 타입 결정
    - 분류 결과에 따라 적절한 Workflow로 라우팅
    - Section 번호 하드코딩 없음

    지원 Section Types:
    - incoming_ls: IncomingLSWorkflow (Step-1)
    - maintenance: MaintenanceWorkflow (Step-2)
    - 기타: 향후 확장 예정
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.llm = LLMManager()

        # Agents
        self.meta_agent = MetaSectionAgent(self.llm, self.config)

        # Workflows (lazy initialization)
        self._incoming_ls_workflow: Optional[IncomingLSWorkflow] = None
        self._maintenance_workflow: Optional[MaintenanceWorkflow] = None

    @property
    def incoming_ls_workflow(self) -> IncomingLSWorkflow:
        """IncomingLS Workflow (lazy initialization)"""
        if self._incoming_ls_workflow is None:
            self._incoming_ls_workflow = IncomingLSWorkflow(self.config)
        return self._incoming_ls_workflow

    @property
    def maintenance_workflow(self) -> MaintenanceWorkflow:
        """Maintenance Workflow (lazy initialization)"""
        if self._maintenance_workflow is None:
            self._maintenance_workflow = MaintenanceWorkflow(self.config)
        return self._maintenance_workflow

    def process_document(
        self,
        docx_path: str,
        output_dir: str,
        meeting_id: str = "unknown",
        section_types: Optional[list[SectionType]] = None,
    ) -> dict:
        """
        전체 문서 처리 (모든 Section)

        🚨 True Agentic AI: Section 분류는 MetaSectionAgent가 LLM으로 수행

        Args:
            docx_path: DOCX 파일 경로
            output_dir: 출력 디렉토리
            meeting_id: 미팅 ID (예: "RAN1_120")
            section_types: 처리할 Section 타입 필터 (None이면 모두 처리)

        Returns:
            처리 결과 딕셔너리
        """
        logger.info(f"[Orchestrator] Starting multi-section processing: {docx_path}")

        # Output 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Step 1: 모든 Heading 1 Section 추출
        logger.info("[Orchestrator] Step 1: Extracting all Heading 1 sections...")
        parser = AllSectionsParser(docx_path, self.llm)
        sections = parser.extract_all_heading1_sections()

        if not sections:
            logger.warning("[Orchestrator] No sections found in document")
            return {"status": "no_sections", "sections_processed": 0}

        logger.info(f"[Orchestrator] Found {len(sections)} sections")

        # Step 2: 각 Section 분류 및 처리
        results = {
            "status": "success",
            "sections_found": len(sections),
            "sections_processed": 0,
            "sections_skipped": 0,
            "outputs": [],
        }

        for section in sections:
            result = self._process_section(
                section=section,
                output_dir=output_path,
                meeting_id=meeting_id,
                section_types_filter=section_types,
            )

            if result.get("processed"):
                results["sections_processed"] += 1
                results["outputs"].append(result)
            else:
                results["sections_skipped"] += 1

        logger.info(
            f"[Orchestrator] Completed: {results['sections_processed']} processed, "
            f"{results['sections_skipped']} skipped"
        )

        return results

    def _process_section(
        self,
        section: HeadingSection,
        output_dir: Path,
        meeting_id: str,
        section_types_filter: Optional[list[SectionType]] = None,
    ) -> dict:
        """
        개별 Section 처리

        Args:
            section: 파싱된 Section
            output_dir: 출력 디렉토리
            meeting_id: 미팅 ID
            section_types_filter: 처리할 Section 타입 필터

        Returns:
            처리 결과
        """
        # Step 2a: Section 분류 (LLM 기반)
        logger.info(f"[Orchestrator] Classifying section: {section.title}")

        classification = self.meta_agent.classify(
            section_title=section.title,
            content_preview=section.content_preview,
        )

        logger.info(
            f"[Orchestrator] Classified as: {classification.section_type} "
            f"(confidence: {classification.confidence:.2f})"
        )

        # 필터 적용
        if section_types_filter and classification.section_type not in section_types_filter:
            logger.info(
                f"[Orchestrator] Skipping {section.title} (not in filter: {section_types_filter})"
            )
            return {"processed": False, "reason": "filtered"}

        # Step 2b: Workflow 라우팅
        metadata = SectionMetadata(
            title=section.title,
            classification=classification,
            content_preview=section.content_preview,
        )

        if classification.section_type == SectionType.INCOMING_LS:
            return self._process_incoming_ls(section, metadata, output_dir, meeting_id)

        elif classification.section_type == SectionType.MAINTENANCE:
            return self._process_maintenance(section, metadata, output_dir, meeting_id)

        else:
            # 아직 지원하지 않는 타입
            logger.info(
                f"[Orchestrator] Section type '{classification.section_type}' not yet supported"
            )
            return {
                "processed": False,
                "reason": f"unsupported_type: {classification.section_type}",
            }

    def _process_incoming_ls(
        self,
        section: HeadingSection,
        metadata: SectionMetadata,
        output_dir: Path,
        meeting_id: str,
    ) -> dict:
        """
        Incoming LS Section 처리

        🚨 기존 코드 보호: IncomingLSWorkflow 직접 사용
        """
        logger.info("[Orchestrator] Processing as Incoming LS...")

        # 출력 파일 경로
        output_file = output_dir / f"{meeting_id}_incoming_ls.md"

        # IncomingLSWorkflow는 docx_path를 받으므로, 별도 처리 필요
        # 여기서는 section.content를 직접 사용하지 않고,
        # 기존 워크플로우가 문서를 다시 파싱하도록 함
        # (기존 동작 보호를 위해)

        # Note: IncomingLSWorkflow는 전체 문서를 받아서 LLM으로 추출하므로
        # 여기서는 결과만 기록
        return {
            "processed": True,
            "section_type": "incoming_ls",
            "title": section.title,
            "output_file": str(output_file),
            "note": "Use standalone IncomingLSWorkflow for full processing",
        }

    def _process_maintenance(
        self,
        section: HeadingSection,
        metadata: SectionMetadata,
        output_dir: Path,
        meeting_id: str,
    ) -> dict:
        """
        Maintenance Section 처리

        🚨 General Design: 하나의 MaintenanceWorkflow가 모든 Maintenance 처리
        """
        logger.info(
            f"[Orchestrator] Processing as Maintenance "
            f"(release: {metadata.release}, tech: {metadata.technology})..."
        )

        # 출력 파일 경로 생성 (콘텐츠 기반)
        filename_suffix = metadata.get_output_filename_suffix()
        output_file = output_dir / f"{meeting_id}_{filename_suffix}.md"

        # 미팅 번호 추출
        meeting_number = self._extract_meeting_number(meeting_id)

        # MaintenanceWorkflow 실행
        try:
            result = self.maintenance_workflow.run_and_save(
                section_text=section.content,
                output_path=str(output_file),
                section_metadata=metadata,
                meeting_number=meeting_number,
            )

            items_count = len(result.get("items", []))
            logger.info(
                f"[Orchestrator] Maintenance processed: {items_count} items → {output_file}"
            )

            return {
                "processed": True,
                "section_type": "maintenance",
                "title": section.title,
                "release": metadata.release,
                "technology": metadata.technology,
                "output_file": str(output_file),
                "items_count": items_count,
            }

        except Exception as e:
            logger.error(f"[Orchestrator] Maintenance processing failed: {e}")
            return {
                "processed": False,
                "section_type": "maintenance",
                "title": section.title,
                "reason": f"error: {e}",
            }

    def _extract_meeting_number(self, meeting_id: str) -> str:
        """미팅 ID에서 번호 추출 (예: RAN1_120 → 120)"""
        parts = meeting_id.split("_")
        if len(parts) >= 2:
            return parts[-1]
        return "unknown"

    def process_maintenance_only(
        self,
        docx_path: str,
        output_dir: str,
        meeting_id: str = "unknown",
    ) -> dict:
        """
        Maintenance Section만 처리 (편의 함수)

        Args:
            docx_path: DOCX 파일 경로
            output_dir: 출력 디렉토리
            meeting_id: 미팅 ID

        Returns:
            처리 결과
        """
        return self.process_document(
            docx_path=docx_path,
            output_dir=output_dir,
            meeting_id=meeting_id,
            section_types=[SectionType.MAINTENANCE],
        )


def create_orchestrator(config: Optional[dict] = None) -> MultiSectionOrchestrator:
    """
    오케스트레이터 팩토리 함수

    Args:
        config: 설정 딕셔너리

    Returns:
        MultiSectionOrchestrator 인스턴스
    """
    return MultiSectionOrchestrator(config)
