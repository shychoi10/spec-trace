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

        return f"""Format this complete Issue in Markdown.

Issue Number: {issue_number}
LS ID: {ls_id}
Title: {title}

Full Content:
{content}

Decision:
{decision}

Selected Tdocs:
{selected_tdocs}

Output Format (EXACT structure):
### Issue {issue_number}: {title}

**Origin**
- Type: `LS` (Incoming LS)
- LS ID: {ls_id}
- Source WG: [Extract from content - look for "from RAN2", "from RAN4", etc.]
- Source companies: [Extract from content if mentioned, otherwise "없음"]

**LS**
- {ls_id} — *{title}* ([Source WG], [Source companies if available]) — `ls_incoming`

**Summary**
[Korean summary of what this LS is about - 1-2 sentences explaining the technical topic]

**Relevant Tdocs**
{selected_tdocs}

**Decision**
{decision}

**Agenda Item**
- [Extract from Decision if mentioned (e.g., "discussed in agenda item 7.1.1.4.1"), otherwise "없음"]

**Issue Type**
- [Classify as one of:
  - "Actionable Issue" if Decision mentions "RAN1 response necessary" or "draft reply LS endorsed" or "discussed in agenda item"
  - "Non-action Issue" if Decision is "Noted" or "No further action necessary"
  - "Reference Issue" if for information only]

Generate the complete Issue Markdown now:
"""
