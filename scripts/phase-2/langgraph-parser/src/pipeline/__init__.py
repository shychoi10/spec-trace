"""
Pipeline 패키지 - 역할별 노드 (LangGraph 노드)

명세서 2장 참조:
- role_0_preprocess: 역할 0 - pandoc 변환
- role_1_metadata: 역할 1 - 메타데이터 추출
- role_2_toc: 역할 2 - TOC 파싱 + section_type
- role_3_sections: 역할 3 - 섹션 처리 (Orchestrator)
- role_4_validation: 역할 4 - 검증 + 크로스체크
"""

from .role_0_preprocess import preprocess_node
from .role_1_metadata import metadata_node
from .role_2_toc import toc_node
from .role_3_sections import sections_node
from .role_4_validation import validation_node

__all__ = [
    "preprocess_node",
    "metadata_node",
    "toc_node",
    "sections_node",
    "validation_node",
]
