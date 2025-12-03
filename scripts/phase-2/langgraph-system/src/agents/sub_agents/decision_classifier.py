"""
DecisionClassifier Sub-Agent

Decision 텍스트를 기반으로 Issue Type을 분류합니다:
- Actionable Issue: RAN1 액션 필요
- Non-action Issue: 액션 불필요
- Reference Issue: CC-only

True Agentic AI: 모든 분류는 LLM이 수행
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent, AgentResult
from ...models import IssueType

logger = logging.getLogger(__name__)


class DecisionClassifier(BaseAgent):
    """Issue Type 분류 Sub-Agent"""

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.section_hints = self.config.get("incoming_ls_hints", {})

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Decision 텍스트를 기반으로 Issue Type 분류

        Args:
            state: LangGraph state
                - decision: Decision 텍스트
                - is_primary: Primary recipient 여부

        Returns:
            업데이트된 state
                - issue_type: 분류된 Issue Type
        """
        decision = state.get("decision", "")
        is_primary = state.get("is_primary", True)

        self.log_start("Issue type classification")

        result = self._classify_issue_type(decision, is_primary)

        if result.success:
            state["issue_type"] = result.output
            state["classification_confidence"] = result.confidence_score
            self.log_end("Issue type classification", success=True)
        else:
            state["issue_type"] = IssueType.NON_ACTION
            state["classification_confidence"] = 0.0
            self.log_end("Issue type classification", success=False)

        return state

    def _classify_issue_type(
        self, decision: str, is_primary: bool
    ) -> AgentResult:
        """
        LLM을 사용하여 Issue Type 분류

        Args:
            decision: Decision 텍스트
            is_primary: Primary recipient 여부

        Returns:
            AgentResult with IssueType
        """
        issue_type_hints = self.section_hints.get("issue_type_classification", {})
        types_info = issue_type_hints.get("types", {})

        # Get critical distinction from hints
        critical_distinction = self.section_hints.get("issue_type_classification", {}).get(
            "critical_distinction", ""
        )

        prompt = f"""You are classifying a 3GPP Liaison Statement issue type.

**CRITICAL CLASSIFICATION RULES:**
{critical_distinction}

**IMPORTANT DISTINCTION:**
- "To be taken into account" → ALWAYS Reference Issue (NOT Actionable!)
- "To be handled/discussed" + "response necessary" → Actionable Issue
- "No further action" → Non-action Issue

**Actionable Issue** - RAN1 MUST respond/act:
{json.dumps(types_info.get('actionable', {}), indent=2)}

**Non-action Issue** - Explicitly no action needed:
{json.dumps(types_info.get('non_action', {}), indent=2)}

**Reference Issue** - For awareness/reference only:
{json.dumps(types_info.get('reference', {}), indent=2)}

**Decision Text to Classify:**
"{decision}"

**Additional Context:**
- Is RAN1 primary recipient: {is_primary}

**Classification Logic (apply in order):**
1. If "To be taken into account" appears → Reference Issue (even with agenda item!)
2. If "No further action" or "no action" appears → Non-action Issue
3. If "response necessary" or "response is necessary" AND "To be handled/discussed" → Actionable Issue
4. If RAN1 was CC-ed only (not primary) → Reference Issue
5. Default for unclear cases → Non-action Issue

Return your classification as JSON:
{{
  "issue_type": "Actionable Issue" | "Non-action Issue" | "Reference Issue",
  "reasoning": "brief explanation of which pattern matched",
  "confidence": 0.0-1.0
}}
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=1024)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"[DecisionClassifier] JSON parse failed: {error}")
                # 기본값 반환
                default_type = IssueType.REFERENCE if not is_primary else IssueType.NON_ACTION
                return AgentResult(
                    success=True,
                    output=default_type,
                    confidence_score=0.5,
                    validation_notes=[f"Parse failed, using default: {default_type}"],
                )

            # Issue Type 파싱
            type_str = parsed.get("issue_type", "Non-action Issue")
            confidence = parsed.get("confidence", 0.7)
            reasoning = parsed.get("reasoning", "")

            # 문자열을 IssueType으로 변환
            if "actionable" in type_str.lower():
                issue_type = IssueType.ACTIONABLE
            elif "reference" in type_str.lower():
                issue_type = IssueType.REFERENCE
            else:
                issue_type = IssueType.NON_ACTION

            return AgentResult(
                success=True,
                output=issue_type,
                confidence_score=confidence,
                validation_notes=[reasoning] if reasoning else [],
            )

        except Exception as e:
            logger.error(f"[DecisionClassifier] LLM call failed: {e}")
            default_type = IssueType.REFERENCE if not is_primary else IssueType.NON_ACTION
            return AgentResult(
                success=True,
                output=default_type,
                confidence_score=0.3,
                error_message=str(e),
            )

    def classify_batch(
        self, decisions: list[tuple[str, bool]]
    ) -> list[IssueType]:
        """
        여러 Decision을 일괄 분류

        Args:
            decisions: (decision_text, is_primary) 튜플 리스트

        Returns:
            IssueType 리스트
        """
        results = []
        for decision, is_primary in decisions:
            result = self._classify_issue_type(decision, is_primary)
            results.append(result.output)
        return results
