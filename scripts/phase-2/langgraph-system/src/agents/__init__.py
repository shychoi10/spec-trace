"""
Agents Package for Phase-2 LangGraph System

Agent Hierarchy (콘텐츠 기반, Section 번호 무관):
├── BaseAgent: 모든 Agent의 기반 클래스 (EVRIRL 지원)
├── Section Agents: 콘텐츠 유형별 처리 담당
│   └── LSAgent: Incoming Liaison Statements
└── Sub-Agents: 공유 기능 담당
    ├── BoundaryDetector
    ├── MetadataExtractor
    ├── DecisionClassifier
    ├── SummaryGenerator
    └── TdocLinker
"""

from .base_agent import BaseAgent, AgentResult, ReflectionResult
from .section_agents import LSAgent
from .sub_agents import (
    BoundaryDetector,
    MetadataExtractor,
    DecisionClassifier,
    SummaryGenerator,
    TdocLinker,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    "ReflectionResult",
    # Section Agents
    "LSAgent",
    # Sub-Agents
    "BoundaryDetector",
    "MetadataExtractor",
    "DecisionClassifier",
    "SummaryGenerator",
    "TdocLinker",
]
