"""
CRMetadataExtractorAgent: CR/Spec 메타데이터를 추출하는 에이전트

Ground Truth 형식의 CR/Spec 메타:
**CR / Spec 메타**
- Release: **Rel-17**
- Spec: **TS 38.214**
- Work Item: `NR_MIMO_evo_DL_UL-Core`
- CR: `CR0655`
- Category: Cat F

** 제1 원칙 준수 **
- 모든 추출은 LLM으로만 수행
- NO REGEX for semantic analysis
"""

import json
import logging
from typing import Any

from ..base_agent import BaseAgent
from ...models import CRMetadata

logger = logging.getLogger(__name__)


class CRMetadataExtractorAgent(BaseAgent):
    """
    Issue 텍스트에서 CR/Spec 메타데이터를 추출

    추출 정보:
    - release: Rel-17, Rel-18 등
    - spec: TS 38.214, TS 38.211 등
    - work_item: NR_MIMO_evo_DL_UL-Core 등
    - cr_id: CR0655 등
    - category: Cat A, Cat F 등
    - tdoc_id: Final CR의 Tdoc ID
    """

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Issue 텍스트에서 CR 메타데이터 추출

        Args:
            state:
                - issue_text: Issue 원문
                - tdocs: 관련 Tdoc 목록 (선택)

        Returns:
            state with cr_metadata: list[CRMetadata]
        """
        self.log_start("CR metadata extraction")

        issue_text = state.get("issue_text", "")
        tdocs = state.get("tdocs", [])

        cr_metadata_list = self._extract_cr_metadata_with_llm(issue_text, tdocs)

        self.log_end(f"CR metadata extraction ({len(cr_metadata_list)} CRs)")
        return {**state, "cr_metadata": cr_metadata_list}

    def _extract_cr_metadata_with_llm(
        self,
        issue_text: str,
        tdocs: list[dict]
    ) -> list[CRMetadata]:
        """
        LLM을 사용하여 CR 메타데이터 추출 (제1 원칙 준수)
        """
        tdocs_context = ""
        if tdocs:
            tdocs_context = f"\n\nRelated TDocs:\n{json.dumps(tdocs[:10], ensure_ascii=False)}"

        prompt = f"""You are a 3GPP CR (Change Request) metadata extractor. Analyze the issue text and extract all CR-related metadata.

## CR Metadata Fields
- release: 3GPP Release (e.g., "Rel-17", "Rel-18", "Rel-19")
- spec: Specification number (e.g., "TS 38.214", "TS 38.211")
- work_item: Work Item code (e.g., "NR_MIMO_evo_DL_UL-Core", "NR_enh_MIMO-Core")
- cr_id: CR identifier (e.g., "CR0655", "0655")
- category: CR category (e.g., "Cat F", "Cat A", "Cat B")
- tdoc_id: Associated TDoc ID for the final CR (e.g., "R1-2501564")

## Issue Text
{issue_text[:4000]}
{tdocs_context}

## Instructions
1. Look for CR numbers (CR followed by digits, or just the number if context is clear)
2. Identify the target specification (TS xx.xxx)
3. Find the Release version
4. Identify the Work Item code if mentioned
5. Find the CR category (Cat A/B/C/D/F)
6. Associate with TDoc IDs if available

An issue may have multiple CRs (e.g., one for Rel-17 and one for Rel-18).

## Output Format
Return a JSON array of CR metadata objects:
[
  {{
    "release": "Rel-17",
    "spec": "TS 38.214",
    "work_item": "NR_MIMO_evo_DL_UL-Core",
    "cr_id": "CR0655",
    "category": "Cat F",
    "tdoc_id": "R1-2501564"
  }}
]

If no CR is found, return an empty array: []

Return ONLY the JSON array.
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=2048)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                logger.warning(f"JSON parse failed: {error}")
                return []

            # CRMetadata 객체로 변환
            result = []
            for item in parsed:
                if not item.get("release"):
                    continue  # release는 필수

                result.append(CRMetadata(
                    release=item.get("release", ""),
                    spec=item.get("spec"),
                    work_item=item.get("work_item"),
                    cr_id=item.get("cr_id"),
                    category=item.get("category"),
                    tdoc_id=item.get("tdoc_id")
                ))

            return result

        except Exception as e:
            logger.error(f"LLM CR metadata extraction failed: {e}")
            return []

    def extract_from_tdocs(
        self,
        tdocs: list[dict],
        default_release: str = ""
    ) -> list[CRMetadata]:
        """
        Tdoc 목록에서 CR 메타데이터 추출 (배치 처리용)

        Args:
            tdocs: Tdoc 정보 리스트 (doc_type 포함)
            default_release: 기본 Release 값

        Returns:
            CRMetadata 리스트
        """
        # Final CR만 필터링
        final_crs = [
            t for t in tdocs
            if t.get("doc_type") in ["cr_final", "CR_FINAL"]
        ]

        if not final_crs:
            return []

        prompt = f"""Extract CR metadata from these Final CR TDocs.

## Final CR TDocs
{json.dumps(final_crs, ensure_ascii=False, indent=2)}

Default Release (if not found): {default_release or "Unknown"}

## Output Format
Return a JSON array with one entry per CR:
[
  {{
    "release": "Release version",
    "spec": "Specification number",
    "work_item": "Work Item code or null",
    "cr_id": "CR number",
    "category": "Category or null",
    "tdoc_id": "TDoc ID"
  }}
]

Return ONLY the JSON array.
"""

        try:
            response = self.llm.generate(prompt, temperature=0.1, max_tokens=2048)
            success, parsed, error = self.validate_json_response(response)

            if not success:
                return []

            result = []
            for item in parsed:
                result.append(CRMetadata(
                    release=item.get("release", default_release),
                    spec=item.get("spec"),
                    work_item=item.get("work_item"),
                    cr_id=item.get("cr_id"),
                    category=item.get("category"),
                    tdoc_id=item.get("tdoc_id")
                ))

            return result

        except Exception as e:
            logger.error(f"LLM CR extraction from tdocs failed: {e}")
            return []
