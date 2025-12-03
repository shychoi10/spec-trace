"""
IssueSplitterAgent: Issue 경계 식별 Sub-Agent

Incoming Liaison Statements 텍스트를 입력받아 개별 LS 경계를 식별하고 JSON array로 반환
Note: 콘텐츠 기반 처리 - Section 번호에 종속되지 않음
"""

import json
from typing import Dict, Any, List


class IssueSplitterAgent:
    """Issue 경계 식별 Agent (LLM Autonomy)"""

    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.agent_name = self.__class__.__name__

    def process(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Incoming LS 텍스트를 개별 LS로 분할 (콘텐츠 기반)

        Args:
            content: Incoming Liaison Statements 전체 텍스트
            metadata: meeting_number 등

        Returns:
            List of issue dicts:
            [
                {
                    "ls_id": "R1-2500007",
                    "title": "LS response on waveform...",
                    "content": "Full text...",
                    "decision_text": "RAN2 response...",
                    "has_tdocs": false
                },
                ...
            ]
        """
        meeting_number = metadata.get("meeting_number", "Unknown")

        print(f"\n[{self.agent_name}] Splitting Incoming LS section into individual items...")

        prompt = self._build_prompt(content, meeting_number)

        # LLM 호출 (JSON 출력)
        for attempt in range(3):
            try:
                response = self.llm.generate(
                    prompt, temperature=0.1, max_tokens=20000
                )

                # Debug: Show first 500 chars of response
                print(f"[{self.agent_name}] LLM response preview: {response[:500]}...")

                # Strip markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]  # Remove ```

                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove closing ```

                cleaned_response = cleaned_response.strip()

                # JSON 파싱
                issues = json.loads(cleaned_response)

                print(
                    f"[{self.agent_name}] ✅ Identified {len(issues)} LS items"
                )
                return issues

            except json.JSONDecodeError as e:
                print(
                    f"[{self.agent_name}] ⚠️  JSON parse failed (attempt {attempt+1}/3): {e}"
                )
                print(f"[{self.agent_name}] Response was: {response[:1000]}")
                if attempt == 2:
                    print(
                        f"[{self.agent_name}] ❌ Failed after 3 attempts. Returning empty list."
                    )
                    return []

    def _build_prompt(self, content: str, meeting_number: str) -> str:
        """
        Dynamic prompt generation for issue splitting

        Args:
            content: Incoming Liaison Statements text
            meeting_number: Meeting number

        Returns:
            LLM prompt string
        """
        return f"""You are analyzing the Incoming Liaison Statements section of a 3GPP RAN1 meeting report.

Meeting: RAN1#{meeting_number}

Your task: Identify individual LS boundaries in this section.

Input Text:
{content}

Look for patterns:
- Each LS starts with an LS ID (R1-XXXXXXX)
- Followed by LS title
- Contains "Decision:" section
- May have "Relevant Tdocs" section

Output Format (JSON array):
[
  {{
    "ls_id": "R1-2500007",
    "title": "LS response on waveform determination in FR1-TDD for Rel-18 MIMO",
    "source_wg": "RAN2",
    "source_companies": ["CATT"],
    "content": "Full text for this LS including all paragraphs until next LS or section end",
    "decision_text": "RAN2 response for RAN1 LS (R2-2406928) on waveform determination in FR1-TDD for Rel-18 MIMO is noted. No further action is necessary.",
    "has_tdocs": false,
    "is_primary": true
  }},
  {{
    "ls_id": "R1-2500008",
    "title": "LS on preamble codebook mapping table issue",
    "source_wg": "RAN2",
    "source_companies": ["Huawei", "HiSilicon"],
    "content": "Full text...",
    "decision_text": "RAN1 is requested to discuss this LS in agenda item 7.1.1.4.1. A draft reply LS endorsed as in R1-2501635 will be sent to RAN2.",
    "has_tdocs": true,
    "is_primary": true
  }}
]

Important:
- Be comprehensive - identify ALL LS items regardless of count (do not assume any expected number)
- "source_wg": Extract the source Working Group (RAN2, RAN3, RAN4, SA2, etc.) - MANDATORY
- "source_companies": Extract company names if mentioned (look for patterns like "RAN2, Huawei" or "from Samsung") - use empty array [] if not found
- "is_primary": true if LS requires working group action/reply, false if CC-only (Decision indicates "Noted" with no action)
- Extract "decision_text" EXACTLY as written (look for "Decision:" keyword)
- "has_tdocs": Check if there's a "Relevant Tdocs:" section

Generate the JSON array now:
"""
