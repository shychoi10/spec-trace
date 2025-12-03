"""
LSAgent - Liaison Statement Section Agent

Incoming Liaison Statements 처리를 담당하는 Section Agent입니다.
Note: 콘텐츠 기반 처리 - Section 번호에 종속되지 않음

Architecture:
    LSAgent orchestrates 5 Sub-Agents:
    1. BoundaryDetector: Issue 경계 탐지
    2. MetadataExtractor: LS 메타데이터 추출
    3. TdocLinker: 관련 Tdoc 연결
    4. DecisionClassifier: Issue Type 분류
    5. SummaryGenerator: 한국어 요약 생성

True Agentic AI: 모든 분류/추출은 LLM이 수행
"""

import logging
from typing import Any, Optional

from ..base_agent import BaseAgent, AgentResult
from ..sub_agents import (
    BoundaryDetector,
    MetadataExtractor,
    TdocLinker,
    DecisionClassifier,
    SummaryGenerator,
)
from ...models import Issue, Origin, TdocRef, SectionOutput, CCOnlyItem
from ...models import IssueType, OriginType

logger = logging.getLogger(__name__)


class LSAgent(BaseAgent):
    """Incoming Liaison Statements 처리 Agent (콘텐츠 기반)"""

    def __init__(self, llm_manager, config: Optional[dict] = None):
        """
        Args:
            llm_manager: LLM 호출 매니저
            config: Agent 설정 (domain_hints 포함)
        """
        super().__init__(llm_manager, config)

        # Sub-Agents 초기화
        self.boundary_detector = BoundaryDetector(llm_manager, config)
        self.metadata_extractor = MetadataExtractor(llm_manager, config)
        self.tdoc_linker = TdocLinker(llm_manager, config)
        self.decision_classifier = DecisionClassifier(llm_manager, config)
        self.summary_generator = SummaryGenerator(llm_manager, config)

        # 콘텐츠 기반 처리 - Section 번호는 런타임에 결정
        self.section_number = self.config.get("section_number", None)

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Incoming LS 전체 처리 (콘텐츠 기반)

        Args:
            state: LangGraph state
                - section_text: Incoming LS 전체 텍스트
                - meeting_number: 미팅 번호

        Returns:
            업데이트된 state
                - section_output: SectionOutput 객체
                - issues: Issue 리스트
        """
        section_text = state.get("section_text", "")
        meeting_number = state.get("meeting_number", "unknown")

        self.log_start(f"Section {self.section_number} processing")

        # Step 1: Issue 경계 탐지
        self.log_progress("Step 1/6: Detecting issue boundaries")
        boundary_state = {"content": section_text, "metadata": {}}
        boundary_state = self.boundary_detector.process(boundary_state)

        # BoundaryDetector 결과 처리 (새 형식: dict with boundaries, cc_only_items)
        raw_boundaries = boundary_state.get("boundaries", {})

        # 새 형식과 구 형식 모두 지원
        if isinstance(raw_boundaries, dict):
            # 새 형식: {"boundaries": [...], "cc_only_items": [...]}
            boundaries = raw_boundaries.get("boundaries", [])
            detected_cc_only = raw_boundaries.get("cc_only_items", [])
        else:
            # 구 형식: 리스트 직접 반환
            boundaries = raw_boundaries if isinstance(raw_boundaries, list) else []
            detected_cc_only = []

        if not boundaries:
            logger.warning("[LSAgent] No boundaries detected")
            state["section_output"] = self._create_empty_output(meeting_number)
            state["issues"] = []
            self.log_end(f"Section {self.section_number} processing", success=False)
            return state

        self.log_progress(f"Found {len(boundaries)} primary issue boundaries, {len(detected_cc_only)} CC-only items")

        # Step 2: 각 Issue 처리
        issues = []
        cc_only_items = []

        for idx, boundary in enumerate(boundaries):
            self.log_progress(f"Step 2-5: Processing issue {idx + 1}/{len(boundaries)}")

            issue_result = self._process_single_issue(
                boundary=boundary,
                section_text=section_text,
                meeting_number=meeting_number,
                issue_index=idx + 1,
            )

            if issue_result:
                if issue_result.is_cc_only:
                    cc_only_items.append(
                        CCOnlyItem(
                            ls_id=issue_result.origin.ls_id or "",
                            title=issue_result.title,
                            decision=issue_result.decision,
                        )
                    )
                else:
                    issues.append(issue_result)

        # BoundaryDetector에서 감지한 CC-only 항목도 추가
        for cc_item in detected_cc_only:
            cc_only_items.append(
                CCOnlyItem(
                    ls_id=cc_item.get("ls_id", ""),
                    title=cc_item.get("title", "") or cc_item.get("title_snippet", ""),
                    decision="CC-only",
                )
            )

        # Step 6: Section Overview 생성 (LLM에 Issues 정보 전달)
        self.log_progress("Step 6/6: Generating section overview")

        # Issues 정보를 LLM에 전달할 형식으로 준비
        issues_info = []
        for issue in issues:
            issues_info.append({
                "title": issue.title,
                "source_wg": issue.origin.source_wg if issue.origin else "",
                "agenda_item": issue.agenda_item or "N/A",
            })

        overview_result = self.summary_generator.generate_section_overview(
            section_text=section_text,
            meeting_number=meeting_number,
            issue_count=len(issues) + len(cc_only_items),
            issues_info=issues_info,
        )

        overview_data = overview_result.output if overview_result.success else {}
        overview_text = overview_data.get("overview", "") if isinstance(overview_data, dict) else str(overview_data)
        source_wgs = overview_data.get("source_wgs", []) if isinstance(overview_data, dict) else []
        categories = overview_data.get("categories", {}) if isinstance(overview_data, dict) else {}

        # Statistics 계산
        statistics = self._calculate_statistics(issues, cc_only_items, source_wgs, categories)

        # SectionOutput 생성
        section_output = SectionOutput(
            section_number=self.section_number,
            meeting_number=meeting_number,
            overview=overview_text,
            issues=issues,
            cc_only_items=cc_only_items,
            statistics=statistics,
        )

        state["section_output"] = section_output
        state["issues"] = issues
        state["cc_only_items"] = cc_only_items

        self.log_end(
            f"Section {self.section_number} processing: {len(issues)} issues, {len(cc_only_items)} CC-only",
            success=True,
        )

        return state

    def _process_single_issue(
        self,
        boundary: dict[str, Any],
        section_text: str,
        meeting_number: str,
        issue_index: int,
    ) -> Optional[Issue]:
        """
        단일 Issue 처리 - BoundaryDetector가 이미 모든 데이터를 추출함

        Args:
            boundary: BoundaryDetector가 추출한 완전한 Issue 정보
            section_text: Section 전체 텍스트 (백업용)
            meeting_number: 미팅 번호
            issue_index: Issue 인덱스

        Returns:
            Issue 객체 또는 None
        """
        try:
            # BoundaryDetector가 이미 모든 정보를 추출함 - 직접 사용
            ls_id = boundary.get("ls_id", "")
            title = boundary.get("title", "") or boundary.get("title_snippet", "") or f"LS {ls_id}"
            source_wg = boundary.get("source_wg", "")
            source_companies = boundary.get("source_companies", [])
            decision = boundary.get("decision", "")
            agenda_item = boundary.get("agenda_item")
            is_primary = boundary.get("is_primary", True)

            # Issue Type 결정 (boundary에서 가져오거나 decision 텍스트 기반으로 결정)
            issue_type_str = boundary.get("issue_type", "")
            issue_type = self._determine_issue_type(issue_type_str, decision, is_primary)

            # Relevant Tdocs 변환 (boundary dict → TdocRef 객체)
            relevant_tdocs = self._convert_tdocs(boundary.get("relevant_tdocs", []))

            # 한국어 요약 생성 (간단한 LLM 호출)
            summary_ko = self._generate_simple_summary(title, decision, source_wg)

            # Origin 생성
            origin = Origin(
                type=OriginType.LS,
                section=self.section_number,
                ls_id=ls_id,
                source_wg=source_wg,
                source_companies=source_companies,
            )

            # Issue 생성
            issue = Issue(
                issue_id=f"Issue_{self.section_number}_{issue_index}",
                origin=origin,
                title=title,
                summary_ko=summary_ko,
                relevant_tdocs=relevant_tdocs,
                decision=decision,
                agenda_item=agenda_item,
                issue_type=issue_type,
                is_cc_only=not is_primary,
                confidence_score=boundary.get("confidence", 0.8),
            )

            return issue

        except Exception as e:
            logger.error(f"[LSAgent] Failed to process issue {issue_index}: {e}")
            return None

    def _determine_issue_type(
        self, type_str: str, decision: str, is_primary: bool
    ) -> IssueType:
        """
        Issue Type 결정 - BoundaryDetector 결과 우선 사용 (Phase B 최적화)

        BoundaryDetector가 이미 LLM으로 issue_type을 추출했으므로,
        그 결과를 우선 사용하여 중복 LLM 호출을 방지합니다.

        Args:
            type_str: BoundaryDetector가 반환한 issue_type 문자열
            decision: Decision 텍스트 (fallback용)
            is_primary: Primary recipient 여부

        Returns:
            IssueType enum
        """
        # CC-only는 항상 Reference (메타데이터 기반 판단)
        if not is_primary:
            return IssueType.REFERENCE

        # Phase B 최적화: BoundaryDetector 결과 우선 사용
        # BoundaryDetector가 이미 LLM으로 issue_type을 추출했으므로 재사용
        if type_str:
            type_lower = type_str.lower()
            if "actionable" in type_lower:
                return IssueType.ACTIONABLE
            elif "reference" in type_lower:
                return IssueType.REFERENCE
            elif "non" in type_lower:  # non_action, non-action
                return IssueType.NON_ACTION

        # BoundaryDetector 결과가 없을 때만 LLM 호출 (fallback)
        prompt = f"""Classify this 3GPP RAN1 Liaison Statement decision into one of three types.

Decision text: "{decision}"

Issue Types:
1. "actionable" - RAN1 needs to take action (response LS, CR, discussion required)
2. "non_action" - No action needed from RAN1 (information only, no further action)
3. "reference" - For reference only (to be taken into account, CC-only)

Rules:
- If decision says "To be taken into account" → reference
- If decision says "No further action" or "No action necessary" → non_action
- If decision requires RAN1 response, handling, or discussion → actionable
- If uncertain, prefer non_action

Return ONLY one word: actionable, non_action, or reference"""

        try:
            # max_tokens: Issue Type 결정은 짧은 응답
            # See: docs/phase-2/LLM_TOKEN_GUIDELINES.md
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=64)
            result = response.strip().lower()

            if "actionable" in result:
                return IssueType.ACTIONABLE
            elif "reference" in result:
                return IssueType.REFERENCE
            else:
                return IssueType.NON_ACTION

        except Exception as e:
            logger.warning(f"[LSAgent] Issue type classification failed: {e}")
            return IssueType.NON_ACTION

    def _convert_tdocs(self, tdocs_data: list[dict]) -> list[TdocRef]:
        """
        BoundaryDetector의 tdoc dict를 TdocRef 객체로 변환

        Args:
            tdocs_data: [{"id": "R1-...", "title": "...", "companies": [...], "doc_type": "..."}]

        Returns:
            TdocRef 객체 리스트
        """
        from ...models import DocType

        result = []
        for td in tdocs_data:
            if not td.get("id"):
                continue

            # doc_type 문자열을 DocType enum으로 변환
            doc_type_str = td.get("doc_type", "").lower()
            doc_type = None
            if "discussion" in doc_type_str:
                doc_type = DocType.DISCUSSION
            elif "reply" in doc_type_str or "ls_reply" in doc_type_str:
                doc_type = DocType.LS_REPLY_DRAFT
            elif "session" in doc_type_str or "note" in doc_type_str:
                doc_type = DocType.SESSION_NOTES
            elif "incoming" in doc_type_str or "ls_incoming" in doc_type_str:
                doc_type = DocType.LS_INCOMING

            result.append(
                TdocRef(
                    id=td.get("id", ""),
                    title=td.get("title"),
                    companies=td.get("companies", []),
                    doc_type=doc_type,
                )
            )

        return result

    def _generate_simple_summary(
        self, title: str, decision: str, source_wg: str
    ) -> str:
        """
        간단한 한국어 요약 생성

        Args:
            title: LS 제목
            decision: Decision 텍스트
            source_wg: 소스 WG

        Returns:
            한국어 요약 문자열
        """
        prompt = f"""Generate a concise Korean summary (1-2 sentences) for this Liaison Statement.

Title: {title}
Source WG: {source_wg}
Decision: {decision}

Output ONLY the Korean summary, nothing else.
Example: "RAN2에서 AI/ML 기반 UE 에너지 절약 기능의 RAN1 측면에 대한 의견을 요청함. RAN1은 추후 논의 예정."
"""

        try:
            response = self.llm.generate(prompt, temperature=0.3, max_tokens=1024)
            return response.strip()
        except Exception as e:
            logger.warning(f"[LSAgent] Summary generation failed: {e}")
            return f"{source_wg}에서 {title}에 대한 협조를 요청함."

    def _calculate_issue_confidence(
        self,
        metadata_state: dict,
        tdoc_state: dict,
        classifier_state: dict,
        summary_state: dict,
    ) -> float:
        """
        Issue의 전체 신뢰도 계산

        Args:
            *_state: 각 Sub-Agent의 결과 state

        Returns:
            평균 신뢰도 (0.0-1.0)
        """
        confidences = [
            metadata_state.get("metadata_confidence", 0.5),
            tdoc_state.get("tdoc_confidence", 0.5),
            classifier_state.get("classification_confidence", 0.5),
            summary_state.get("summary_confidence", 0.5),
        ]
        return sum(confidences) / len(confidences)

    def _calculate_statistics(
        self,
        issues: list[Issue],
        cc_only_items: list[CCOnlyItem],
        source_wgs: list[str],
        categories: dict[str, int],
    ) -> dict[str, Any]:
        """
        Section 통계 계산

        Args:
            issues: Issue 리스트
            cc_only_items: CC-only 아이템 리스트
            source_wgs: 소스 WG 리스트
            categories: 카테고리별 개수

        Returns:
            통계 딕셔너리
        """
        # Issue Type별 집계
        type_counts = {}
        for issue in issues:
            type_str = str(issue.issue_type)
            type_counts[type_str] = type_counts.get(type_str, 0) + 1

        # Source WG 집계 (issues에서도 추출)
        all_source_wgs = set(source_wgs)
        for issue in issues:
            if issue.origin.source_wg:
                all_source_wgs.add(issue.origin.source_wg)

        return {
            "total_primary": len(issues),
            "total_cc_only": len(cc_only_items),
            "total_items": len(issues) + len(cc_only_items),
            "source_wgs": ", ".join(sorted(all_source_wgs)) if all_source_wgs else "",
            "issue_types": type_counts,
            "categories": categories,
        }

    def _create_empty_output(self, meeting_number: str) -> SectionOutput:
        """
        빈 SectionOutput 생성 (경계 탐지 실패 시)

        Args:
            meeting_number: 미팅 번호

        Returns:
            빈 SectionOutput
        """
        return SectionOutput(
            section_number=self.section_number,
            meeting_number=meeting_number,
            overview="이 섹션에서 처리할 Liaison Statement가 발견되지 않았습니다.",
            issues=[],
            cc_only_items=[],
            statistics={
                "total_primary": 0,
                "total_cc_only": 0,
                "total_items": 0,
            },
        )

    def detect_pattern(self, content: str) -> float:
        """
        이 Agent가 처리해야 하는 패턴인지 점수 반환

        Args:
            content: 분석할 텍스트

        Returns:
            0.0-1.0 신뢰도 점수
        """
        # Incoming LS 키워드 점수 (콘텐츠 기반)
        keywords = [
            "incoming liaison",
            "liaison statement",
            "incoming ls",
            "ls on",
            "reply ls",
            "to: ran1",
            "cc: ran1",
        ]

        content_lower = content.lower()
        score = 0.0
        for keyword in keywords:
            if keyword in content_lower:
                score += 0.15

        return min(score, 1.0)
