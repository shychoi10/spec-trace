"""
SectionOverviewAgent: Section Overview 생성 Sub-Agent

모든 Issues를 분석하여 한국어 요약 + Statistics + Categories 생성
"""

from typing import List, Dict, Any


class SectionOverviewAgent:
    """Section Overview 생성 Agent"""

    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.agent_name = self.__class__.__name__

    def process(
        self,
        all_issues: List[Dict[str, Any]],
        meeting_number: str,
    ) -> str:
        """
        Section Overview Markdown 생성

        Args:
            all_issues: List of all issue dicts from IssueSplitter
            meeting_number: Meeting number

        Returns:
            Section Overview Markdown
        """
        print(
            f"\n[{self.agent_name}] Generating Section Overview for {len(all_issues)} LS..."
        )

        prompt = self._build_prompt(all_issues, meeting_number)

        # LLM 호출
        response = self.llm.generate(prompt, temperature=0.2, max_tokens=2000)

        print(f"[{self.agent_name}] ✅ Generated Section Overview")

        return response

    def _build_prompt(
        self, all_issues: List[Dict[str, Any]], meeting_number: str
    ) -> str:
        """
        Dynamic prompt for Section Overview

        Args:
            all_issues: All issue dicts
            meeting_number: Meeting number

        Returns:
            LLM prompt
        """
        # Primary vs CC-only 구분
        primary_issues = [i for i in all_issues if i.get("is_primary", True)]
        cc_only_issues = [i for i in all_issues if not i.get("is_primary", True)]

        # Issues 샘플 (처음 5개)
        issues_sample = "\n\n".join(
            [
                f"LS {i['ls_id']}: {i['title']}\nDecision: {i['decision_text']}"
                for i in all_issues[:5]
            ]
        )

        return f"""Create Section Overview for RAN1 #{meeting_number} Incoming Liaison Statements.

Total LS Items: {len(all_issues)}
- Primary LS Items (requiring RAN1 action): {len(primary_issues)}
- CC-only Items (RAN1 cc-ed, no action): {len(cc_only_issues)}

Sample of Issues:
{issues_sample}
...

(Total {len(all_issues)} LS items in this section)

Task:
1. Analyze all LS items
2. Extract Source Working Groups (from LS IDs and content)
3. Categorize by Release (Rel-17, Rel-18, Rel-19)
4. Identify "During the week" additions (if any pattern detected)
5. Write Korean summary paragraph

Output Format (EXACT structure):

# Incoming Liaison Statements (RAN1 #{meeting_number} Ground Truth)

## Section Overview

[Korean summary paragraph - 2-3 sentences describing:
 - What were the main topics discussed in these LS
 - Which Releases were involved
 - Which work items or technical areas were covered
 - Overall theme of the incoming LS]

**Statistics:**
- Total Primary LS Items: {len(primary_issues)}
- CC-only Items: {len(cc_only_issues)}
- Source Working Groups: [List unique source WGs like "RAN2, RAN3, RAN4, SA2"]

**Categories:**
- Rel-17 items: X개
- Rel-18 items: X개
- Rel-19 items: X개
- During the week additions: X개
- CC-only items: {len(cc_only_issues)}개

---

**Total: {len(primary_issues)} Issues**

---

Generate the Section Overview now:
"""
