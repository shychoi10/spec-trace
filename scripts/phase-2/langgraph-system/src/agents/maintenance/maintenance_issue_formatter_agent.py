"""
MaintenanceIssueFormatterAgent: 모든 정보를 MaintenanceIssue로 조합

Ground Truth 형식의 Issue 블록 생성:
- Origin 블록
- Draft / Discussion Tdocs
- Moderator Summaries
- LS 관련 Tdocs
- Final CRs
- Summary (Korean)
- Decision / Agreement
- CR / Spec 메타
- Agenda Item
- Issue Type

** 제1 원칙 준수 **
- 모든 분석은 LLM으로만 수행
- NO REGEX for semantic analysis
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent
from ...models import (
    CRMetadata,
    DecisionType,
    DocType,
    IssueOrigin,
    IssueType,
    MaintenanceIssue,
    OriginType,
    TdocWithType,
)

logger = logging.getLogger(__name__)


class MaintenanceIssueFormatterAgent(BaseAgent):
    """
    추출된 모든 정보를 MaintenanceIssue 객체로 조합

    입력: 개별 에이전트들의 출력
    출력: Ground Truth 형식의 MaintenanceIssue
    """

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        모든 추출 정보를 MaintenanceIssue로 조합

        Args:
            state:
                - issue_text: 원본 Issue 텍스트
                - issue_title: Issue 제목
                - origin: IssueOrigin 객체
                - categorized_tdocs: TdocWithType 리스트
                - cr_metadata: CRMetadata 리스트
                - issue_type: IssueType
                - decision_text: Decision/Agreement 텍스트
                - decision_type: DecisionType
                - summary_ko: Korean summary

        Returns:
            state with maintenance_issue: MaintenanceIssue
        """
        self.log_start("MaintenanceIssue formatting")

        # 필수 정보 추출
        issue_title = state.get("issue_title", "Untitled Issue")
        issue_text = state.get("issue_text", "")

        # Origin
        origin = state.get("origin")
        if not origin:
            origin = self._create_default_origin(state)

        # Tdocs 분류별 그룹화
        categorized_tdocs = state.get("categorized_tdocs", [])
        tdoc_groups = self._group_tdocs(categorized_tdocs)

        # CR 메타데이터
        cr_metadata = state.get("cr_metadata", [])

        # Decision/Agreement
        decision_text = state.get("decision_text", "")
        decision_type = state.get("decision_type")

        # Summary
        summary_ko = state.get("summary_ko", "")
        if not summary_ko and issue_text:
            summary_ko = self._generate_summary(issue_text, decision_text)

        # Issue Type
        issue_type = state.get("issue_type")
        if not issue_type:
            issue_type = self._infer_issue_type(
                decision_text, len(tdoc_groups.get("final_crs", []))
            )

        # Agenda Item
        agenda_item = state.get("agenda_item", "")
        if not agenda_item and origin:
            agenda_item = f"{origin.topic or 'General'} ({origin.section})"

        # MaintenanceIssue 생성
        maintenance_issue = MaintenanceIssue(
            issue_title=issue_title,
            origin=origin,
            draft_discussion_tdocs=tdoc_groups.get("draft_discussion", []),
            moderator_summaries=tdoc_groups.get("moderator_summaries", []),
            ls_related_tdocs=tdoc_groups.get("ls_related", []),
            final_crs=tdoc_groups.get("final_crs", []),
            summary_ko=summary_ko,
            decision_text=decision_text,
            decision_type=decision_type,
            cr_metadata=cr_metadata,
            agenda_item=agenda_item,
            issue_type=issue_type,
            confidence_score=self._calculate_confidence(state),
            raw_text=issue_text
        )

        self.log_end(f"MaintenanceIssue formatted: {issue_title[:50]}...")
        return {**state, "maintenance_issue": maintenance_issue}

    def _create_default_origin(self, state: dict[str, Any]) -> IssueOrigin:
        """
        state에서 Origin 정보 생성
        """
        section_title = state.get("section_title", "Unknown Section")
        section_type = state.get("section_type", "maintenance")
        topic = state.get("topic", None)

        if section_type == "incoming_ls":
            origin_type = OriginType.LS
        else:
            origin_type = OriginType.INTERNAL_MAINTENANCE

        return IssueOrigin(
            type=origin_type,
            section=section_title,
            topic=topic,
            from_ls=None
        )

    def _group_tdocs(
        self,
        categorized_tdocs: list[TdocWithType]
    ) -> dict[str, list[TdocWithType]]:
        """
        Tdocs를 Ground Truth 그룹으로 분류
        """
        groups = {
            "draft_discussion": [],
            "moderator_summaries": [],
            "ls_related": [],
            "final_crs": [],
            "others": []
        }

        for tdoc in categorized_tdocs:
            if tdoc.doc_type in [DocType.CR_DRAFT, DocType.DISCUSSION]:
                groups["draft_discussion"].append(tdoc)
            elif tdoc.doc_type in [DocType.SUMMARY, DocType.SUMMARY_FINAL]:
                groups["moderator_summaries"].append(tdoc)
            elif tdoc.doc_type in [DocType.LS_INCOMING, DocType.LS_DRAFT,
                                   DocType.LS_FINAL, DocType.LS_REPLY_DRAFT]:
                groups["ls_related"].append(tdoc)
            elif tdoc.doc_type == DocType.CR_FINAL:
                groups["final_crs"].append(tdoc)
            else:
                groups["others"].append(tdoc)

        return groups

    def _generate_summary(self, issue_text: str, decision_text: str) -> str:
        """
        LLM을 사용하여 Korean summary 생성 (제1 원칙 준수)
        """
        prompt = f"""당신은 3GPP 기술 문서 요약 전문가입니다. 아래 이슈를 한국어로 요약해주세요.

## Issue 내용
{issue_text[:3000]}

## Decision/Agreement
{decision_text[:500] if decision_text else "결정 없음"}

## 요약 작성 가이드라인
1. 3-5문장으로 핵심 내용 요약
2. 기술적 논점을 명확히 설명
3. 최종 결정/합의 내용 포함
4. 한국어로 작성 (기술 용어는 영문 유지 가능)

요약만 작성해주세요 (다른 설명 없이).
"""
        try:
            response = self.llm.generate(prompt, temperature=0.3, max_tokens=1024)
            return response.strip()
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return ""

    def _infer_issue_type(
        self,
        decision_text: str,
        final_cr_count: int
    ) -> IssueType:
        """
        Decision 텍스트와 Final CR 개수로 Issue Type 추론
        """
        if final_cr_count > 0:
            return IssueType.SPEC_CHANGE_FINAL_CR

        if not decision_text:
            return IssueType.OPEN_INCONCLUSIVE

        # LLM으로 분류
        prompt = f"""Classify this 3GPP decision into one of:
- SpecChange_FinalCR: Final CR approved
- Closed_Not_Pursued: Not pursued, nothing broken
- Clarification_NoCR: Clarification only, no CR
- Open_Inconclusive: No consensus, open

Decision text: {decision_text[:500]}

Return ONLY the classification (one of the above).
"""
        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=64)
            response = response.strip()

            if "FinalCR" in response:
                return IssueType.SPEC_CHANGE_FINAL_CR
            elif "Not_Pursued" in response:
                return IssueType.CLOSED_NOT_PURSUED
            elif "NoCR" in response:
                return IssueType.CLARIFICATION_NO_CR
            else:
                return IssueType.OPEN_INCONCLUSIVE

        except Exception:
            return IssueType.CLOSED_NOT_PURSUED

    def _calculate_confidence(self, state: dict[str, Any]) -> float:
        """
        추출 품질에 대한 신뢰도 점수 계산
        """
        score = 0.5  # 기본 점수

        # Origin 존재
        if state.get("origin"):
            score += 0.1

        # Tdocs 존재
        if state.get("categorized_tdocs"):
            score += 0.1

        # Decision 존재
        if state.get("decision_text"):
            score += 0.1

        # Summary 존재
        if state.get("summary_ko"):
            score += 0.1

        # Issue Type 존재
        if state.get("issue_type"):
            score += 0.1

        return min(score, 1.0)

    def format_batch(
        self,
        issues_data: list[dict[str, Any]]
    ) -> list[MaintenanceIssue]:
        """
        여러 Issue를 배치로 포맷팅

        Args:
            issues_data: Issue 데이터 리스트

        Returns:
            MaintenanceIssue 리스트
        """
        results = []
        for issue_data in issues_data:
            result_state = self.process(issue_data)
            if result_state.get("maintenance_issue"):
                results.append(result_state["maintenance_issue"])

        return results

    def to_ground_truth_markdown(
        self,
        issues: list[MaintenanceIssue],
        section_title: str,
        meeting_number: str
    ) -> str:
        """
        MaintenanceIssue 리스트를 Ground Truth 형식 Markdown으로 변환

        Args:
            issues: MaintenanceIssue 리스트
            section_title: Section 제목
            meeting_number: Meeting 번호

        Returns:
            Ground Truth 형식 Markdown 문자열
        """
        lines = [
            f"# {section_title} (RAN1 #{meeting_number})",
            "",
            "---",
            ""
        ]

        for idx, issue in enumerate(issues, 1):
            lines.append(f"### Issue {idx}: {issue.issue_title}")
            lines.append("")
            lines.append(issue.to_markdown())
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
