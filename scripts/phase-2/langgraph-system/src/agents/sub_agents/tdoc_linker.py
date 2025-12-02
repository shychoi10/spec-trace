"""
TdocLinker Sub-Agent

Issue 텍스트에서 관련 Tdoc을 추출하고 문서 유형을 분류합니다.

True Agentic AI: Tdoc 추출 및 유형 분류를 LLM이 수행
- 정규식(regex) 사용 금지
- 모든 추출/분류는 LLM이 수행
"""

import json
import logging
from typing import Any, Optional

from ..base_agent import BaseAgent, AgentResult
from ...models import TdocRef, DocType

logger = logging.getLogger(__name__)


class TdocLinker(BaseAgent):
    """Tdoc 연결 및 문서 유형 분류 Sub-Agent"""

    def __init__(self, llm_manager, config: Optional[dict] = None):
        super().__init__(llm_manager, config)
        self.doc_type_hints = self.config.get("incoming_ls_hints", {}).get(
            "doc_type_classification", {}
        )

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Issue 텍스트에서 관련 Tdoc 추출 및 유형 분류

        Args:
            state: LangGraph state
                - issue_text: Issue 텍스트
                - ls_id: 메인 LS ID (제외용)

        Returns:
            업데이트된 state
                - relevant_tdocs: TdocRef 리스트
        """
        issue_text = state.get("issue_text", "")
        ls_id = state.get("ls_id", "")

        self.log_start("Tdoc linking and classification")

        result = self._extract_and_classify_tdocs(issue_text, ls_id)

        if result.success:
            state["relevant_tdocs"] = result.output
            state["tdoc_confidence"] = result.confidence_score
            self.log_end("Tdoc linking", success=True)
        else:
            state["relevant_tdocs"] = []
            state["tdoc_confidence"] = 0.0
            self.log_end("Tdoc linking", success=False)

        return state

    def _extract_and_classify_tdocs(
        self, issue_text: str, exclude_ls_id: str
    ) -> AgentResult:
        """
        LLM을 사용하여 Tdoc 추출 및 분류

        Args:
            issue_text: Issue 텍스트
            exclude_ls_id: 제외할 메인 LS ID

        Returns:
            AgentResult with list of TdocRef
        """
        types_info = self.doc_type_hints.get("types", {})

        prompt = f"""You are extracting and classifying related Tdocs from a 3GPP RAN1 discussion.

**Document Type Classification Guidelines:**
{json.dumps(types_info, indent=2)}

**Issue Text:**
{issue_text[:10000]}

**Main LS ID to Exclude:** {exclude_ls_id}

**Instructions:**
1. Find ALL Tdoc references in the text (extract IDs exactly as they appear)
2. For each Tdoc:
   - Extract the exact ID from the text
   - Extract title if mentioned
   - Extract company names if mentioned (e.g., CATT, OPPO, Huawei)
   - Classify document type based on context
3. **Exclude** the main LS ID ({exclude_ls_id}) from the list
4. Common document types:
   - "ls_incoming": Incoming Liaison Statement
   - "ls_reply_draft": Draft reply to LS
   - "discussion": Discussion paper
   - "session_notes": Session moderator notes
   - "cr": Change Request
   - "other": Cannot determine

**IMPORTANT:**
- Return ONLY valid JSON
- Be thorough - include ALL Tdocs mentioned in the text
- Extract IDs exactly as they appear in the text

Return as JSON:
{{
  "tdocs": [
    {{
      "id": "<exact ID from text>",
      "title": "Document title or null",
      "companies": ["Company1", "Company2"],
      "doc_type": "ls_incoming|ls_reply_draft|discussion|session_notes|cr|other"
    }}
  ],
  "confidence": 0.0-1.0
}}
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=4000)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"[TdocLinker] JSON parse failed: {error}")
                # LLM 재시도 (True Agentic AI - regex fallback 금지)
                retry_result = self._retry_extraction_with_llm(issue_text, exclude_ls_id)
                return retry_result

            tdocs_data = parsed.get("tdocs", [])
            confidence = parsed.get("confidence", 0.7)

            # TdocRef 객체로 변환
            tdoc_refs = []
            for tdoc in tdocs_data:
                tdoc_id = tdoc.get("id", "")
                if not tdoc_id or tdoc_id == exclude_ls_id:
                    continue

                # DocType 변환
                doc_type_str = tdoc.get("doc_type", "other")
                doc_type = self._str_to_doctype(doc_type_str)

                tdoc_ref = TdocRef(
                    id=tdoc_id,
                    title=tdoc.get("title"),
                    companies=tdoc.get("companies", []),
                    doc_type=doc_type,
                )
                tdoc_refs.append(tdoc_ref)

            return AgentResult(
                success=True,
                output=tdoc_refs,
                confidence_score=confidence,
                validation_notes=[f"Found {len(tdoc_refs)} relevant Tdocs"],
            )

        except Exception as e:
            logger.error(f"[TdocLinker] LLM call failed: {e}")
            # LLM 재시도 (True Agentic AI - regex fallback 금지)
            retry_result = self._retry_extraction_with_llm(issue_text, exclude_ls_id)
            return retry_result

    def _str_to_doctype(self, type_str: str) -> DocType:
        """
        문자열을 DocType으로 변환

        Args:
            type_str: 문서 유형 문자열

        Returns:
            DocType enum
        """
        type_str_lower = type_str.lower()

        if "ls_incoming" in type_str_lower or "incoming" in type_str_lower:
            return DocType.LS_INCOMING
        elif "ls_reply" in type_str_lower or "reply" in type_str_lower:
            return DocType.LS_REPLY_DRAFT
        elif "discussion" in type_str_lower:
            return DocType.DISCUSSION
        elif "session" in type_str_lower or "moderator" in type_str_lower:
            return DocType.SESSION_NOTES
        elif "cr" in type_str_lower or "change" in type_str_lower:
            return DocType.CR
        else:
            return DocType.OTHER

    def _retry_extraction_with_llm(
        self, issue_text: str, exclude_ls_id: str
    ) -> AgentResult:
        """
        LLM 재시도를 통한 Tdoc 추출 (True Agentic AI)

        간소화된 프롬프트로 LLM 재시도를 수행합니다.
        정규식 fallback 대신 LLM만 사용합니다.

        Args:
            issue_text: Issue 텍스트
            exclude_ls_id: 제외할 메인 LS ID

        Returns:
            AgentResult with list of TdocRef
        """
        # 간소화된 프롬프트로 재시도 (콘텐츠 기반 - 미팅 번호/포맷 하드코딩 금지)
        simple_prompt = f"""Extract Tdoc IDs from this 3GPP RAN1 text.

Text:
{issue_text[:6000]}

Instructions:
1. Find all Tdoc references (R1-XXXXXXX format) mentioned in the text
2. Exclude the main LS ID: {exclude_ls_id}
3. For each Tdoc, classify its type based on context

Return ONLY valid JSON (no trailing commas, complete structure):
{{"tdocs": [{{"id": "<exact ID from text>", "doc_type": "discussion|ls_reply_draft|session_notes|other"}}], "confidence": 0.7}}
"""

        try:
            response = self.llm.generate(simple_prompt, temperature=0.0, max_tokens=2000)
            success, parsed, error = self.validate_json_response(response)

            if success:
                tdocs_data = parsed.get("tdocs", [])
                tdoc_refs = []

                for tdoc in tdocs_data:
                    tdoc_id = tdoc.get("id", "")
                    if not tdoc_id or tdoc_id == exclude_ls_id:
                        continue

                    doc_type = self._str_to_doctype(tdoc.get("doc_type", "other"))
                    tdoc_refs.append(TdocRef(
                        id=tdoc_id,
                        doc_type=doc_type,
                    ))

                return AgentResult(
                    success=True,
                    output=tdoc_refs,
                    confidence_score=0.5,
                    validation_notes=["LLM retry successful"],
                )
            else:
                logger.warning(f"[TdocLinker] Retry also failed: {error}")
                return AgentResult(
                    success=True,
                    output=[],
                    confidence_score=0.2,
                    validation_notes=["LLM extraction failed after retry"],
                )

        except Exception as e:
            logger.error(f"[TdocLinker] Retry LLM call failed: {e}")
            return AgentResult(
                success=True,
                output=[],
                confidence_score=0.1,
                error_message=str(e),
            )

    def classify_single_tdoc(
        self, tdoc_id: str, context: str
    ) -> DocType:
        """
        단일 Tdoc의 문서 유형 분류

        Args:
            tdoc_id: Tdoc ID
            context: 주변 컨텍스트 텍스트

        Returns:
            분류된 DocType
        """
        types_info = self.doc_type_hints.get("types", {})

        prompt = f"""Classify this 3GPP Tdoc's document type.

**Tdoc ID:** {tdoc_id}

**Context:**
{context[:1000]}

**Document Types:**
{json.dumps(types_info, indent=2)}

Return as JSON:
{{
  "doc_type": "ls_incoming|ls_reply_draft|discussion|session_notes|cr|other",
  "reasoning": "brief explanation"
}}
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=300)
            success, parsed, error = self.validate_json_response(response)

            if success:
                return self._str_to_doctype(parsed.get("doc_type", "other"))
            else:
                return DocType.OTHER

        except Exception as e:
            logger.warning(f"[TdocLinker] Single classification failed: {e}")
            return DocType.OTHER

    def link_batch(
        self, issues: list[tuple[str, str]]
    ) -> list[list[TdocRef]]:
        """
        여러 Issue의 Tdoc 일괄 추출

        Args:
            issues: (issue_text, exclude_ls_id) 튜플 리스트

        Returns:
            TdocRef 리스트의 리스트
        """
        results = []
        for issue_text, exclude_id in issues:
            result = self._extract_and_classify_tdocs(issue_text, exclude_id)
            results.append(result.output)
        return results
