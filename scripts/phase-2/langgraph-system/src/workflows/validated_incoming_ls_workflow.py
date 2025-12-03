"""
Validated Incoming LS Workflow - 검증 루프 포함

기존 IncomingLSWorkflow에 2-Layer Validation 추가:
- Layer 1: Step-wise Validation (각 노드별 검증)
- Layer 2: Final Validation (100% 정확도 검증)

100% 정확도 달성 전략:
Validate → [100% 미만] → Identify Errors → Auto-Correct → Re-validate
                ↓
         [최대 3회 반복]
                ↓
         [여전히 실패] → Manual Review Flag + 상세 오류 리포트
"""

import logging
from pathlib import Path
from typing import Any, TypedDict, Optional

from langgraph.graph import StateGraph, END

from ..utils.document_parser import DocumentParser
from ..utils.llm_manager import LLMManager
from ..agents.incoming_ls_agent import IncomingLSAgent
from ..validators import (
    ParseValidator,
    BoundaryValidator,
    MetadataValidator,
    ClassificationValidator,
    FinalValidator,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class ValidatedIncomingLSState(TypedDict):
    """Validated Incoming LS Workflow State"""

    # Input
    docx_path: str

    # Parsed data
    section_text: str
    meeting_number: str

    # Processing
    issues: list
    cc_only_items: list

    # Output
    markdown_output: str

    # Validation
    validation_status: str
    validation_accuracy: float
    validation_report: str
    requires_manual_review: bool

    # Metadata
    confidence_score: float
    processing_notes: list[str]


class ValidatedIncomingLSWorkflow:
    """
    검증 루프가 포함된 Incoming LS Workflow

    100% 정확도 목표의 2-Layer Validation:
    - Layer 1: Step-wise (Parse, Boundary, Metadata, Classification)
    - Layer 2: Final (원본 대비 완전성 검증)
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        self.llm = LLMManager()

        # Agent
        self.ls_agent = IncomingLSAgent(self.llm)

        # Validators
        self.parse_validator = ParseValidator(self.llm)
        self.boundary_validator = BoundaryValidator(self.llm)
        self.metadata_validator = MetadataValidator(self.llm)
        self.classification_validator = ClassificationValidator(self.llm)
        self.final_validator = FinalValidator(self.llm)

        # LangGraph 빌드
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """검증 노드가 포함된 LangGraph 빌드"""

        workflow = StateGraph(ValidatedIncomingLSState)

        # 노드 추가
        workflow.add_node("parse_document", self._parse_document)
        workflow.add_node("validate_parse", self._validate_parse)
        workflow.add_node("extract_meeting_number", self._extract_meeting_number)
        workflow.add_node("process_section", self._process_section)
        workflow.add_node("validate_processing", self._validate_processing)
        workflow.add_node("generate_output", self._generate_output)
        workflow.add_node("final_validation", self._final_validation)

        # Edge 추가
        workflow.set_entry_point("parse_document")
        workflow.add_edge("parse_document", "validate_parse")

        # 조건부 엣지: 파싱 검증 통과 여부
        workflow.add_conditional_edges(
            "validate_parse",
            self._should_continue_after_parse,
            {
                "continue": "extract_meeting_number",
                "retry": "parse_document",
                "fail": END,
            }
        )

        workflow.add_edge("extract_meeting_number", "process_section")
        workflow.add_edge("process_section", "validate_processing")

        # 조건부 엣지: 처리 검증 통과 여부
        workflow.add_conditional_edges(
            "validate_processing",
            self._should_continue_after_processing,
            {
                "continue": "generate_output",
                "retry": "process_section",
                "fail": END,
            }
        )

        workflow.add_edge("generate_output", "final_validation")
        workflow.add_edge("final_validation", END)

        return workflow.compile()

    def _parse_document(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 1: 문서 파싱"""
        docx_path = state.get("docx_path", "")

        logger.info(f"[Parse] Loading document: {docx_path}")

        try:
            parser = DocumentParser(docx_path, llm_manager=self.llm)
            parser.parse_paragraphs()
            section_text = parser.get_section_text("incoming_ls")

            state["section_text"] = section_text
            state["processing_notes"] = state.get("processing_notes", [])
            state["processing_notes"].append(f"Extracted {len(section_text)} chars")

            logger.info(f"[Parse] Extracted {len(section_text)} characters")

        except Exception as e:
            logger.error(f"[Parse] Failed: {e}")
            state["section_text"] = ""
            state["processing_notes"] = [f"Parse error: {e}"]

        return state

    def _validate_parse(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 1.5: 파싱 검증"""
        section_text = state.get("section_text", "")

        logger.info("[Validate] Running parse validation...")

        result = self.parse_validator.validate_with_correction_loop(
            section_text,
            context={"docx_path": state.get("docx_path")}
        )

        if result.corrected_output:
            state["section_text"] = result.corrected_output
            state["processing_notes"].append("Parse auto-corrected")

        state["_parse_validation_status"] = result.status.value
        state["_parse_retry_count"] = result.retry_count

        logger.info(f"[Validate] Parse validation: {result.status.value} ({result.accuracy:.0%})")

        return state

    def _should_continue_after_parse(self, state: ValidatedIncomingLSState) -> str:
        """파싱 검증 후 다음 단계 결정"""
        status = state.get("_parse_validation_status", "fail")
        retry_count = state.get("_parse_retry_count", 0)

        if status == "pass":
            return "continue"
        elif retry_count < 3 and status in ("fail", "corrected"):
            return "retry"
        else:
            state["requires_manual_review"] = True
            return "fail"

    def _extract_meeting_number(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 2: 미팅 번호 추출 (일반화 - 모든 WG 지원)"""
        docx_path = state.get("docx_path", "")
        section_text = state.get("section_text", "")
        filename = Path(docx_path).name

        prompt = f"""Extract the 3GPP working group meeting number from this information.

**Filename:** {filename}
**Section text (first 500 chars):** {section_text[:500]}

Look for patterns: WG#NNN, TSGXX_NNN (e.g., RAN1#120, TSGR1_120, RAN2#105)
Return ONLY the meeting number (like "119", "120"), nothing else."""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=256)
            meeting_number = "".join(c for c in response.strip() if c.isdigit())
            state["meeting_number"] = meeting_number if meeting_number else "unknown"
            logger.info(f"[Meeting] Extracted: {meeting_number}")

        except Exception as e:
            logger.warning(f"[Meeting] Failed: {e}")
            state["meeting_number"] = "unknown"

        return state

    def _process_section(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 3: LSAgent로 처리"""
        section_text = state.get("section_text", "")
        meeting_number = state.get("meeting_number", "unknown")

        if not section_text:
            state["issues"] = []
            state["cc_only_items"] = []
            return state

        logger.info("[Process] Running IncomingLSAgent...")

        agent_state = {
            "content": section_text,
            "metadata": {"meeting_number": meeting_number},
        }

        result_state = self.ls_agent.process(agent_state)

        # Issues 추출 (IncomingLSAgent 출력 형식에 맞춤)
        # Agent는 structured_output (markdown)을 반환하므로,
        # issues와 cc_only를 별도로 파싱해야 함
        # 현재는 agent 내부에서 이미 issues를 생성함
        state["issues"] = result_state.get("issues", [])
        state["cc_only_items"] = result_state.get("cc_only_items", [])
        state["markdown_output"] = result_state.get("structured_output", "")

        logger.info(f"[Process] Got {len(state['issues'])} issues, {len(state['cc_only_items'])} CC-only")

        return state

    def _validate_processing(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 3.5: 처리 결과 검증 (Boundary, Metadata, Classification)"""
        issues = state.get("issues", [])
        section_text = state.get("section_text", "")

        logger.info("[Validate] Running processing validation...")

        all_errors = []
        all_corrections = False

        # Boundary Validation
        boundary_result = self.boundary_validator.validate_with_correction_loop(
            issues,
            context={"section_text": section_text}
        )
        all_errors.extend(boundary_result.errors)
        if boundary_result.corrected_output:
            state["issues"] = boundary_result.corrected_output
            all_corrections = True

        # Metadata Validation
        metadata_result = self.metadata_validator.validate_with_correction_loop(
            state["issues"],
            context={}
        )
        all_errors.extend(metadata_result.errors)
        if metadata_result.corrected_output:
            state["issues"] = metadata_result.corrected_output
            all_corrections = True

        # Classification Validation
        classification_result = self.classification_validator.validate_with_correction_loop(
            state["issues"],
            context={}
        )
        all_errors.extend(classification_result.errors)
        if classification_result.corrected_output:
            state["issues"] = classification_result.corrected_output
            all_corrections = True

        # 종합 상태
        all_pass = all(
            r.status == ValidationStatus.PASS
            for r in [boundary_result, metadata_result, classification_result]
        )

        state["_processing_validation_status"] = "pass" if all_pass else "fail"
        state["_processing_retry_count"] = max(
            boundary_result.retry_count,
            metadata_result.retry_count,
            classification_result.retry_count,
        )

        if all_corrections:
            state["processing_notes"].append("Processing auto-corrected")

        logger.info(f"[Validate] Processing validation: {'pass' if all_pass else 'fail'}")

        return state

    def _should_continue_after_processing(self, state: ValidatedIncomingLSState) -> str:
        """처리 검증 후 다음 단계 결정"""
        status = state.get("_processing_validation_status", "fail")
        retry_count = state.get("_processing_retry_count", 0)

        if status == "pass":
            return "continue"
        elif retry_count < 3:
            return "retry"
        else:
            # 최선의 결과로 계속 진행
            return "continue"

    def _generate_output(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 4: Markdown 출력 생성"""
        # 이미 process_section에서 생성됨
        if not state.get("markdown_output"):
            state["markdown_output"] = "# Incoming Liaison Statements\n\n*No content*"

        return state

    def _final_validation(self, state: ValidatedIncomingLSState) -> ValidatedIncomingLSState:
        """Step 5: 최종 검증 (100% 정확도 목표)"""
        logger.info("[Final] Running final validation...")

        data = {
            "issues": state.get("issues", []),
            "cc_only_items": state.get("cc_only_items", []),
            "markdown_output": state.get("markdown_output", ""),
        }

        # 동적 WG 지원 - config 또는 state에서 가져옴
        working_group = state.get("working_group", "RAN1")
        context = {
            "section_text": state.get("section_text", ""),
            "meeting_id": f"{working_group}_{state.get('meeting_number', 'unknown')}",
        }

        result = self.final_validator.validate_with_correction_loop(data, context)

        state["validation_status"] = result.status.value
        state["validation_accuracy"] = result.accuracy
        state["validation_report"] = result.notes[0] if result.notes else ""
        state["requires_manual_review"] = result.status == ValidationStatus.MANUAL_REVIEW

        if result.corrected_output:
            state["issues"] = result.corrected_output.get("issues", state["issues"])
            state["cc_only_items"] = result.corrected_output.get("cc_only_items", state["cc_only_items"])

        logger.info(
            f"[Final] Validation: {result.status.value} ({result.accuracy:.0%})"
        )

        return state

    def run(self, docx_path: str) -> ValidatedIncomingLSState:
        """
        Workflow 실행

        Args:
            docx_path: DOCX 파일 경로

        Returns:
            최종 state
        """
        initial_state: ValidatedIncomingLSState = {
            "docx_path": docx_path,
            "section_text": "",
            "meeting_number": "",
            "issues": [],
            "cc_only_items": [],
            "markdown_output": "",
            "validation_status": "",
            "validation_accuracy": 0.0,
            "validation_report": "",
            "requires_manual_review": False,
            "confidence_score": 0.0,
            "processing_notes": [],
        }

        logger.info(f"[Workflow] Starting validated processing: {docx_path}")

        result = self.app.invoke(initial_state)

        logger.info(
            f"[Workflow] Completed - Status: {result.get('validation_status')}, "
            f"Accuracy: {result.get('validation_accuracy', 0):.0%}"
        )

        return result

    def run_and_save(
        self,
        docx_path: str,
        output_path: str,
        validation_dir: Optional[str] = None
    ) -> ValidatedIncomingLSState:
        """
        Workflow 실행 및 결과 저장

        Args:
            docx_path: DOCX 파일 경로
            output_path: 출력 Markdown 파일 경로
            validation_dir: 검증 리포트 저장 디렉토리

        Returns:
            최종 state
        """
        result = self.run(docx_path)

        # Markdown 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.get("markdown_output", ""))

        logger.info(f"[Workflow] Saved output: {output_path}")

        # 검증 리포트 저장
        if validation_dir and result.get("validation_report"):
            val_dir = Path(validation_dir)
            val_dir.mkdir(parents=True, exist_ok=True)

            # 동적 WG 지원
            working_group = result.get("working_group", "RAN1")
            meeting_id = f"{working_group}_{result.get('meeting_number', 'unknown')}"
            report_path = val_dir / f"{meeting_id}_validation_report.md"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(result.get("validation_report", ""))

            logger.info(f"[Workflow] Saved validation report: {report_path}")

        return result
