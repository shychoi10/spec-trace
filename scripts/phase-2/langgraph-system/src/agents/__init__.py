"""
Agents Package for Phase-2 LangGraph System

Agent Hierarchy (콘텐츠 기반, Section 번호 무관):
├── BaseAgent: 모든 Agent의 기반 클래스 (EVRIRL 지원)
├── Meta Agents: Section 분류 및 라우팅
│   └── MetaSectionAgent: LLM 기반 Section 타입 분류
├── Section Agents: 콘텐츠 유형별 처리 담당
│   └── LSAgent: Incoming Liaison Statements
└── Sub-Agents: 공유 기능 담당
    ├── BoundaryDetector
    ├── MetadataExtractor
    ├── DecisionClassifier
    ├── SummaryGenerator
    └── TdocLinker
"""

from .base_agent import AgentResult, BaseAgent, ReflectionResult
from .meta_section_agent import MetaSectionAgent
from .section_agents import LSAgent
from .sub_agents import (
    BoundaryDetector,
    DecisionClassifier,
    MetadataExtractor,
    SummaryGenerator,
    TdocLinker,
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    "ReflectionResult",
    # Meta Agents
    "MetaSectionAgent",
    # Section Agents
    "LSAgent",
    # Sub-Agents
    "BoundaryDetector",
    "MetadataExtractor",
    "DecisionClassifier",
    "SummaryGenerator",
    "TdocLinker",
]
