"""
IssueFormatterAgent: Issue Markdown 포맷팅 Sub-Agent

Issue dict + selected Tdocs를 입력받아 완전한 Issue Markdown 생성
"""

from typing import Dict, Any


class IssueFormatterAgent:
    """Issue Markdown 포맷팅 Agent"""

    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.agent_name = self.__class__.__name__

    def process(
        self,
        issue: Dict[str, Any],
        selected_tdocs_markdown: str,
        issue_number: int,
    ) -> str:
        """
        Complete Issue Markdown 생성

        Args:
            issue: Issue dict
            selected_tdocs_markdown: Selected Tdocs (Markdown)
            issue_number: Issue number (1, 2, 3, ...)

        Returns:
            Complete Issue Markdown
        """
        ls_id = issue["ls_id"]

        print(
            f"\n[{self.agent_name}] Formatting Issue {issue_number} ({ls_id})..."
        )

        prompt = self._build_prompt(issue, selected_tdocs_markdown, issue_number)

        # LLM 호출
        response = self.llm.generate(prompt, temperature=0.2, max_tokens=2000)

        print(
            f"[{self.agent_name}] ✅ Formatted Issue {issue_number}"
        )

        return response

    def _build_prompt(
        self, issue: Dict[str, Any], selected_tdocs: str, issue_number: int
    ) -> str:
        """
        Dynamic prompt for Issue formatting

        Args:
            issue: Issue dict
            selected_tdocs: Selected Tdocs (Markdown)
            issue_number: Issue number

        Returns:
            LLM prompt
        """
        ls_id = issue["ls_id"]
        title = issue["title"]
        content = issue["content"]
        decision = issue["decision_text"]
        source_wg = issue.get("source_wg", "Unknown")
        source_companies = issue.get("source_companies", [])

        # Format source companies for display
        if source_companies and len(source_companies) > 0:
            companies_str = "[" + ", ".join(source_companies) + "]"
        else:
            companies_str = "없음"

        return f"""Format this complete Issue in Markdown.

Issue Number: {issue_number}
LS ID: {ls_id}
Title: {title}
Source WG: {source_wg}
Source Companies: {companies_str}

Full Content:
{content}

Decision:
{decision}

Selected Tdocs:
{selected_tdocs}

Output Format (EXACT structure - use the provided Source WG and Source Companies):
### Issue {issue_number}: {title}

**Origin**
- Type: `LS` (Incoming LS)
- LS ID: {ls_id}
- Source WG: {source_wg}
- Source companies: {companies_str}

**LS**
- {ls_id} — *{title}* ({source_wg}, {companies_str}) — `ls_incoming`

**Summary**
[Korean summary of what this LS is about - 1-2 sentences explaining the technical topic]

**Relevant Tdocs**
{selected_tdocs}

**Decision**
{decision}

**Agenda Item**
- [Extract from Decision if mentioned (e.g., "discussed in agenda item 7.1.1.4.1"), otherwise "없음"]

**Issue Type**
- [Classify based on semantic analysis of Decision text:
  - "Actionable Issue" if Decision indicates response/action is required (e.g., reply LS needed, discussed in agenda item, input requested)
  - "Non-action Issue" if Decision indicates acknowledgment only (e.g., noted, no further action)
  - "Reference Issue" if for information only]

Generate the complete Issue Markdown now:
"""
