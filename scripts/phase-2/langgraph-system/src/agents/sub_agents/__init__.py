"""
Sub-Agents for Phase-2 LangGraph System

이 모듈은 Section Agent에서 사용하는 공유 Sub-Agent들을 제공합니다.
모든 Sub-Agent는 True Agentic AI 원칙을 따릅니다 (LLM 기반 분류/추출).

NEW Sub-Agents (Stage 1):
- BoundaryDetector: Issue 경계 탐지
- MetadataExtractor: 메타데이터 추출
- DecisionClassifier: Issue Type 분류
- SummaryGenerator: 한국어 요약 생성
- TdocLinker: Tdoc 연결 및 문서 유형 분류

LEGACY Sub-Agents (기존 호환용):
- IssueSplitterAgent: Issue 경계 식별 (JSON)
- TdocsExtractorAgent: 포괄적 Tdoc 추출 (Markdown)
- TdocsSelectorAgent: 선택적 Tdoc 필터링 (Dynamic Prompting)
- IssueFormatterAgent: Issue Markdown 포맷팅
- SectionOverviewAgent: Section Overview 생성
"""

# New Sub-Agents (Stage 1)
from .boundary_detector import BoundaryDetector
from .metadata_extractor import MetadataExtractor
from .decision_classifier import DecisionClassifier
from .summary_generator import SummaryGenerator
from .tdoc_linker import TdocLinker

# Legacy Sub-Agents (backward compatibility)
from .issue_splitter_agent import IssueSplitterAgent
from .tdocs_extractor_agent import TdocsExtractorAgent
from .tdocs_selector_agent import TdocsSelectorAgent
from .issue_formatter_agent import IssueFormatterAgent
from .section_overview_agent import SectionOverviewAgent

__all__ = [
    # New Sub-Agents
    "BoundaryDetector",
    "MetadataExtractor",
    "DecisionClassifier",
    "SummaryGenerator",
    "TdocLinker",
    # Legacy Sub-Agents
    "IssueSplitterAgent",
    "TdocsExtractorAgent",
    "TdocsSelectorAgent",
    "IssueFormatterAgent",
    "SectionOverviewAgent",
]
