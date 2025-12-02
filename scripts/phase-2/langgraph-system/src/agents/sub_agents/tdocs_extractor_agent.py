"""
TdocsExtractorAgent: Tdocs 포괄 추출 Sub-Agent

개별 Issue를 입력받아 관련된 모든 Tdocs를 포괄적으로 추출 (Gemini 강점 활용)
"""

from typing import Dict, Any


class TdocsExtractorAgent:
    """모든 관련 Tdocs 추출 Agent (Comprehensive Extraction)"""

    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.agent_name = self.__class__.__name__

    def process(self, issue: Dict[str, Any]) -> str:
        """
        Issue와 관련된 모든 Tdocs 추출

        Args:
            issue: Single issue dict
                - ls_id: LS ID
                - title: LS title
                - content: Full LS text
                - decision_text: Decision text
                - has_tdocs: boolean

        Returns:
            Markdown text with ALL related Tdocs
        """
        ls_id = issue["ls_id"]
        has_tdocs = issue.get("has_tdocs", False)

        print(f"\n[{self.agent_name}] Extracting Tdocs for {ls_id}...")

        # has_tdocs=False면 빈 결과 반환
        if not has_tdocs:
            print(f"[{self.agent_name}] No Tdocs expected for {ls_id}")
            return "없음"

        prompt = self._build_prompt(issue)

        # LLM 호출 (Markdown 출력)
        response = self.llm.generate(prompt, temperature=0.1, max_tokens=3000)

        print(
            f"[{self.agent_name}] ✅ Extracted all Tdocs ({len(response)} chars)"
        )

        return response

    def _build_prompt(self, issue: Dict[str, Any]) -> str:
        """
        Dynamic prompt for comprehensive Tdoc extraction

        Args:
            issue: Issue dict

        Returns:
            LLM prompt
        """
        ls_id = issue["ls_id"]
        title = issue["title"]
        content = issue["content"]

        return f"""Find ALL Tdocs related to this Liaison Statement.

LS ID: {ls_id}
LS Title: {title}

Content:
{content}

Task:
1. Find ALL Discussion Tdocs with titles mentioning this LS topic
   - Look for "Discussion on [Topic]" or "Discussion on LS on [Topic]"
   - Include merged/joint discussions (multiple companies listed)
   - These are usually listed BEFORE "Decision:" section

2. Find ALL Draft Reply LS Tdocs
   - Look for "[Draft] Reply LS to [Source WG] on [Topic]"
   - May be multiple versions (different companies, revisions)

Output Format (Markdown):
**All Discussion Tdocs**
- R1-XXXXXXX — [Full Tdoc title] — [Company1], [Company2], ... — `discussion`
- R1-XXXXXXX — [Full Tdoc title] — [Company1], [Company2], ... — `discussion`

**All Draft Reply LS**
- R1-XXXXXXX — [Draft] Reply LS to [Source WG] on [Topic] — [Company] — `ls_reply_draft`
- R1-XXXXXXX — [Draft] Reply LS to [Source WG] on [Topic] — [Company] — `ls_reply_draft`

CRITICAL: Be COMPREHENSIVE. List all potentially related Tdocs.
Extract full metadata (Tdoc ID, complete title, all companies, tag).

Generate now:
"""
