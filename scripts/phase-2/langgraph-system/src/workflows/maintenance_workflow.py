"""
Maintenance Workflow - Generic Maintenance Section Processing (Ground Truth Format)

🚨 제1 원칙 (First Principles) 준수:
1. True Agentic AI: 모든 분석은 LLM이 수행 (No Regex)
2. Content-based Naming: Section 번호 없음
3. General Design: 하나의 워크플로우가 모든 Maintenance Section 처리
4. 기존 코드 보호: incoming_ls_workflow.py 영향 없음

이 워크플로우는 다음 Maintenance Section을 모두 처리합니다:
- Maintenance on Release 18
- Pre-Rel-18 NR Maintenance
- Pre-Rel-18 E-UTRA Maintenance

Ground Truth Output Format:
- Origin 블록
- Tdoc 분류 (Draft/Discussion, Moderator Summaries, LS, Final CRs)
- Summary (Korean)
- Decision / Agreement
- CR / Spec 메타데이터
- Agenda Item
- Issue Type

Flow:
    1. extract_overview: Section 개요 생성 (LLM)
    2. detect_issues: Issue 경계 감지 (LLM)
    3. process_issues: 각 Issue 처리 - Origin, Tdocs, CR Meta, Issue Type (LLM)
    4. generate_output: Ground Truth 형식 Markdown 출력 생성
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..models import (
    CRMetadata,
    DecisionType,
    DocType,
    IssueOrigin,
    IssueType,
    MaintenanceIssue,
    MaintenanceSectionOutput,
    OriginType,
    SectionMetadata,
    TdocWithType,
    TopicSection,
)
from ..utils.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class MaintenanceState(TypedDict):
    """Maintenance Workflow State (Ground Truth Format)"""

    # Input
    section_text: str
    section_metadata: Optional[SectionMetadata]
    meeting_number: str

    # Parsed data
    overview: str
    issues_raw: list[dict]  # Raw issue data from boundary detection
    issues: list[MaintenanceIssue]  # Ground Truth format issues

    # Output
    section_output: Optional[MaintenanceSectionOutput]
    markdown_output: str

    # Metadata
    confidence_score: float
    processing_notes: list[str]


class MaintenanceWorkflow:
    """
    범용 Maintenance Workflow (Ground Truth Format)

    🚨 General Design 원칙:
    - 하나의 워크플로우가 모든 Maintenance Section 처리
    - Release, Technology는 SectionMetadata로 전달
    - Section 번호 하드코딩 없음

    Output Format: Ground Truth 형식 (MaintenanceIssue)
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: 설정 딕셔너리 (domain_hints 등)
        """
        self.config = config or {}
        self.llm = LLMManager()
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph 빌드 (Ground Truth 파이프라인)"""
        workflow = StateGraph(MaintenanceState)

        # 노드 추가
        workflow.add_node("extract_overview", self._extract_overview)
        workflow.add_node("detect_issues", self._detect_issues)
        workflow.add_node("process_issues", self._process_issues)
        workflow.add_node("generate_output", self._generate_output)

        # Edge 추가
        workflow.set_entry_point("extract_overview")
        workflow.add_edge("extract_overview", "detect_issues")
        workflow.add_edge("detect_issues", "process_issues")
        workflow.add_edge("process_issues", "generate_output")
        workflow.add_edge("generate_output", END)

        return workflow.compile()

    def _extract_overview(self, state: MaintenanceState) -> MaintenanceState:
        """Step 1: Section 개요 생성"""
        section_text = state.get("section_text", "")
        metadata = state.get("section_metadata")

        release_info = metadata.release if metadata and metadata.release else ""
        tech_info = metadata.technology if metadata and metadata.technology else ""

        prompt = f"""You are analyzing a 3GPP Maintenance section.

**Context**:
Release: {release_info or "Unknown"}
Technology: {tech_info or "NR"}

**Section Content** (first 5000 chars):
{section_text[:5000]}

**Task**: Generate a concise Korean summary (overview).

**Instructions**:
1. Summarize the main topics/issues covered
2. Note significant CR approvals
3. Keep it 3-5 sentences in Korean

**Response Format** (JSON):
{{
    "overview_ko": "한국어 요약...",
    "main_topics": ["Topic1", "Topic2", ...]
}}

Return ONLY valid JSON."""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=2000)
            success, data, error = self._parse_json_response(response)

            if success:
                state["overview"] = data.get("overview_ko", "")
                state["processing_notes"] = [f"Overview: {len(data.get('main_topics', []))} topics"]
                logger.info(f"[Overview] Generated with {len(data.get('main_topics', []))} topics")
            else:
                state["overview"] = ""
                state["processing_notes"] = [f"Overview extraction failed: {error}"]

        except Exception as e:
            logger.error(f"[Overview] Failed: {e}")
            state["overview"] = ""
            state["processing_notes"] = [f"Overview extraction failed: {e}"]

        return state

    def _detect_issues(self, state: MaintenanceState) -> MaintenanceState:
        """Step 2: Issue 경계 감지 (Ground Truth 단위)"""
        section_text = state.get("section_text", "")
        metadata = state.get("section_metadata")

        release_info = metadata.release if metadata and metadata.release else "Unknown"
        tech_info = metadata.technology if metadata and metadata.technology else "NR"

        # 긴 텍스트 처리
        if len(section_text) > 20000:
            issues_raw = self._detect_issues_chunked(section_text, release_info, tech_info)
        else:
            issues_raw = self._detect_issues_single(section_text, release_info, tech_info)

        state["issues_raw"] = issues_raw
        state["processing_notes"].append(f"Detected {len(issues_raw)} issues")
        logger.info(f"[Issues] Detected {len(issues_raw)} issues")

        return state

    def _detect_issues_single(
        self, section_text: str, release: str, technology: str
    ) -> list[dict]:
        """단일 청크에서 Issue 감지"""
        prompt = f"""You are a 3GPP Maintenance section parser. Identify ALL individual maintenance issues.

**Context**:
Release: {release}
Technology: {technology}

**Section Content**:
{section_text[:25000]}

**Task**: Identify each maintenance issue as a separate unit.

**What constitutes an Issue**:
- A Draft CR submission and its discussion → Decision
- A technical question/clarification → Response/Agreement
- A feature proposal → Discussion → Outcome
- An LS reply discussion → Decision

**Instructions**:
1. Each issue should be self-contained
2. Include the issue title (what it's about)
3. Mark where the issue text starts and ends
4. Identify the topic (MIMO, NES, etc.)

**Response Format** (JSON):
{{
    "issues": [
        {{
            "title": "Issue brief title",
            "topic": "MIMO",
            "start_text": "First 30-50 chars that uniquely identify issue start",
            "end_text": "Last 30-50 chars that uniquely identify issue end",
            "has_cr": true/false,
            "has_decision": true/false
        }}
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=16384)
            success, data, error = self._parse_json_response(response)

            if not success:
                logger.warning(f"Issue detection JSON parse failed: {error}")
                # 부분 복구 시도
                data = self._partial_json_recovery(response)
                if not data or not data.get("issues"):
                    return [{"title": "General Discussion", "issue_text": section_text, "topic": "General"}]

            issues_raw = []
            for issue in data.get("issues", []):
                issue_text = self._extract_text_by_markers(
                    section_text,
                    issue.get("start_text", ""),
                    issue.get("end_text", "")
                )
                if issue_text:
                    issues_raw.append({
                        "title": issue.get("title", ""),
                        "topic": issue.get("topic", ""),
                        "issue_text": issue_text,
                        "has_cr": issue.get("has_cr", False),
                        "has_decision": issue.get("has_decision", False)
                    })

            return issues_raw if issues_raw else [{"title": "General Discussion", "issue_text": section_text, "topic": "General"}]

        except Exception as e:
            logger.error(f"Issue detection failed: {e}")
            return [{"title": "General Discussion", "issue_text": section_text, "topic": "General"}]

    def _detect_issues_chunked(
        self, section_text: str, release: str, technology: str
    ) -> list[dict]:
        """긴 텍스트를 청크로 나누어 처리"""
        chunk_size = 10000  # 줄임: 15000 → 10000
        overlap = 500
        all_issues = []

        start = 0
        chunk_num = 0
        while start < len(section_text):
            chunk_num += 1
            end = min(start + chunk_size, len(section_text))
            chunk = section_text[start:end]

            if end < len(section_text):
                # 문장 경계에서 자르기
                last_period = chunk.rfind(". ")
                if last_period > chunk_size // 2:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1

            logger.info(f"[Chunked] Processing chunk {chunk_num}: {len(chunk)} chars")
            issues = self._detect_issues_single(chunk, release, technology)

            # "General Discussion" 폴백은 청크 병합 시 제외
            filtered = [i for i in issues if i.get("title") != "General Discussion"]
            if filtered:
                all_issues.extend(filtered)
            elif not all_issues:
                # 첫 청크에서 아무것도 못 찾으면 폴백 유지
                all_issues.extend(issues)

            start = end - overlap if end < len(section_text) else len(section_text)

        return all_issues if all_issues else [{"title": "General Discussion", "issue_text": section_text, "topic": "General"}]

    def _process_issues(self, state: MaintenanceState) -> MaintenanceState:
        """Step 3: 각 Issue를 Ground Truth 형식으로 처리"""
        issues_raw = state.get("issues_raw", [])
        metadata = state.get("section_metadata")

        release = metadata.release if metadata and metadata.release else "Unknown"
        technology = metadata.technology if metadata and metadata.technology else "NR"
        section_title = f"{release} {technology} Maintenance" if release != "Unknown" else "Maintenance"

        issues = []
        for idx, issue_raw in enumerate(issues_raw):
            try:
                maintenance_issue = self._process_single_issue(
                    issue_raw,
                    section_title,
                    release,
                    technology,
                    idx + 1
                )
                issues.append(maintenance_issue)
            except Exception as e:
                logger.error(f"Failed to process issue {idx + 1}: {e}")

        state["issues"] = issues
        state["processing_notes"].append(f"Processed {len(issues)} issues to Ground Truth format")
        logger.info(f"[Process] Converted {len(issues)} issues to Ground Truth format")

        return state

    def _process_single_issue(
        self,
        issue_raw: dict,
        section_title: str,
        release: str,
        technology: str,
        issue_number: int
    ) -> MaintenanceIssue:
        """단일 Issue를 Ground Truth 형식으로 변환 (LLM 기반)"""
        issue_text = issue_raw.get("issue_text", "")
        issue_title = issue_raw.get("title", f"Issue {issue_number}")
        topic = issue_raw.get("topic", "General")

        prompt = f"""You are extracting structured information from a 3GPP maintenance issue.

**Issue Title**: {issue_title}
**Topic**: {topic}
**Section**: {section_title}
**Release**: {release}
**Technology**: {technology}

**Issue Content**:
{issue_text[:6000]}

**Task**: Extract all relevant information in Ground Truth format.

**Required Information**:
1. **Origin**: Type (Internal_Maintenance or From_LS), Section, Topic
2. **Tdocs**: Categorize all TDocs by type:
   - Draft/Discussion: Draft CRs, discussion papers
   - Moderator Summaries: FL summary, moderator summary documents
   - LS Related: Incoming LS, reply LS
   - Final CRs: Approved CRs
3. **Decision/Agreement**: The actual decision text (verbatim if possible)
4. **CR Metadata**: If CRs approved - release, spec, CR number, category
5. **Issue Type**: One of:
   - SpecChange_FinalCR: Final CR approved
   - Closed_Not_Pursued: Not pursued, nothing broken
   - Clarification_NoCR: Clarification only
   - Open_Inconclusive: No consensus
   - LS_Reply_Issue: LS reply created
6. **Summary_ko**: Korean summary (3-4 sentences)

**Response Format** (JSON):
{{
    "origin": {{
        "type": "Internal_Maintenance" or "From_LS",
        "section": "{section_title}",
        "topic": "{topic}",
        "from_ls": null or "R1-XXXXXXX"
    }},
    "tdocs": {{
        "draft_discussion": [
            {{"tdoc_id": "R1-XXXXXXX", "title": "...", "source": "Company", "doc_type": "cr_draft"}}
        ],
        "moderator_summaries": [],
        "ls_related": [],
        "final_crs": []
    }},
    "decision_text": "Actual decision/agreement text...",
    "decision_type": "Agreement" or "Decision" or "Conclusion",
    "cr_metadata": [
        {{"release": "Rel-18", "spec": "TS 38.214", "cr_id": "CR0656", "category": "Cat F", "tdoc_id": "R1-XXXXXXX"}}
    ],
    "issue_type": "SpecChange_FinalCR",
    "summary_ko": "한국어 요약...",
    "agenda_item": "Topic (Section)"
}}

Return ONLY valid JSON."""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=4096)
            success, data, error = self._parse_json_response(response)

            if not success:
                logger.warning(f"Issue processing JSON parse failed: {error}")
                return self._create_default_issue(issue_title, section_title, topic, issue_text)

            # Origin 생성
            origin_data = data.get("origin", {})
            try:
                origin_type = OriginType(origin_data.get("type", "Internal_Maintenance"))
            except ValueError:
                origin_type = OriginType.INTERNAL_MAINTENANCE

            origin = IssueOrigin(
                type=origin_type,
                section=origin_data.get("section", section_title),
                topic=origin_data.get("topic", topic),
                from_ls=origin_data.get("from_ls")
            )

            # Tdocs 파싱
            tdocs_data = data.get("tdocs", {})
            draft_discussion = self._parse_tdocs(tdocs_data.get("draft_discussion", []))
            moderator_summaries = self._parse_tdocs(tdocs_data.get("moderator_summaries", []))
            ls_related = self._parse_tdocs(tdocs_data.get("ls_related", []))
            final_crs = self._parse_tdocs(tdocs_data.get("final_crs", []))

            # Decision Type
            decision_type_str = data.get("decision_type", "").upper()
            if "AGREEMENT" in decision_type_str:
                decision_type = DecisionType.AGREEMENT
            elif "DECISION" in decision_type_str:
                decision_type = DecisionType.DECISION
            elif "CONCLUSION" in decision_type_str:
                decision_type = DecisionType.CONCLUSION
            else:
                decision_type = DecisionType.OTHER

            # CR Metadata
            cr_metadata = []
            for cr in data.get("cr_metadata", []):
                if cr.get("release"):
                    cr_metadata.append(CRMetadata(
                        release=cr.get("release", ""),
                        spec=cr.get("spec"),
                        work_item=cr.get("work_item"),
                        cr_id=cr.get("cr_id"),
                        category=cr.get("category"),
                        tdoc_id=cr.get("tdoc_id")
                    ))

            # Issue Type
            issue_type_str = data.get("issue_type", "")
            issue_type = self._parse_issue_type(issue_type_str, len(final_crs) > 0)

            return MaintenanceIssue(
                issue_title=issue_title,
                origin=origin,
                draft_discussion_tdocs=draft_discussion,
                moderator_summaries=moderator_summaries,
                ls_related_tdocs=ls_related,
                final_crs=final_crs,
                summary_ko=data.get("summary_ko", ""),
                decision_text=data.get("decision_text", ""),
                decision_type=decision_type,
                cr_metadata=cr_metadata,
                agenda_item=data.get("agenda_item", f"{topic} ({section_title})"),
                issue_type=issue_type,
                confidence_score=0.8,
                raw_text=issue_text
            )

        except Exception as e:
            logger.error(f"Issue processing failed: {e}")
            return self._create_default_issue(issue_title, section_title, topic, issue_text)

    def _parse_tdocs(self, tdocs_data: list) -> list[TdocWithType]:
        """Tdoc 데이터를 TdocWithType으로 변환"""
        result = []
        for t in tdocs_data:
            try:
                doc_type = DocType(t.get("doc_type", "other"))
            except ValueError:
                doc_type = DocType.OTHER

            result.append(TdocWithType(
                tdoc_id=t.get("tdoc_id", ""),
                title=t.get("title", ""),
                source=t.get("source", ""),
                doc_type=doc_type
            ))
        return result

    def _parse_issue_type(self, issue_type_str: str, has_final_cr: bool) -> IssueType:
        """Issue Type 문자열을 IssueType enum으로 변환"""
        type_mapping = {
            "SpecChange_FinalCR": IssueType.SPEC_CHANGE_FINAL_CR,
            "SpecChange_AlignmentCR": IssueType.SPEC_CHANGE_ALIGNMENT_CR,
            "Closed_Not_Pursued": IssueType.CLOSED_NOT_PURSUED,
            "Clarification_NoCR": IssueType.CLARIFICATION_NO_CR,
            "Open_Inconclusive": IssueType.OPEN_INCONCLUSIVE,
            "LS_Reply_Issue": IssueType.LS_REPLY_ISSUE,
            "UE_Feature_Definition": IssueType.UE_FEATURE_DEFINITION,
            "UE_Feature_Clarification": IssueType.UE_FEATURE_CLARIFICATION,
        }

        for key, value in type_mapping.items():
            if key in issue_type_str:
                return value

        return IssueType.SPEC_CHANGE_FINAL_CR if has_final_cr else IssueType.CLOSED_NOT_PURSUED

    def _create_default_issue(
        self, title: str, section_title: str, topic: str, issue_text: str
    ) -> MaintenanceIssue:
        """기본 Issue 생성 (LLM 실패 시)"""
        return MaintenanceIssue(
            issue_title=title,
            origin=IssueOrigin(
                type=OriginType.INTERNAL_MAINTENANCE,
                section=section_title,
                topic=topic
            ),
            draft_discussion_tdocs=[],
            moderator_summaries=[],
            ls_related_tdocs=[],
            final_crs=[],
            summary_ko="",
            decision_text="",
            decision_type=DecisionType.OTHER,
            cr_metadata=[],
            agenda_item=f"{topic} ({section_title})",
            issue_type=IssueType.CLOSED_NOT_PURSUED,
            confidence_score=0.3,
            raw_text=issue_text
        )

    def _generate_output(self, state: MaintenanceState) -> MaintenanceState:
        """Step 4: Ground Truth 형식 Markdown 출력 생성"""
        metadata = state.get("section_metadata")
        meeting_number = state.get("meeting_number", "unknown")
        overview = state.get("overview", "")
        issues = state.get("issues", [])

        # Section 제목 생성
        release = metadata.release if metadata and metadata.release else ""
        technology = metadata.technology if metadata and metadata.technology else ""

        if release:
            section_title = f"Maintenance on {release}"
            if technology:
                section_title = f"{release} {technology} Maintenance"
        else:
            section_title = "Maintenance"

        # 통계 계산
        stats = self._calculate_statistics(issues)

        # TopicSection 생성 (issues를 topic별로 그룹화)
        topics = self._group_issues_by_topic(issues)

        # MaintenanceSectionOutput 생성
        section_output = MaintenanceSectionOutput(
            section_title=section_title,
            meeting_number=meeting_number,
            release=release,
            technology=technology,
            overview=overview,
            topics=topics,
            issues=issues,
            statistics=stats,
        )

        state["section_output"] = section_output

        # Markdown 생성
        markdown_output = self._generate_ground_truth_markdown(
            issues, section_title, meeting_number, overview, stats
        )
        state["markdown_output"] = markdown_output

        logger.info(f"[Output] Generated {len(markdown_output)} chars of Ground Truth Markdown")
        return state

    def _calculate_statistics(self, issues: list[MaintenanceIssue]) -> dict:
        """통계 계산"""
        total_crs = sum(len(i.final_crs) for i in issues)
        specs_affected = set()
        for issue in issues:
            for cr in issue.cr_metadata:
                if cr.spec:
                    specs_affected.add(cr.spec)

        issue_type_counts = {}
        for issue in issues:
            if issue.issue_type:
                type_name = str(issue.issue_type)
                issue_type_counts[type_name] = issue_type_counts.get(type_name, 0) + 1

        return {
            "total_issues": len(issues),
            "total_crs_approved": total_crs,
            "specs_affected": list(specs_affected),
            "issue_type_distribution": issue_type_counts,
        }

    def _group_issues_by_topic(self, issues: list[MaintenanceIssue]) -> list[TopicSection]:
        """Issue들을 Topic별로 그룹화"""
        topic_map = {}
        for issue in issues:
            topic_name = issue.origin.topic or "General"
            if topic_name not in topic_map:
                topic_map[topic_name] = []
            topic_map[topic_name].append(issue)

        topics = []
        for name, issue_list in topic_map.items():
            topics.append(TopicSection(
                name=name,
                issues=issue_list,
                total_items=len(issue_list)
            ))

        return topics

    def _generate_ground_truth_markdown(
        self,
        issues: list[MaintenanceIssue],
        section_title: str,
        meeting_number: str,
        overview: str,
        stats: dict
    ) -> str:
        """Ground Truth 형식 Markdown 생성"""
        lines = [
            f"# {section_title} (RAN1 #{meeting_number})",
            "",
            "## Section Overview",
            "",
            overview if overview else "*(Overview not available)*",
            "",
            "**Statistics:**",
            f"- Total Issues: {stats.get('total_issues', 0)}",
            f"- CRs Approved: {stats.get('total_crs_approved', 0)}",
        ]

        specs = stats.get('specs_affected', [])
        if specs:
            lines.append(f"- Specs Affected: {', '.join(specs)}")

        lines.extend(["", "---", ""])

        # 각 Issue를 Ground Truth 형식으로 출력
        for idx, issue in enumerate(issues, 1):
            lines.append(f"### Issue {idx}: {issue.issue_title}")
            lines.append("")
            lines.append(issue.to_markdown())
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _extract_text_by_markers(self, content: str, start: str, end: str) -> str:
        """마커를 사용하여 텍스트 추출"""
        if not start or not end:
            return ""

        try:
            start_idx = content.find(start)
            if start_idx == -1:
                start_idx = content.lower().find(start.lower())
            if start_idx == -1:
                return ""

            end_idx = content.find(end, start_idx + len(start))
            if end_idx == -1:
                end_idx = content.lower().find(end.lower(), start_idx + len(start))
            if end_idx == -1:
                end_idx = min(start_idx + 5000, len(content))

            return content[start_idx:end_idx + len(end)]
        except Exception:
            return ""

    def _parse_json_response(self, response: str) -> tuple[bool, dict, str]:
        """JSON 응답 파싱"""
        try:
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            data = json.loads(response)
            return True, data, ""
        except json.JSONDecodeError as e:
            return False, {}, f"JSON parse error: {e}"
        except Exception as e:
            return False, {}, f"Unexpected error: {e}"

    def _partial_json_recovery(self, response: str) -> dict:
        """잘린 JSON에서 부분 복구 시도"""
        try:
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1]
                if "```" in response:
                    response = response.split("```")[0]
                response = response.strip()
            elif "```" in response:
                response = response.split("```")[1]
                if "```" in response:
                    response = response.split("```")[0]
                response = response.strip()

            # 마지막 완전한 객체 찾기
            # "issues": [ {}, {}, {} 에서 마지막 완전한 {} 까지만 파싱
            last_complete_brace = response.rfind("}")
            if last_complete_brace == -1:
                return {}

            # 가장 가까운 닫는 대괄호 찾기
            last_bracket = response.rfind("]", 0, last_complete_brace)
            if last_bracket == -1:
                # ] 가 없으면 마지막 } 뒤에 ]} 추가
                truncated = response[:last_complete_brace + 1] + "]}"
            else:
                truncated = response[:last_bracket + 1] + "}"

            try:
                data = json.loads(truncated)
                logger.info(f"[Recovery] Partially recovered JSON with {len(data.get('issues', []))} issues")
                return data
            except json.JSONDecodeError:
                # 더 공격적인 복구: 마지막 완전한 객체까지
                # { ... "issues": [ {...}, {...} 형태에서 복구
                last_obj_end = response.rfind("},")
                if last_obj_end > 0:
                    truncated = response[:last_obj_end + 1] + "]}"
                    try:
                        data = json.loads(truncated)
                        logger.info(f"[Recovery] Aggressively recovered JSON with {len(data.get('issues', []))} issues")
                        return data
                    except json.JSONDecodeError:
                        pass

                return {}

        except Exception as e:
            logger.warning(f"[Recovery] Partial JSON recovery failed: {e}")
            return {}

    def run(
        self,
        section_text: str,
        section_metadata: Optional[SectionMetadata] = None,
        meeting_number: str = "unknown",
    ) -> MaintenanceState:
        """
        Workflow 실행

        Args:
            section_text: Section 전체 텍스트
            section_metadata: Section 메타데이터 (release, technology)
            meeting_number: 미팅 번호

        Returns:
            최종 state (Ground Truth 형식)
        """
        initial_state: MaintenanceState = {
            "section_text": section_text,
            "section_metadata": section_metadata,
            "meeting_number": meeting_number,
            "overview": "",
            "issues_raw": [],
            "issues": [],
            "section_output": None,
            "markdown_output": "",
            "confidence_score": 0.0,
            "processing_notes": [],
        }

        release_info = section_metadata.release if section_metadata else "unknown"
        tech_info = section_metadata.technology if section_metadata else ""

        logger.info(f"[Workflow] Starting Maintenance processing (Ground Truth): {release_info} {tech_info}")

        result = self.app.invoke(initial_state)

        logger.info(f"[Workflow] Completed with {len(result.get('issues', []))} issues (Ground Truth)")

        return result

    def run_and_save(
        self,
        section_text: str,
        output_path: str,
        section_metadata: Optional[SectionMetadata] = None,
        meeting_number: str = "unknown",
    ) -> MaintenanceState:
        """
        Workflow 실행 및 결과 저장

        Args:
            section_text: Section 전체 텍스트
            output_path: 출력 Markdown 파일 경로
            section_metadata: Section 메타데이터
            meeting_number: 미팅 번호

        Returns:
            최종 state
        """
        result = self.run(section_text, section_metadata, meeting_number)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.get("markdown_output", ""))

        logger.info(f"[Workflow] Saved Ground Truth output to: {output_path}")

        return result


def create_maintenance_workflow(config: Optional[dict] = None) -> MaintenanceWorkflow:
    """Maintenance Workflow 팩토리 함수"""
    return MaintenanceWorkflow(config)
