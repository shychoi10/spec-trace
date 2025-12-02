# -*- coding: utf-8 -*-
"""
Section Agents for Phase-2 LangGraph System (콘텐츠 기반)

Section Agent handles content types and coordinates Sub-Agents.
Note: 콘텐츠 유형 기반 처리 - Section 번호에 종속되지 않음

Stage 1 (Incoming LS):
- LSAgent: Incoming Liaison Statements processing

Future Stages:
- MaintenanceAgent: Maintenance items processing
- WorkItemAgent: Work Items processing
- ActionItemAgent: Action Items processing
"""

from .ls_agent import LSAgent

__all__ = [
    "LSAgent",
]
