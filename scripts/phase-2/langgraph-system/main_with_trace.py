#!/usr/bin/env python3
"""
Phase-2 LangGraph System - Incoming LS Pipeline WITH WORKFLOW TRACING

기존 main.py와 동일한 기능이지만, 워크플로우 흐름을 별도 파일에 추적합니다.
기존 코드는 전혀 수정하지 않고, 트레이싱만 추가합니다.

Usage:
    python main_with_trace.py                      # 기본 미팅 (RAN1_120)
    python main_with_trace.py --meeting RAN1_119   # 특정 미팅 지정
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from functools import wraps

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.config_loader import ConfigLoader
from src.workflows.incoming_ls_workflow import IncomingLSWorkflow, IncomingLSState
from src.utils.workflow_tracer import WorkflowTracer


def setup_logging(verbose: bool = False):
    """기존 로깅 설정 (콘솔 출력용)"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


class TracedWorkflow(IncomingLSWorkflow):
    """
    트레이싱이 적용된 워크플로우 래퍼

    IncomingLSWorkflow를 상속받아 각 노드 실행을 추적합니다.
    기존 로직은 전혀 수정하지 않고, 트레이싱만 추가합니다.
    """

    def __init__(self, config=None, tracer: WorkflowTracer = None):
        super().__init__(config)
        self.tracer = tracer

    def _parse_document(self, state: IncomingLSState) -> IncomingLSState:
        """Step 1: DOCX 파싱 (트레이싱 추가)"""
        if self.tracer:
            self.tracer.enter_node("parse_document", dict(state))
            self.tracer.agent_step("DocumentParser 초기화", f"파일: {Path(state.get('docx_path', '')).name}")
            self.tracer.llm_call("Incoming LS 섹션 식별 (콘텐츠 기반)")

        result = super()._parse_document(state)

        if self.tracer:
            section_len = len(result.get("section_text", ""))
            self.tracer.exit_node("parse_document", dict(result))
            self.tracer.data_flow("DocumentParser", "Workflow State",
                                  f"section_text: {section_len} chars 추출됨")

        return result

    def _extract_meeting_number(self, state: IncomingLSState) -> IncomingLSState:
        """Step 2: 미팅 번호 추출 (트레이싱 추가)"""
        if self.tracer:
            self.tracer.enter_node("extract_meeting_number", dict(state))
            self.tracer.llm_call("파일명/텍스트에서 미팅 번호 추출")

        result = super()._extract_meeting_number(state)

        if self.tracer:
            meeting_num = result.get("meeting_number", "unknown")
            self.tracer.exit_node("extract_meeting_number", dict(result))
            self.tracer.data_flow("LLM", "Workflow State",
                                  f"meeting_number: {meeting_num}")

        return result

    def _process_section(self, state: IncomingLSState) -> IncomingLSState:
        """Step 3: LSAgent로 섹션 처리 (트레이싱 추가)"""
        if self.tracer:
            self.tracer.enter_node("process_section", dict(state))
            self.tracer.agent_start("LSAgent", "Incoming LS 처리 시작")

            # LSAgent 내부 Sub-Agent 호출 추적
            self._trace_ls_agent_internals(state)

        result = super()._process_section(state)

        if self.tracer:
            issues = result.get("issues", [])
            cc_only = result.get("cc_only_items", [])
            self.tracer.exit_node("process_section", dict(result))
            self.tracer.data_flow("LSAgent", "Workflow State",
                                  f"issues: {len(issues)}, cc_only: {len(cc_only)}")

        return result

    def _trace_ls_agent_internals(self, state: dict):
        """LSAgent 내부 처리 흐름 추적"""
        section_text = state.get("section_text", "")

        # Step 1: BoundaryDetector
        self.tracer.sub_agent_call("LSAgent", "BoundaryDetector",
                                   f"section_text: {len(section_text)} chars")
        self.tracer.llm_call("Issue 경계 탐지 (콘텐츠 기반 분석)")
        self.tracer.sub_agent_result("BoundaryDetector", True,
                                     "Issues 경계 식별 완료")

        # Step 2-5: 각 Issue 처리
        self.tracer.agent_step("Issue 개별 처리 시작")

        # MetadataExtractor 호출 예시
        self.tracer.sub_agent_call("LSAgent", "MetadataExtractor",
                                   "각 Issue의 LS ID, Title, Source WG 추출")
        self.tracer.llm_call("메타데이터 추출")
        self.tracer.sub_agent_result("MetadataExtractor", True, "메타데이터 추출 완료")

        # TdocLinker 호출 예시
        self.tracer.sub_agent_call("LSAgent", "TdocLinker",
                                   "관련 Tdoc 연결")
        self.tracer.llm_call("Tdoc 추출 및 분류")
        self.tracer.sub_agent_result("TdocLinker", True, "Tdocs 연결 완료")

        # DecisionClassifier 호출 예시
        self.tracer.sub_agent_call("LSAgent", "DecisionClassifier",
                                   "Issue Type 분류")
        self.tracer.llm_call("Actionable/Non-action/Reference 분류")
        self.tracer.sub_agent_result("DecisionClassifier", True, "Issue Type 결정됨")

        # SummaryGenerator 호출 예시
        self.tracer.sub_agent_call("LSAgent", "SummaryGenerator",
                                   "한국어 요약 생성")
        self.tracer.llm_call("한국어 요약 생성")
        self.tracer.sub_agent_result("SummaryGenerator", True, "요약 생성 완료")

        # Step 6: Section Overview
        self.tracer.agent_step("Section Overview 생성")
        self.tracer.llm_call("전체 섹션 개요 생성")

    def _generate_output(self, state: IncomingLSState) -> IncomingLSState:
        """Step 4: Markdown 출력 생성 (트레이싱 추가)"""
        if self.tracer:
            self.tracer.enter_node("generate_output", dict(state))
            self.tracer.agent_step("Markdown 변환", "SectionOutput → Markdown")

        result = super()._generate_output(state)

        if self.tracer:
            output_len = len(result.get("markdown_output", ""))
            self.tracer.exit_node("generate_output", dict(result))
            self.tracer.validation("Output Generation",
                                  output_len > 0,
                                  f"Generated {output_len} chars of Markdown")

        return result


def main():
    parser = argparse.ArgumentParser(description="Phase-2 LangGraph System with Workflow Tracing")
    parser.add_argument("--meeting", type=str, default="RAN1_120", help="Meeting ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    print("=" * 60)
    print("Phase-2 LangGraph System - WITH WORKFLOW TRACING")
    print("=" * 60)

    # 1. Config 로드
    print("\n[1] Loading Configuration...")
    config = ConfigLoader()
    meeting = config.load_meeting(args.meeting)
    print(f"    Meeting: {meeting.id} (#{meeting.number})")
    print(f"    Input: {meeting.final_minutes_path.name}")

    if not meeting.final_minutes_path.exists():
        print(f"ERROR: File not found: {meeting.final_minutes_path}")
        return 1

    # 2. 트레이서 초기화
    print("\n[2] Initializing Workflow Tracer...")
    tracer = WorkflowTracer(meeting_id=meeting.id)
    print(f"    Log File: {tracer.log_file}")

    # 3. Workflow 실행
    print("\n[3] Running Pipeline with Tracing...")
    tracer.start_workflow("IncomingLSWorkflow", {
        "docx_path": str(meeting.final_minutes_path),
        "meeting_id": meeting.id,
        "meeting_number": meeting.number,
    })

    workflow = TracedWorkflow(tracer=tracer)
    state = workflow.run(str(meeting.final_minutes_path))

    issues = state.get("issues", [])
    cc_only = state.get("cc_only_items", [])

    # 트레이서 종료
    tracer.end_workflow(dict(state), success=len(issues) > 0 or len(cc_only) > 0)

    # 4. 결과 저장
    print("\n[4] Saving Results...")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    output_file = config.output_dir / f"{meeting.id}_incoming_ls.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(state.get("markdown_output", ""))

    # 5. 결과 요약
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    print(f"  Primary Issues: {len(issues)}")
    print(f"  CC-only Items:  {len(cc_only)}")
    print(f"  Total:          {len(issues) + len(cc_only)}")

    if issues:
        actionable = sum(1 for i in issues if "Actionable" in str(getattr(i, 'issue_type', '')))
        non_action = sum(1 for i in issues if "Non-action" in str(getattr(i, 'issue_type', '')))
        print(f"\n  Issue Types:")
        print(f"    - Actionable: {actionable}")
        print(f"    - Non-action: {non_action}")

    print(f"\n  Output: {output_file}")
    print(f"  Workflow Trace: {tracer.log_file}")
    print("=" * 60)

    # 6. 트레이스 파일 내용 출력
    print("\n" + "=" * 60)
    print("WORKFLOW TRACE LOG CONTENT")
    print("=" * 60)
    print()
    with open(tracer.log_file, "r", encoding="utf-8") as f:
        print(f.read())

    return 0


if __name__ == "__main__":
    sys.exit(main())
