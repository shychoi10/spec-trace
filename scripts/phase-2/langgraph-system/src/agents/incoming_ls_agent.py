"""
Incoming LS Agent: True Agentic AI Orchestrator

이제 266줄 프롬프트 대신, 5개의 Sub-Agent를 조율합니다:
1. IssueSplitter → Issue 경계 식별
2. TdocsExtractor → 모든 Tdocs 추출 (Gemini 강점)
3. TdocsSelector → 1-3개 선택 (Dynamic Prompting)
4. IssueFormatter → Markdown 생성
5. SectionOverview → 전체 요약

True Agentic AI: 정규식 사용 금지, 모든 분석은 LLM이 수행
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from .sub_agents import (
    IssueSplitterAgent,
    TdocsExtractorAgent,
    TdocsSelectorAgent,
    IssueFormatterAgent,
    SectionOverviewAgent,
)


class IncomingLSAgent(BaseAgent):
    """Incoming LS 처리 Orchestrator Agent (True Agentic AI)"""

    # Incoming LS 감지용 키워드 (LLM 프롬프트에서 사용)
    KEYWORDS = [
        "LS on",
        "Reply LS",
        "incoming LS",
        "liaison statement",
        "LS to",
        "LS from",
    ]

    def __init__(self, llm_manager):
        super().__init__(llm_manager)

        # Sub-Agent 초기화
        print(f"[{self.agent_name}] Initializing Sub-Agents...")
        self.splitter = IssueSplitterAgent(llm_manager)
        self.extractor = TdocsExtractorAgent(llm_manager)
        self.selector = TdocsSelectorAgent(llm_manager)
        self.formatter = IssueFormatterAgent(llm_manager)
        self.overview_gen = SectionOverviewAgent(llm_manager)
        print(f"[{self.agent_name}] ✅ 5 Sub-Agents initialized")

    def detect_pattern(self, content: str) -> float:
        """
        Incoming LS 패턴 감지 점수 계산 (True Agentic AI - 키워드 기반)

        LLM 호출 비용을 줄이기 위해 단순 키워드 존재 여부만 확인합니다.
        실제 분류와 분석은 LLM이 수행합니다.

        Args:
            content: 분석할 텍스트

        Returns:
            0.0-1.0 사이의 신뢰도 점수
        """
        content_lower = content.lower()
        matches = 0

        # 단순 키워드 존재 확인 (분류가 아닌 필터링 목적)
        for keyword in self.KEYWORDS:
            if keyword.lower() in content_lower:
                matches += 1

        # 키워드가 많이 발견될수록 높은 점수
        if matches > 0:
            return min(1.0, 0.3 + (matches * 0.2))
        return 0.0

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Incoming LS 처리 (True Agentic AI, 콘텐츠 기반)

        Args:
            state: LangGraph state
                - content: Incoming LS 텍스트 (콘텐츠 기반)
                - metadata: {meeting_number, ...}

        Returns:
            업데이트된 state
                - structured_output: 완전한 Markdown
                - agent_used: "IncomingLSAgent"
        """
        content = state.get("content", "")
        metadata = state.get("metadata", {})
        meeting_number = metadata.get("meeting_number", "Unknown")

        print(f"\n{'='*80}")
        print(f"[{self.agent_name}] Processing Incoming LS (True Agentic AI)")
        print(f"{'='*80}")

        # ========== Stage 1: Issue Splitting ==========
        print(f"\n🔹 Stage 1: Issue Splitting (LLM Autonomy)")
        all_issues = self.splitter.process(content, metadata)

        if not all_issues:
            print(f"[{self.agent_name}] ❌ No issues identified. Aborting.")
            state["structured_output"] = "# Error: No LS items identified"
            state["agent_used"] = self.agent_name
            return state

        # Primary vs CC-only 분리
        primary_issues = [i for i in all_issues if i.get("is_primary", True)]
        cc_only_issues = [i for i in all_issues if not i.get("is_primary", True)]

        print(
            f"[{self.agent_name}] Identified: {len(primary_issues)} Primary + {len(cc_only_issues)} CC-only"
        )

        # ========== Stage 2-4: Process Each Primary Issue ==========
        print(f"\n🔹 Stage 2-4: Processing {len(primary_issues)} Primary Issues")
        processed_issues: List[str] = []

        for idx, issue in enumerate(primary_issues, start=1):
            ls_id = issue["ls_id"]
            print(
                f"\n--- Processing Issue {idx}/{len(primary_issues)}: {ls_id} ---"
            )

            # Stage 2: Extract ALL Tdocs (Gemini 강점 활용)
            all_tdocs_markdown = self.extractor.process(issue)

            # Stage 3: Select 1-3 Tdocs (Dynamic Prompting)
            selected_tdocs_markdown = self.selector.process(
                issue, all_tdocs_markdown
            )

            # Stage 4: Format Issue (Markdown)
            issue_markdown = self.formatter.process(
                issue, selected_tdocs_markdown, idx
            )

            processed_issues.append(issue_markdown)

        # ========== Stage 5: Self-Validation (Moderate) ==========
        print(f"\n🔹 Stage 5: Self-Validation (Moderate)")
        validation_result = self._validate_issues(processed_issues)

        if not validation_result["valid"]:
            print(
                f"[{self.agent_name}] ⚠️  Validation warnings: {validation_result['errors']}"
            )
        else:
            print(f"[{self.agent_name}] ✅ Issues validated successfully")

        # ========== Stage 6: Section Overview ==========
        print(f"\n🔹 Stage 6: Section Overview Generation")
        section_overview = self.overview_gen.process(all_issues, meeting_number)

        # ========== Stage 7: CC-only Items (if any) ==========
        cc_only_markdown = ""
        if cc_only_issues:
            print(
                f"\n🔹 Stage 7: Formatting {len(cc_only_issues)} CC-only Items"
            )
            cc_only_markdown = self._format_cc_only_issues(cc_only_issues)

        # ========== Final Assembly ==========
        print(f"\n🔹 Final: Assembling Complete Markdown")
        final_output = (
            section_overview
            + "\n\n"
            + "\n\n".join(processed_issues)
            + "\n\n"
            + cc_only_markdown
        )

        # State 업데이트
        state["structured_output"] = final_output
        state["agent_used"] = self.agent_name

        print(f"\n{'='*80}")
        print(
            f"[{self.agent_name}] ✅ Processing Complete ({len(final_output)} chars)"
        )
        print(f"{'='*80}")

        return state

    def _validate_issues(self, issues: List[str]) -> Dict[str, Any]:
        """
        Moderate self-validation for processed Issues

        Args:
            issues: List of Issue Markdown strings

        Returns:
            {"valid": bool, "errors": [...], "warnings": [...]}
        """
        print(
            f"[{self.agent_name}] Validating {len(issues)} processed Issues..."
        )

        # 샘플로 첫 3개만 LLM에게 보여줌 (비용 절감)
        sample_issues = "\n\n".join(issues[:3]) + "\n\n... (more issues)"

        validation_prompt = f"""Validate these processed Issues for completeness.

Total Issues: {len(issues)}

Sample (first 3):
{sample_issues}

Check:
1. Do all Issues have required fields?
   - Origin (Type, LS ID, Source WG)
   - Summary (Korean)
   - Relevant Tdocs
   - Decision
   - Agenda Item
   - Issue Type

2. Are Issue numbers sequential (Issue 1, Issue 2, Issue 3...)?

3. Are Tdocs properly categorized with tags (`discussion`, `ls_reply_draft`)?

4. For Non-action Issues, are Tdocs "없음"?

Output (JSON):
{{
  "valid": true or false,
  "errors": ["error 1", "error 2"],
  "warnings": ["warning 1"]
}}

Generate validation result:
"""

        try:
            import json

            response = self.llm.generate(
                validation_prompt, temperature=0.0, max_tokens=1000
            )
            validation = json.loads(response)
            return validation
        except Exception as e:
            print(f"[{self.agent_name}] Validation LLM call failed: {e}")
            return {
                "valid": True,
                "errors": [],
                "warnings": ["Validation skipped due to error"],
            }

    def _format_cc_only_issues(
        self, cc_only_issues: List[Dict[str, Any]]
    ) -> str:
        """
        Format CC-only items section

        Args:
            cc_only_issues: List of CC-only issue dicts

        Returns:
            CC-only section Markdown
        """
        cc_markdown = "### RAN1 was cc-ed in the following incoming LSs\n\n"

        for issue in cc_only_issues:
            ls_id = issue["ls_id"]
            title = issue["title"]
            cc_markdown += f"#### {ls_id}: {title}\n\n"
            cc_markdown += f"**Decision:** {issue['decision_text']}\n\n"

        return cc_markdown
