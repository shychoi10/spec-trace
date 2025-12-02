"""
Workflow Tracer - Agentic AI 워크플로우 흐름 추적 로깅

기존 코드를 수정하지 않고, 워크플로우 흐름만 별도 파일에 기록합니다.
Agent 간 데이터 전달, 처리 과정, 검증 결과를 시각적으로 추적합니다.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from functools import wraps
import time


class WorkflowTracer:
    """Agentic AI 워크플로우 흐름 추적기"""

    # 시각적 구분자
    SEPARATOR = "═" * 80
    SUB_SEPARATOR = "─" * 60
    ARROW = "  └─→ "
    BULLET = "  • "

    def __init__(self, log_dir: Optional[Path] = None, meeting_id: str = "unknown"):
        """
        Args:
            log_dir: 로그 저장 디렉토리
            meeting_id: 미팅 ID (로그 파일명에 사용)
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent.parent.parent / "logs" / "phase-2" / "workflow-traces"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 타임스탬프 포함 로그 파일
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{meeting_id}_workflow_trace_{timestamp}.log"

        # 로거 설정 (별도 파일에만 기록)
        self.logger = logging.getLogger(f"workflow_tracer_{timestamp}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # 기존 핸들러 제거

        # 파일 핸들러 추가
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(file_handler)

        # 상태 추적
        self.start_time = None
        self.current_node = None
        self.node_history = []
        self.agent_calls = []

    def start_workflow(self, workflow_name: str, input_data: dict):
        """워크플로우 시작 기록"""
        self.start_time = time.time()

        self._log(self.SEPARATOR)
        self._log(f"🚀 AGENTIC AI WORKFLOW TRACE")
        self._log(self.SEPARATOR)
        self._log(f"")
        self._log(f"📌 Workflow: {workflow_name}")
        self._log(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"📁 Log File: {self.log_file.name}")
        self._log(f"")
        self._log(f"📥 INPUT DATA:")
        for key, value in input_data.items():
            if isinstance(value, str) and len(value) > 100:
                self._log(f"{self.BULLET}{key}: ({len(value)} chars)")
            else:
                self._log(f"{self.BULLET}{key}: {value}")
        self._log(f"")

    def end_workflow(self, output_data: dict, success: bool = True):
        """워크플로우 종료 기록"""
        elapsed = time.time() - self.start_time if self.start_time else 0

        self._log(f"")
        self._log(self.SEPARATOR)
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self._log(f"🏁 WORKFLOW COMPLETED: {status}")
        self._log(self.SEPARATOR)
        self._log(f"")
        self._log(f"⏱️  Total Time: {elapsed:.2f}s")
        self._log(f"📊 Nodes Executed: {len(self.node_history)}")
        self._log(f"🤖 Agent Calls: {len(self.agent_calls)}")
        self._log(f"")
        self._log(f"📤 OUTPUT SUMMARY:")

        issues = output_data.get("issues", [])
        cc_only = output_data.get("cc_only_items", [])
        confidence = output_data.get("confidence_score", 0)

        self._log(f"{self.BULLET}Primary Issues: {len(issues)}")
        self._log(f"{self.BULLET}CC-only Items: {len(cc_only)}")
        self._log(f"{self.BULLET}Confidence: {confidence:.2%}")

        if issues:
            self._log(f"")
            self._log(f"📋 ISSUES BREAKDOWN:")
            for idx, issue in enumerate(issues, 1):
                issue_type = getattr(issue, 'issue_type', 'unknown')
                title = getattr(issue, 'title', 'N/A')[:50]
                self._log(f"{self.BULLET}Issue {idx}: [{issue_type}] {title}...")

        self._log(f"")
        self._log(f"🔄 EXECUTION FLOW:")
        for idx, node in enumerate(self.node_history, 1):
            self._log(f"   {idx}. {node['name']} ({node['duration']:.2f}s)")

        self._log(f"")
        self._log(self.SEPARATOR)

    def enter_node(self, node_name: str, input_state: dict):
        """LangGraph 노드 진입 기록"""
        self.current_node = {
            "name": node_name,
            "start_time": time.time(),
            "input_keys": list(input_state.keys()),
        }

        self._log(f"")
        self._log(self.SUB_SEPARATOR)
        self._log(f"📍 NODE: {node_name}")
        self._log(self.SUB_SEPARATOR)
        self._log(f"")
        self._log(f"   ⬇️  Input State Keys: {', '.join(input_state.keys())}")

        # 주요 데이터 크기 표시
        for key in ["section_text", "docx_path", "meeting_number"]:
            if key in input_state:
                value = input_state[key]
                if isinstance(value, str):
                    self._log(f"      • {key}: {len(value)} chars" if len(value) > 50 else f"      • {key}: {value}")

    def exit_node(self, node_name: str, output_state: dict):
        """LangGraph 노드 종료 기록"""
        duration = time.time() - self.current_node["start_time"] if self.current_node else 0

        self._log(f"")
        self._log(f"   ⬆️  Output State Changes:")

        # 입력과 비교하여 새로 추가되거나 변경된 키 표시
        input_keys = set(self.current_node.get("input_keys", []))
        output_keys = set(output_state.keys())
        new_keys = output_keys - input_keys

        for key in new_keys:
            value = output_state[key]
            if isinstance(value, str):
                self._log(f"      + {key}: {len(value)} chars" if len(value) > 50 else f"      + {key}: {value}")
            elif isinstance(value, list):
                self._log(f"      + {key}: {len(value)} items")
            else:
                self._log(f"      + {key}: {type(value).__name__}")

        self._log(f"")
        self._log(f"   ⏱️  Duration: {duration:.2f}s")

        # 히스토리에 추가
        self.node_history.append({
            "name": node_name,
            "duration": duration,
            "new_keys": list(new_keys),
        })

    def agent_start(self, agent_name: str, step_info: str = ""):
        """Agent 실행 시작 기록"""
        self._log(f"")
        self._log(f"   🤖 AGENT: {agent_name}")
        if step_info:
            self._log(f"      📋 {step_info}")

    def agent_step(self, step_name: str, details: Optional[str] = None):
        """Agent 내부 단계 기록"""
        self._log(f"      └─ {step_name}")
        if details:
            self._log(f"         {details}")

    def sub_agent_call(self, parent_agent: str, sub_agent: str, input_summary: str = ""):
        """Sub-Agent 호출 기록"""
        self.agent_calls.append({
            "parent": parent_agent,
            "sub": sub_agent,
            "time": datetime.now().isoformat(),
        })

        self._log(f"")
        self._log(f"      ↳ Sub-Agent: {sub_agent}")
        if input_summary:
            self._log(f"         Input: {input_summary}")

    def sub_agent_result(self, sub_agent: str, success: bool, output_summary: str = ""):
        """Sub-Agent 결과 기록"""
        status = "✓" if success else "✗"
        self._log(f"         Result: {status} {output_summary}")

    def data_flow(self, from_component: str, to_component: str, data_summary: str):
        """데이터 흐름 기록"""
        self._log(f"")
        self._log(f"   📦 DATA FLOW: {from_component} → {to_component}")
        self._log(f"      {data_summary}")

    def validation(self, validator: str, passed: bool, details: str = ""):
        """검증 결과 기록"""
        status = "✅ PASSED" if passed else "⚠️ FAILED"
        self._log(f"")
        self._log(f"   🔍 VALIDATION [{validator}]: {status}")
        if details:
            self._log(f"      {details}")

    def llm_call(self, purpose: str, tokens_hint: str = ""):
        """LLM 호출 기록"""
        info = f" ({tokens_hint})" if tokens_hint else ""
        self._log(f"         🧠 LLM: {purpose}{info}")

    def _log(self, message: str):
        """로그 메시지 기록"""
        self.logger.debug(message)


# 글로벌 트레이서 인스턴스 (lazy initialization)
_global_tracer: Optional[WorkflowTracer] = None


def get_tracer(meeting_id: str = "unknown") -> WorkflowTracer:
    """글로벌 트레이서 가져오기"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = WorkflowTracer(meeting_id=meeting_id)
    return _global_tracer


def reset_tracer():
    """트레이서 리셋"""
    global _global_tracer
    _global_tracer = None
