"""
OriginExtractorAgent: Issue의 Origin 블록을 추출하는 에이전트

Ground Truth 형식의 Origin 블록:
**Origin**
- Type: `Internal_Maintenance`
- Section: `7 — Pre-Rel-18 NR`
- Topic: `MIMO`
- from_LS: R1-2500012 (if applicable)

** 제1 원칙 준수 **
- 모든 추출은 LLM으로만 수행
- NO REGEX for semantic analysis
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent
from ...models import IssueOrigin, OriginType

logger = logging.getLogger(__name__)


class OriginExtractorAgent(BaseAgent):
    """
    Issue 텍스트에서 Origin 정보를 추출

    Origin 정보:
    - type: Internal_Maintenance, From_LS, LS 등
    - section: "7 — Pre-Rel-18 NR", "8.1 — Rel-18 MIMO" 등
    - topic: MIMO, DSS, Coverage Enhancement 등
    - from_ls: LS에서 파생된 경우 원본 LS의 Tdoc ID
    """

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Issue 텍스트에서 Origin 정보 추출

        Args:
            state:
                - issue_text: Issue 원문
                - section_title: Section 제목 (힌트용)
                - section_type: maintenance/incoming_ls 등

        Returns:
            state with origin: IssueOrigin
        """
        self.log_start("Origin extraction")

        issue_text = state.get("issue_text", "")
        section_title = state.get("section_title", "")
        section_type = state.get("section_type", "maintenance")

        origin = self._extract_origin_with_llm(
            issue_text, section_title, section_type
        )

        self.log_end(f"Origin extraction (type={origin.type})")
        return {**state, "origin": origin}

    def _extract_origin_with_llm(
        self,
        issue_text: str,
        section_title: str,
        section_type: str
    ) -> IssueOrigin:
        """
        LLM을 사용하여 Origin 정보 추출 (제1 원칙 준수)
        """
        prompt = f"""You are a 3GPP document analyzer. Extract the "Origin" information from this issue.

## Origin Types
- Internal_Maintenance: Internal maintenance issue within the WG
- From_LS: Maintenance issue originating from a Liaison Statement
- LS: Incoming Liaison Statement (for Section 5)
- WorkItem: Related to a specific Work Item
- ActionItem: Related to a previous Action Item

## Section Context
Section Title: {section_title}
Section Type: {section_type}

## Issue Text
{issue_text[:3000]}

## Output Format
Return a JSON object:
{{
  "type": "Internal_Maintenance" or "From_LS" or "LS" or "WorkItem" or "ActionItem",
  "section": "Human readable section description, e.g., '7 — Pre-Rel-18 NR' or '8.1 — Coverage Enhancement'",
  "topic": "Main topic like 'MIMO', 'DSS', 'Coverage Enhancement', or null if unclear",
  "from_ls": "If type is From_LS, the original LS Tdoc ID like 'R1-2500012', otherwise null"
}}

Analyze the content and determine:
1. Is this an internal maintenance issue or derived from an LS?
2. What section does this belong to (use section title as hint)?
3. What is the main technical topic?
4. If from LS, which LS document?

Return ONLY the JSON object.
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=1024)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"JSON parse failed: {error}")
                return self._create_default_origin(section_title, section_type)

            # OriginType 변환
            try:
                origin_type = OriginType(parsed.get("type", "Internal_Maintenance"))
            except ValueError:
                origin_type = OriginType.INTERNAL_MAINTENANCE

            return IssueOrigin(
                type=origin_type,
                section=parsed.get("section", section_title),
                topic=parsed.get("topic"),
                from_ls=parsed.get("from_ls")
            )

        except Exception as e:
            logger.error(f"LLM origin extraction failed: {e}")
            return self._create_default_origin(section_title, section_type)

    def _create_default_origin(
        self, section_title: str, section_type: str
    ) -> IssueOrigin:
        """
        LLM 실패 시 기본 Origin 생성

        NOTE: 제1 원칙에 따라 regex fallback 없음
        """
        if section_type == "incoming_ls":
            origin_type = OriginType.LS
        else:
            origin_type = OriginType.INTERNAL_MAINTENANCE

        return IssueOrigin(
            type=origin_type,
            section=section_title,
            topic=None,
            from_ls=None
        )

    def extract_from_context(
        self,
        section_context: dict[str, Any]
    ) -> IssueOrigin:
        """
        Section 컨텍스트에서 기본 Origin 생성 (배치 처리용)

        Args:
            section_context:
                - title: Section 제목
                - type: Section 타입 (maintenance, incoming_ls)
                - release: Rel-18, Pre-Rel-18 등
                - technology: NR, E-UTRA 등
        """
        section_type = section_context.get("type", "maintenance")
        title = section_context.get("title", "")
        release = section_context.get("release", "")
        technology = section_context.get("technology", "")

        # Origin type 결정
        if section_type == "incoming_ls":
            origin_type = OriginType.LS
        else:
            origin_type = OriginType.INTERNAL_MAINTENANCE

        # Section 문자열 생성
        section_str = title
        if not section_str:
            parts = []
            if release:
                parts.append(release)
            if technology:
                parts.append(technology)
            section_str = " ".join(parts) if parts else "Unknown Section"

        return IssueOrigin(
            type=origin_type,
            section=section_str,
            topic=None,
            from_ls=None
        )
