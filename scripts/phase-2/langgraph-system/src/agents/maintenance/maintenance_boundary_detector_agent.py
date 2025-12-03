"""
MaintenanceBoundaryDetectorAgent: Maintenance Section에서 Issue 경계를 감지

Maintenance Section의 특성:
- Topic 단위로 구분 (MIMO, Network Energy Savings 등)
- 각 Topic 내에 여러 Issue 존재
- Issue는 Draft CR 제출 → 논의 → Decision/Agreement 패턴

** 제1 원칙 준수 **
- 모든 경계 감지는 LLM으로만 수행
- NO REGEX for boundary detection
"""

import json
import logging
from typing import Any

from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MaintenanceBoundaryDetectorAgent(BaseAgent):
    """
    Maintenance Section에서 Issue 경계 감지

    감지 기준:
    - Topic 변경 (### 레벨 헤더)
    - 새로운 Draft CR/Discussion 시작
    - Agreement/Decision 블록 종료 후 새 항목 시작
    """

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Section 텍스트에서 Issue 경계 감지

        Args:
            state:
                - content: Section 전체 텍스트
                - section_type: maintenance
                - release: Rel-18, Pre-Rel-18 등
                - technology: NR, E-UTRA 등

        Returns:
            state with:
                - issues_raw: list[dict] with issue_text, topic, start_pos, end_pos
                - topics: list[str] Topic 목록
        """
        self.log_start("Maintenance boundary detection")

        content = state.get("content", "")
        release = state.get("release", "")
        technology = state.get("technology", "")

        if not content:
            return {**state, "issues_raw": [], "topics": []}

        # LLM으로 경계 감지
        issues_raw, topics = self._detect_boundaries_with_llm(
            content, release, technology
        )

        self.log_end(f"Detected {len(issues_raw)} issues in {len(topics)} topics")
        return {**state, "issues_raw": issues_raw, "topics": topics}

    def _detect_boundaries_with_llm(
        self,
        content: str,
        release: str,
        technology: str
    ) -> tuple[list[dict], list[str]]:
        """
        LLM을 사용하여 Issue 경계 감지 (제1 원칙 준수)
        """
        # 텍스트가 너무 길면 분할 처리
        max_chunk_size = 15000
        if len(content) > max_chunk_size:
            return self._detect_boundaries_chunked(content, release, technology)

        prompt = f"""You are a 3GPP meeting minutes parser. Analyze this Maintenance section and identify individual issues/items.

## Context
Release: {release or "Unknown"}
Technology: {technology or "NR"}

## Maintenance Section Content
{content}

## Task
1. Identify all TOPICS (main categories like MIMO, Network Energy Savings, DSS, etc.)
2. For each topic, identify individual ISSUES (technical items discussed)
3. Each issue typically has: Draft CR/Discussion → Technical discussion → Decision/Agreement

## Issue Identification Rules
- A new issue starts with a new TDoc submission or discussion item
- Issues are separated by Agreement/Decision statements
- Look for patterns like "The following proposals were discussed" or "Company X proposes"
- Issues end with Agreement, Decision, or transition to next item

## Output Format
Return a JSON object:
{{
  "topics": ["MIMO", "Network Energy Savings", ...],
  "issues": [
    {{
      "topic": "MIMO",
      "title": "Brief descriptive title of the issue",
      "start_marker": "First unique phrase that starts this issue (10-30 chars)",
      "end_marker": "Last unique phrase that ends this issue (10-30 chars)",
      "has_decision": true/false
    }},
    ...
  ]
}}

Find ALL issues in the document. Return ONLY the JSON object.
"""

        try:
            # max_tokens 증가: 10-40 Issues × 500자 + JSON 오버헤드 = 16K 필요
            # See: docs/phase-2/LLM_TOKEN_GUIDELINES.md
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=16000)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"JSON parse failed: {error}")
                return self._fallback_split(content)

            topics = parsed.get("topics", [])
            issues_data = parsed.get("issues", [])

            # start_marker/end_marker를 사용하여 실제 텍스트 추출
            issues_raw = []
            for issue in issues_data:
                issue_text = self._extract_issue_text(
                    content,
                    issue.get("start_marker", ""),
                    issue.get("end_marker", "")
                )
                if issue_text:
                    issues_raw.append({
                        "topic": issue.get("topic", ""),
                        "title": issue.get("title", ""),
                        "issue_text": issue_text,
                        "has_decision": issue.get("has_decision", False)
                    })

            return issues_raw, topics

        except Exception as e:
            logger.error(f"LLM boundary detection failed: {e}")
            return self._fallback_split(content)

    def _detect_boundaries_chunked(
        self,
        content: str,
        release: str,
        technology: str
    ) -> tuple[list[dict], list[str]]:
        """
        긴 텍스트를 청크로 나누어 처리
        """
        chunk_size = 12000
        overlap = 1000

        all_issues = []
        all_topics = set()

        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]

            # 청크 끝이 문장 중간이면 조정
            if end < len(content):
                last_period = chunk.rfind(". ")
                if last_period > chunk_size // 2:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1

            # 각 청크 처리
            issues, topics = self._detect_single_chunk(chunk, release, technology)
            all_issues.extend(issues)
            all_topics.update(topics)

            start = end - overlap if end < len(content) else len(content)

        return all_issues, list(all_topics)

    def _detect_single_chunk(
        self,
        chunk: str,
        release: str,
        technology: str
    ) -> tuple[list[dict], list[str]]:
        """단일 청크 처리"""
        prompt = f"""Analyze this portion of a 3GPP Maintenance section and identify issues.

Release: {release or "Unknown"}
Technology: {technology or "NR"}

Content:
{chunk}

Return JSON:
{{
  "topics": ["topic1", "topic2"],
  "issues": [
    {{"topic": "...", "title": "...", "start_marker": "...", "end_marker": "...", "has_decision": true/false}}
  ]
}}

Return ONLY the JSON.
"""
        try:
            # max_tokens 증가: 청크당 10-20 Issues × 500자 + JSON 오버헤드 = 8K 필요
            # See: docs/phase-2/LLM_TOKEN_GUIDELINES.md
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=8192)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                return [], []

            topics = parsed.get("topics", [])
            issues_raw = []

            for issue in parsed.get("issues", []):
                issue_text = self._extract_issue_text(
                    chunk,
                    issue.get("start_marker", ""),
                    issue.get("end_marker", "")
                )
                if issue_text:
                    issues_raw.append({
                        "topic": issue.get("topic", ""),
                        "title": issue.get("title", ""),
                        "issue_text": issue_text,
                        "has_decision": issue.get("has_decision", False)
                    })

            return issues_raw, topics

        except Exception as e:
            logger.warning(f"Chunk processing failed: {e}")
            return [], []

    def _extract_issue_text(
        self,
        content: str,
        start_marker: str,
        end_marker: str
    ) -> str:
        """
        마커를 사용하여 Issue 텍스트 추출

        NOTE: 이것은 단순 문자열 검색이며, semantic analysis가 아님
        """
        if not start_marker or not end_marker:
            return ""

        try:
            start_idx = content.find(start_marker)
            if start_idx == -1:
                # 대소문자 무시하여 재시도
                start_idx = content.lower().find(start_marker.lower())

            if start_idx == -1:
                return ""

            end_idx = content.find(end_marker, start_idx)
            if end_idx == -1:
                end_idx = content.lower().find(end_marker.lower(), start_idx)

            if end_idx == -1:
                # end_marker를 찾지 못하면 적당한 길이로 자르기
                end_idx = min(start_idx + 5000, len(content))

            return content[start_idx:end_idx + len(end_marker)]

        except Exception:
            return ""

    def _fallback_split(self, content: str) -> tuple[list[dict], list[str]]:
        """
        LLM 실패 시 전체 콘텐츠를 하나의 Issue로 반환

        NOTE: 제1 원칙에 따라 regex 기반 분할은 사용하지 않음
        """
        return [{
            "topic": "General",
            "title": "Maintenance Discussion",
            "issue_text": content,
            "has_decision": True
        }], ["General"]
