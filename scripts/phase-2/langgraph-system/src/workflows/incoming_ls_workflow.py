"""
Incoming LS Workflow - Liaison Statements Processing

콘텐츠 기반 LangGraph Workflow입니다.
Section 번호에 종속되지 않고, Incoming LS 콘텐츠를 처리합니다.

Flow:
    1. parse_document: DOCX → Incoming LS 섹션 텍스트 추출
    2. extract_meeting_number: 미팅 번호 추출 (LLM)
    3. process_section: LSAgent로 Incoming LS 처리
    4. generate_output: Markdown 출력 생성

Note: 이 워크플로우는 Section 번호(5, 6 등)에 관계없이
      Incoming LS 콘텐츠가 있는 모든 섹션에 적용됩니다.
"""

import logging
from pathlib import Path
from typing import Any, TypedDict, Optional

from langgraph.graph import StateGraph, END

from ..utils.document_parser import DocumentParser
from ..utils.llm_manager import LLMManager
from ..agents.section_agents import LSAgent
from ..models import SectionOutput

logger = logging.getLogger(__name__)


class IncomingLSState(TypedDict):
    """Incoming LS Workflow State (콘텐츠 기반, Section 번호 무관)"""

    # Input
    docx_path: str

    # Parsed data
    section_text: str
    meeting_number: str

    # Processing
    section_output: Optional[SectionOutput]
    issues: list
    cc_only_items: list

    # Output
    markdown_output: str

    # Metadata
    confidence_score: float
    processing_notes: list[str]


class IncomingLSWorkflow:
    """Incoming LS 전용 LangGraph Workflow (콘텐츠 기반)"""

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: 설정 딕셔너리 (domain_hints 등)
        """
        self.config = config or {}
        self.llm = LLMManager()
        self.ls_agent = LSAgent(self.llm, config)

        # LangGraph 빌드
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph 빌드"""

        workflow = StateGraph(IncomingLSState)

        # 노드 추가
        workflow.add_node("parse_document", self._parse_document)
        workflow.add_node("extract_meeting_number", self._extract_meeting_number)
        workflow.add_node("process_section", self._process_section)
        workflow.add_node("generate_output", self._generate_output)

        # Edge 추가
        workflow.set_entry_point("parse_document")
        workflow.add_edge("parse_document", "extract_meeting_number")
        workflow.add_edge("extract_meeting_number", "process_section")
        workflow.add_edge("process_section", "generate_output")
        workflow.add_edge("generate_output", END)

        return workflow.compile()

    def _parse_document(self, state: IncomingLSState) -> IncomingLSState:
        """
        Step 1: DOCX 파싱 및 Incoming LS 섹션 추출 (LLM 기반)

        LLM이 문서에서 "Incoming Liaison Statements" 섹션을 찾습니다.
        Section 번호에 의존하지 않고 콘텐츠 기반으로 식별합니다.

        Args:
            state: workflow state

        Returns:
            업데이트된 state (section_text 추가)
        """
        docx_path = state.get("docx_path", "")

        logger.info(f"[Parse] Loading document: {docx_path}")

        try:
            # LLM 기반 DocumentParser 사용
            parser = DocumentParser(docx_path, llm_manager=self.llm)
            parser.parse_paragraphs()

            # LLM이 Incoming LS 섹션을 추출 (콘텐츠 기반)
            # Note: get_section_text는 내부적으로 LLM을 사용하여 콘텐츠 기반 식별
            section_text = parser.get_section_text("incoming_ls")

            if not section_text:
                logger.warning("[Parse] Incoming LS section not found by LLM")

            state["section_text"] = section_text
            state["processing_notes"] = state.get("processing_notes", [])
            state["processing_notes"].append(f"LLM extracted {len(section_text)} chars from Incoming LS section")

            logger.info(f"[Parse] LLM extracted Incoming LS section: {len(section_text)} characters")

        except Exception as e:
            logger.error(f"[Parse] Failed to parse document: {e}")
            state["section_text"] = ""
            state["processing_notes"] = [f"Parse error: {e}"]

        return state

    def _extract_meeting_number(self, state: IncomingLSState) -> IncomingLSState:
        """
        Step 2: 미팅 번호 추출 (LLM 기반)

        Args:
            state: workflow state

        Returns:
            업데이트된 state (meeting_number 추가)
        """
        docx_path = state.get("docx_path", "")
        section_text = state.get("section_text", "")

        # 파일명에서 힌트 추출
        filename = Path(docx_path).name

        prompt = f"""Extract the RAN1 meeting number from this information.

**Filename:** {filename}

**Section text (first 500 chars):**
{section_text[:500]}

**Instructions:**
1. Look for patterns like "RAN1#NNN", "RAN1 #NNN", "TSGR1_NNN", "Meeting NNN"
2. Extract just the number
3. If uncertain, return "unknown"

Return ONLY the meeting number (a number like "119", "120", "121", etc.), nothing else."""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=50)
            meeting_number = response.strip().replace("#", "").replace("RAN1", "").strip()

            # LLM 응답 정리 (숫자만 필터링 - 데이터 변환, 분석 아님)
            cleaned = "".join(c for c in meeting_number if c.isdigit())
            meeting_number = cleaned if cleaned else "unknown"

            state["meeting_number"] = meeting_number
            logger.info(f"[Meeting] Extracted meeting number: {meeting_number}")

        except Exception as e:
            logger.warning(f"[Meeting] Failed to extract meeting number: {e}")
            state["meeting_number"] = "unknown"

        return state

    def _process_section(self, state: IncomingLSState) -> IncomingLSState:
        """
        Step 3: LSAgent로 Incoming LS 처리

        Args:
            state: workflow state

        Returns:
            업데이트된 state (section_output, issues 추가)
        """
        section_text = state.get("section_text", "")
        meeting_number = state.get("meeting_number", "unknown")

        if not section_text:
            logger.warning("[Process] No section text to process")
            state["section_output"] = None
            state["issues"] = []
            state["cc_only_items"] = []
            return state

        logger.info(f"[Process] Processing Incoming LS with LSAgent")

        # Section 번호 추출 (LLM 기반) - 콘텐츠에서 동적으로 추출
        section_number = self._extract_section_number(section_text)
        self.ls_agent.section_number = section_number

        # LSAgent 실행
        agent_state = {
            "section_text": section_text,
            "meeting_number": meeting_number,
        }

        result_state = self.ls_agent.process(agent_state)

        state["section_output"] = result_state.get("section_output")
        state["issues"] = result_state.get("issues", [])
        state["cc_only_items"] = result_state.get("cc_only_items", [])

        # 신뢰도 계산
        issues = state["issues"]
        if issues:
            avg_confidence = sum(i.confidence_score for i in issues) / len(issues)
            state["confidence_score"] = avg_confidence
        else:
            state["confidence_score"] = 0.0

        logger.info(f"[Process] Processed {len(issues)} issues, {len(state['cc_only_items'])} CC-only items")

        return state

    def _extract_section_number(self, section_text: str) -> str:
        """
        Section 텍스트에서 Section 번호 추출 (LLM 기반)

        Args:
            section_text: Section 전체 텍스트

        Returns:
            Section 번호 (예: "5")
        """
        # 텍스트 처음 부분에서 Section 번호 힌트 찾기
        prompt = f"""What is the section number of this "Incoming Liaison Statements" section?

Look at the first few lines:
{section_text[:500]}

Common patterns:
- "N Incoming liaison statements" (where N is any number)
- "Section N: Incoming LS"
- "N. Incoming Liaison Statements"

Return ONLY the section number (e.g., "5", "6", etc.). If not found, return "unknown"."""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=20)
            section_number = response.strip()

            # 숫자만 추출 (데이터 정리, 분석 아님)
            cleaned = "".join(c for c in section_number if c.isdigit())
            return cleaned if cleaned else "unknown"

        except Exception as e:
            logger.warning(f"[Section] Failed to extract section number: {e}")
            return "unknown"

    def _generate_output(self, state: IncomingLSState) -> IncomingLSState:
        """
        Step 4: Markdown 출력 생성

        Args:
            state: workflow state

        Returns:
            업데이트된 state (markdown_output 추가)
        """
        section_output = state.get("section_output")

        if section_output is None:
            state["markdown_output"] = "# Incoming Liaison Statements\n\n*No content to process*"
            return state

        try:
            markdown_output = section_output.to_markdown()
            state["markdown_output"] = markdown_output

            logger.info(f"[Output] Generated {len(markdown_output)} chars of Markdown")

        except Exception as e:
            logger.error(f"[Output] Failed to generate Markdown: {e}")
            state["markdown_output"] = f"# Error generating output\n\n{e}"

        return state

    def run(self, docx_path: str) -> IncomingLSState:
        """
        Workflow 실행

        Args:
            docx_path: DOCX 파일 경로

        Returns:
            최종 state
        """
        initial_state: IncomingLSState = {
            "docx_path": docx_path,
            "section_text": "",
            "meeting_number": "",
            "section_output": None,
            "issues": [],
            "cc_only_items": [],
            "markdown_output": "",
            "confidence_score": 0.0,
            "processing_notes": [],
        }

        logger.info(f"[Workflow] Starting Incoming LS processing: {docx_path}")

        result = self.app.invoke(initial_state)

        logger.info(f"[Workflow] Completed with confidence: {result.get('confidence_score', 0):.2f}")

        return result

    def run_and_save(self, docx_path: str, output_path: str) -> IncomingLSState:
        """
        Workflow 실행 및 결과 저장

        Args:
            docx_path: DOCX 파일 경로
            output_path: 출력 Markdown 파일 경로

        Returns:
            최종 state
        """
        result = self.run(docx_path)

        # Markdown 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.get("markdown_output", ""))

        logger.info(f"[Workflow] Saved output to: {output_path}")

        return result


def create_incoming_ls_workflow(config: Optional[dict] = None) -> IncomingLSWorkflow:
    """
    Incoming LS Workflow 팩토리 함수

    Args:
        config: 설정 딕셔너리

    Returns:
        IncomingLSWorkflow 인스턴스
    """
    return IncomingLSWorkflow(config)


# Note: Section5* aliases removed - use content-based naming only
# (e.g., IncomingLSState, IncomingLSWorkflow)
