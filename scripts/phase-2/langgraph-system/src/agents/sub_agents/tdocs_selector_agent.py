"""
TdocsSelectorAgent: Tdocs 선택적 필터링 Sub-Agent

Extractor가 추출한 모든 Tdocs 중 가장 중요한 1-3개만 선택 (Dynamic Prompting)

True Agentic AI: 정규식 사용 금지, 모든 분석은 LLM이 수행
"""

from typing import Dict, Any


class TdocsSelectorAgent:
    """중요 Tdocs 선택 Agent (Selective Filtering)"""

    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.agent_name = self.__class__.__name__

    def process(
        self, issue: Dict[str, Any], all_tdocs_markdown: str
    ) -> str:
        """
        추출된 모든 Tdocs 중 중요한 것만 선택

        Args:
            issue: Single issue dict
            all_tdocs_markdown: Extractor가 반환한 Markdown

        Returns:
            Selected Tdocs only (Markdown)
        """
        ls_id = issue["ls_id"]

        print(f"\n[{self.agent_name}] Selecting important Tdocs for {ls_id}...")

        # all_tdocs가 "없음"이면 그대로 반환
        if all_tdocs_markdown.strip() == "없음":
            print(f"[{self.agent_name}] No Tdocs to select")
            return "없음"

        prompt = self._build_dynamic_prompt(issue, all_tdocs_markdown)

        # LLM 호출 (결정론적)
        response = self.llm.generate(prompt, temperature=0.0, max_tokens=2000)

        print(
            f"[{self.agent_name}] ✅ Selected Tdocs ({len(response)} chars)"
        )

        return response

    def _build_dynamic_prompt(
        self, issue: Dict[str, Any], all_tdocs: str
    ) -> str:
        """
        Dynamic prompt with Decision-based branching

        Args:
            issue: Issue dict
            all_tdocs: All extracted Tdocs (Markdown)

        Returns:
            LLM prompt
        """
        ls_id = issue["ls_id"]
        title = issue["title"]
        decision = issue["decision_text"]

        prompt = f"""Select the MOST IMPORTANT Tdocs for this LS.

LS ID: {ls_id}
LS Title: {title}
Decision: {decision}

All Related Tdocs (from comprehensive extraction):
{all_tdocs}

Selection Rules:

"""

        # Dynamic branching based on Decision text (LLM will analyze)
        prompt += """Analyze the Decision text and determine:

1. If Decision is "Noted" or "No further action" → This is a Non-action Issue
   - Return: "없음"

2. Otherwise → This is an Actionable Issue. Select:
   - Discussion Tdocs: Select 1-3 MOST RELEVANT
     * Prefer MERGED discussions (many companies listed)
     * Prefer titles directly matching this LS topic
     * Exclude generic or tangentially related discussions

   - Draft Reply LS: Select EXACTLY ONE
     * If Decision mentions "endorsed as in R1-XXXXXXX", select that specific one
     * Otherwise, select the MOST RECENT or MERGED version
     * Usually marked "[Draft]" or "Moderator"
     * If multiple versions, prefer the one with most companies
"""

        prompt += """
Output Format (Markdown):
**Discussion (`discussion`)**
- R1-XXXXXXX — [Title] — [Companies] — `discussion`
- R1-XXXXXXX — [Title] — [Companies] — `discussion`

**Draft Reply LS (`ls_reply_draft`)**
- R1-XXXXXXX — [Draft] Reply LS to [WG] on [Topic] — [Company] — `ls_reply_draft`

Or just: "없음"

CRITICAL: Quality over quantity! Return ONLY the most important ones.

Generate now:
"""
        return prompt
