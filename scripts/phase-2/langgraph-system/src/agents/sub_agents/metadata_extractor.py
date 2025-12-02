"""
MetadataExtractor Sub-Agent

각 Issue에서 메타데이터를 추출합니다:
- LS ID, Source WG, Source Companies
- Title, Decision

True Agentic AI: 모든 추출은 LLM이 수행
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class MetadataExtractor(BaseAgent):
    """메타데이터 추출 Sub-Agent"""

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.section_hints = self.config.get("incoming_ls_hints", {})

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Issue 텍스트에서 메타데이터 추출

        Args:
            state: LangGraph state
                - issue_text: 단일 Issue의 텍스트
                - boundary: 경계 정보

        Returns:
            업데이트된 state
                - metadata: 추출된 메타데이터
        """
        issue_text = state.get("issue_text", "")
        boundary = state.get("boundary", {})

        self.log_start(f"Metadata extraction for {boundary.get('ls_id', 'unknown')}")

        result = self._extract_metadata(issue_text, boundary)

        if result.success:
            state["extracted_metadata"] = result.output
            state["metadata_confidence"] = result.confidence_score
            self.log_end("Metadata extraction", success=True)
        else:
            state["extracted_metadata"] = {}
            state["metadata_confidence"] = 0.0
            self.log_end("Metadata extraction", success=False)

        return state

    def _extract_metadata(
        self, issue_text: str, boundary: dict
    ) -> AgentResult:
        """
        LLM을 사용하여 메타데이터 추출

        Args:
            issue_text: Issue 텍스트
            boundary: 경계 정보

        Returns:
            AgentResult with metadata dict
        """
        metadata_hints = self.section_hints.get("metadata_extraction", {})

        prompt = f"""You are extracting metadata from a 3GPP Liaison Statement item.

**Domain Knowledge Hints:**
{json.dumps(metadata_hints, indent=2)}

**Issue Text:**
{issue_text[:8000]}

**Known Information:**
- LS ID hint: {boundary.get('ls_id', 'unknown')}
- Is Primary: {boundary.get('is_primary', True)}

**Instructions:**
Extract the following metadata fields from the text:

1. **ls_id**: The document identifier (extract the exact ID from the text)
2. **title**: The title of the Liaison Statement
3. **source_wg**: The Working Group that sent this LS (e.g., RAN2, RAN3, SA2)
4. **source_companies**: List of companies associated with this LS (if mentioned)
5. **decision**: The decision or outcome for this LS item
6. **agenda_item**: Related agenda item (if mentioned, e.g., "AI 8.1", "9.1.4")
7. **is_primary**: Whether RAN1 is the primary recipient (true) or CC-ed (false)

**IMPORTANT:**
- Return ONLY a single JSON object, NOT an array
- Extract the LS ID exactly as it appears in the text

Return as JSON:
{{
  "ls_id": "<exact ID from text>",
  "title": "...",
  "source_wg": "RAN2",
  "source_companies": ["Company1", "Company2"],
  "decision": "...",
  "agenda_item": "8.1" or null,
  "is_primary": true,
  "confidence": 0.0-1.0
}}
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=1500)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"[MetadataExtractor] JSON parse failed: {error}")
                return AgentResult(
                    success=False,
                    output={},
                    confidence_score=0.0,
                    error_message=error,
                )

            # JSON 응답 안정화: list인 경우 첫 번째 요소 사용
            parsed = self._normalize_json_response(parsed)

            confidence = parsed.get("confidence", 0.7)

            # 필수 필드 검증
            required_fields = ["ls_id", "title", "decision"]
            field_score, notes = self.validate_required_fields(parsed, required_fields)

            # 종합 신뢰도
            final_confidence = (confidence + field_score) / 2

            return AgentResult(
                success=True,
                output=parsed,
                confidence_score=final_confidence,
                validation_notes=notes,
            )

        except Exception as e:
            logger.error(f"[MetadataExtractor] LLM call failed: {e}")
            return AgentResult(
                success=False,
                output={},
                confidence_score=0.0,
                error_message=str(e),
            )

    def _normalize_json_response(self, parsed: Any) -> dict:
        """
        LLM JSON 응답 정규화 - list인 경우 dict로 변환

        Args:
            parsed: 파싱된 JSON (dict 또는 list)

        Returns:
            정규화된 dict
        """
        # list인 경우 첫 번째 요소 사용
        if isinstance(parsed, list):
            if len(parsed) > 0:
                parsed = parsed[0]
            else:
                return {}

        # dict가 아닌 경우 빈 dict 반환
        if not isinstance(parsed, dict):
            return {}

        return parsed

    def extract_batch(
        self, issues_text: list[tuple[str, dict]]
    ) -> list[dict]:
        """
        여러 Issue의 메타데이터를 일괄 추출

        Args:
            issues_text: (issue_text, boundary) 튜플 리스트

        Returns:
            메타데이터 리스트
        """
        results = []
        for issue_text, boundary in issues_text:
            result = self._extract_metadata(issue_text, boundary)
            if result.success:
                results.append(result.output)
            else:
                # 실패 시 기본값
                results.append({
                    "ls_id": boundary.get("ls_id", "unknown"),
                    "title": boundary.get("title_snippet", ""),
                    "decision": "",
                    "error": result.error_message,
                })
        return results
