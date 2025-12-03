"""
IssueTypeClassifierAgent: Issue Type을 분류하는 에이전트

Ground Truth의 Issue Type 분류:
- Incoming LS용: Actionable Issue, Non-action Issue, Reference Issue
- Maintenance용: SpecChange_FinalCR, Closed_Not_Pursued, Clarification_NoCR, 등

** 제1 원칙 준수 **
- 모든 분류는 LLM으로만 수행
- NO REGEX for semantic analysis
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent
from ...models import IssueType

logger = logging.getLogger(__name__)


class IssueTypeClassifierAgent(BaseAgent):
    """
    Issue를 분석하여 적절한 Issue Type 분류

    분류 기준:
    - Incoming LS: WG 액션 필요 여부로 분류
    - Maintenance: CR 결과 및 합의 내용으로 분류
    """

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Issue 텍스트를 분석하여 Issue Type 분류

        Args:
            state:
                - issue_text: Issue 원문
                - section_type: incoming_ls / maintenance
                - decision_text: Decision/Agreement 텍스트 (선택)
                - has_final_cr: Final CR 존재 여부 (선택)

        Returns:
            state with issue_type: IssueType
        """
        self.log_start("Issue type classification")

        issue_text = state.get("issue_text", "")
        section_type = state.get("section_type", "maintenance")
        decision_text = state.get("decision_text", "")
        has_final_cr = state.get("has_final_cr", False)

        issue_type = self._classify_with_llm(
            issue_text, section_type, decision_text, has_final_cr
        )

        self.log_end(f"Issue type classification: {issue_type}")
        return {**state, "issue_type": issue_type}

    def _classify_with_llm(
        self,
        issue_text: str,
        section_type: str,
        decision_text: str,
        has_final_cr: bool
    ) -> IssueType:
        """
        LLM을 사용하여 Issue Type 분류 (제1 원칙 준수)
        """
        # Section type에 따라 다른 분류 체계 사용
        if section_type == "incoming_ls":
            return self._classify_incoming_ls(issue_text, decision_text)
        else:
            return self._classify_maintenance(
                issue_text, decision_text, has_final_cr
            )

    def _classify_incoming_ls(
        self,
        issue_text: str,
        decision_text: str
    ) -> IssueType:
        """
        Incoming LS용 Issue Type 분류
        """
        prompt = f"""You are a 3GPP Liaison Statement analyzer. Classify this incoming LS issue.

## Issue Types for Incoming LS
- Actionable Issue: The WG needs to take action (create CR, reply LS, technical work)
- Non-action Issue: Information received but no immediate action required
- Reference Issue: CC-only, for reference/information only

## Issue Text
{issue_text[:3000]}

## Decision/Agreement (if any)
{decision_text[:1000] if decision_text else "No decision recorded"}

## Classification Criteria
1. **Actionable Issue**: Contains words like "needs", "should", "request", "action required", or discussion leads to work items
2. **Non-action Issue**: Information noted, no specific action, "noted", "no comment"
3. **Reference Issue**: CC (copy for info), no discussion, purely informational

## Output
Return ONLY ONE of: "Actionable Issue", "Non-action Issue", "Reference Issue"
"""

        try:
            # max_tokens 증가: Issue Type 분류 응답이 잘릴 수 있음
            # See: docs/phase-2/LLM_TOKEN_GUIDELINES.md
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=512)
            response = response.strip().strip('"').strip("'")

            # 매핑
            if "Actionable" in response:
                return IssueType.ACTIONABLE
            elif "Non-action" in response or "Non action" in response:
                return IssueType.NON_ACTION
            elif "Reference" in response:
                return IssueType.REFERENCE
            else:
                return IssueType.NON_ACTION  # 기본값

        except Exception as e:
            logger.error(f"LLM incoming LS classification failed: {e}")
            return IssueType.NON_ACTION

    def _classify_maintenance(
        self,
        issue_text: str,
        decision_text: str,
        has_final_cr: bool
    ) -> IssueType:
        """
        Maintenance용 Issue Type 분류
        """
        prompt = f"""You are a 3GPP Maintenance issue analyzer. Classify this maintenance issue.

## Issue Types for Maintenance
1. SpecChange_FinalCR: Final CR approved, specification will be changed
2. SpecChange_AlignmentCR: Alignment CR (typically Cat F/A for consistency)
3. Closed_Not_Pursued: Issue discussed but closed without CR (not pursued)
4. Clarification_NoCR: Clarification provided but no CR needed
5. Open_Inconclusive: No consensus reached, issue remains open
6. LS_Reply_Issue: Reply LS was created/approved for this issue
7. LS_Reply_Issue_PartialConsensus: Partial consensus reached for LS reply
8. UE_Feature_Definition: UE feature definition/capability related
9. UE_Feature_Clarification: UE feature clarification/interpretation

## Issue Text
{issue_text[:3000]}

## Decision/Agreement Text
{decision_text[:1500] if decision_text else "No decision recorded"}

## Has Final CR: {has_final_cr}

## Classification Rules
- If Final CR is approved/agreed → SpecChange_FinalCR
- If alignment CR or Cat F correction → SpecChange_AlignmentCR
- If "not pursued", "no consensus to change", "nothing broken" → Closed_Not_Pursued
- If clarification provided without spec change → Clarification_NoCR
- If no conclusion, FFS, postponed → Open_Inconclusive
- If Reply LS created → LS_Reply_Issue
- If UE feature related → UE_Feature_Definition or UE_Feature_Clarification

## Output
Return ONLY ONE of the issue type values exactly as listed above.
"""

        try:
            # max_tokens 증가: Maintenance Issue Type 분류 응답이 잘릴 수 있음
            # See: docs/phase-2/LLM_TOKEN_GUIDELINES.md
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=512)
            response = response.strip().strip('"').strip("'")

            # 매핑
            type_mapping = {
                "SpecChange_FinalCR": IssueType.SPEC_CHANGE_FINAL_CR,
                "SpecChange_AlignmentCR": IssueType.SPEC_CHANGE_ALIGNMENT_CR,
                "Closed_Not_Pursued": IssueType.CLOSED_NOT_PURSUED,
                "Clarification_NoCR": IssueType.CLARIFICATION_NO_CR,
                "Open_Inconclusive": IssueType.OPEN_INCONCLUSIVE,
                "LS_Reply_Issue": IssueType.LS_REPLY_ISSUE,
                "LS_Reply_Issue_PartialConsensus": IssueType.LS_REPLY_PARTIAL_CONSENSUS,
                "UE_Feature_Definition": IssueType.UE_FEATURE_DEFINITION,
                "UE_Feature_Clarification": IssueType.UE_FEATURE_CLARIFICATION,
                "UE_Feature_List_Consolidation": IssueType.UE_FEATURE_LIST_CONSOLIDATION,
            }

            # 정확한 매칭 시도
            for key, value in type_mapping.items():
                if key in response:
                    return value

            # Final CR 힌트 사용
            if has_final_cr:
                return IssueType.SPEC_CHANGE_FINAL_CR

            return IssueType.CLOSED_NOT_PURSUED  # 기본값

        except Exception as e:
            logger.error(f"LLM maintenance classification failed: {e}")
            if has_final_cr:
                return IssueType.SPEC_CHANGE_FINAL_CR
            return IssueType.CLOSED_NOT_PURSUED

    def classify_batch(
        self,
        issues: list[dict[str, Any]],
        section_type: str
    ) -> list[IssueType]:
        """
        여러 Issue를 배치로 분류

        Args:
            issues: Issue 리스트 (각각 issue_text, decision_text 포함)
            section_type: incoming_ls / maintenance

        Returns:
            IssueType 리스트
        """
        results = []
        for issue in issues:
            state = {
                "issue_text": issue.get("issue_text", ""),
                "section_type": section_type,
                "decision_text": issue.get("decision_text", ""),
                "has_final_cr": issue.get("has_final_cr", False)
            }
            result_state = self.process(state)
            results.append(result_state["issue_type"])

        return results
