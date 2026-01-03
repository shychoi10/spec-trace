"""
LS SubSection Agent

LS (Liaison Statement) 섹션에서 Item 추출

Spec 6.4 청킹 준수:
- 토큰 수 기반 청킹 판단 (코드)
- 청킹 경계는 LLM이 의미 단위로 결정 (True Agentic AI)
"""

import json
import re
from typing import Any

from .base import BaseSubSectionAgent
from ...prompts.subsection_prompts import LS_PROMPT
from ...utils.llm_client import call_llm_for_items, get_llm_client


# 청크 분할 임계값 (chars) - LLM 응답 크기 제한 고려
LS_CHUNK_THRESHOLD = 8000


# LLM 청킹 경계 결정 프롬프트 (Spec 6.4.2)
LS_CHUNKING_PROMPT = """당신은 3GPP 회의록 분석 전문가입니다.

다음 LS (Liaison Statement) 섹션 내용을 의미 단위로 분할해주세요.

## 분할 원칙 (Spec 6.4.2)
- 하나의 LS Item이 쪼개지지 않도록
- 의미 단위로 분할 (True Agentic AI)
- LS 청킹 경계 힌트:
  - 개별 LS 항목 경계 (각 수신 LS TDoc)
  - Release 그룹 경계 ("Rel-18", "Rel-19")
  - "CC-ed LSs" 등 카테고리 경계

## LS 섹션 내용
```
{content}
```

## 출력 형식
JSON 배열로 분할 경계를 표시하는 텍스트 마커를 반환하세요:
```json
{{
  "chunk_markers": [
    "첫 번째 청크 시작을 나타내는 텍스트 (예: **Rel-19 ...)",
    "두 번째 청크 시작을 나타내는 텍스트",
    ...
  ],
  "chunk_count": 숫자,
  "reason": "분할 근거"
}}
```

주의:
- chunk_markers는 실제 텍스트에서 찾을 수 있는 문자열이어야 함
- 분할이 불필요하면 빈 배열 반환
- 최대 10개 청크까지만 분할
"""


class LSSubAgent(BaseSubSectionAgent):
    """LS SubSection Agent

    명세서 5.2.5 참조:
    - 단위: 1 LS = 1 Item
    - 주요 결과: Decision
    - ls_in, ls_out 정보 추출

    Spec 6.4 청킹 준수:
    - 토큰 수 기반 청킹 필요 판단 (코드)
    - 청킹 경계는 LLM이 의미 단위로 결정 (True Agentic AI)
    """

    def get_section_type(self) -> str:
        """담당 section_type"""
        return "LS"

    def _normalize_content(self, content: str) -> str:
        """입력 내용 정규화

        python-docx 출력에서 발생하는 서식 이슈 처리

        Args:
            content: 원본 내용

        Returns:
            정규화된 내용
        """
        # 1. <u> 태그 제거
        normalized = re.sub(r'</?u>', '', content)
        # 2. 연속된 **** 병합 (볼드 경계 정리)
        normalized = re.sub(r'\*{4,}', '', normalized)
        return normalized

    def _split_by_llm(self, content: str) -> list[str]:
        """LLM 기반 청킹 경계 결정 (Spec 6.4.2)

        True Agentic AI 원칙:
        - LLM이 의미 단위로 분할 경계 결정
        - 하나의 Item이 쪼개지지 않도록

        Args:
            content: LS 섹션 전체 내용 (정규화됨)

        Returns:
            의미 단위로 분할된 청크 리스트
        """
        try:
            # 내용이 너무 길면 앞부분만 사용 (LLM 컨텍스트 제한)
            content_for_prompt = content[:20000] if len(content) > 20000 else content

            llm = get_llm_client()
            prompt = LS_CHUNKING_PROMPT.format(content=content_for_prompt)

            response = llm.invoke(prompt)
            result_content = response.content

            # JSON 추출
            if "```json" in result_content:
                result_content = result_content.split("```json")[1].split("```")[0]
            elif "```" in result_content:
                result_content = result_content.split("```")[1].split("```")[0]

            result = json.loads(result_content.strip())
            chunk_markers = result.get("chunk_markers", [])

            if not chunk_markers:
                return [content]

            # 마커 기반으로 청크 분할
            chunks = []
            positions = []

            for marker in chunk_markers:
                pos = content.find(marker)
                if pos >= 0:
                    positions.append(pos)

            # 위치 정렬
            positions = sorted(set(positions))

            if not positions:
                return [content]

            # 청크 생성
            for i, pos in enumerate(positions):
                start = pos
                end = positions[i + 1] if i + 1 < len(positions) else len(content)
                chunk = content[start:end].strip()
                if chunk:
                    chunks.append(chunk)

            # 첫 번째 마커 이전 헤더 처리
            if positions[0] > 0:
                header = content[:positions[0]].strip()
                if header and chunks:
                    chunks[0] = header + "\n\n" + chunks[0]

            return chunks if chunks else [content]

        except Exception:
            # LLM 실패 시 fallback: 정규식 기반
            return self._split_by_regex_fallback(content)

    def _split_by_regex_fallback(self, content: str) -> list[str]:
        """정규식 기반 청킹 (fallback)

        LLM 실패 시 사용하는 백업 로직

        Args:
            content: LS 섹션 전체 내용

        Returns:
            Release Category별 청크 리스트
        """
        # Release category 패턴
        release_pattern = r'\*\*(?:Rel-\d+[^*]+|CC-ed[^*]+|LS received during[^*]+)\*\*'
        matches = list(re.finditer(release_pattern, content))

        if not matches:
            return [content]

        chunks = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

        # 첫 번째 Release Category 이전 내용 (헤더) 처리
        if matches and matches[0].start() > 0:
            header = content[:matches[0].start()].strip()
            if header and chunks:
                chunks[0] = header + "\n\n" + chunks[0]

        return chunks

    def _merge_small_chunks(self, chunks: list[str], max_size: int = 6000) -> list[str]:
        """작은 청크들을 병합하여 효율적인 LLM 호출

        Args:
            chunks: 분할된 청크 리스트
            max_size: 병합 후 최대 크기

        Returns:
            병합된 청크 리스트
        """
        merged = []
        current = ""

        for chunk in chunks:
            if len(current) + len(chunk) + 2 <= max_size:
                current = current + "\n\n" + chunk if current else chunk
            else:
                if current:
                    merged.append(current)
                current = chunk

        if current:
            merged.append(current)

        return merged

    def extract_items(
        self,
        leaf_id: str,
        leaf_title: str,
        leaf_content: str,
        context: dict,
    ) -> list[dict[str, Any]]:
        """Item 추출

        명세서 5.2.5, 6.5.5 참조:
        - 각 LS를 개별 Item으로 추출
        - ls_in, ls_out 필드 생성
        - Decision 추출

        Spec 6.4 청킹 준수:
        - LS_CHUNK_THRESHOLD 초과 시 LLM 기반 청킹
        - 청킹 경계는 LLM이 의미 단위로 결정 (True Agentic AI)
        - 각 청크 개별 LLM 호출 후 결과 병합

        Args:
            leaf_id: Leaf 섹션 ID
            leaf_title: Leaf 섹션 제목
            leaf_content: Leaf Markdown 내용
            context: 컨텍스트 (meeting_id, section_id, section_type 등)

        Returns:
            Item 목록
        """
        if not leaf_content or not leaf_content.strip():
            return []

        # 입력 정규화
        normalized_content = self._normalize_content(leaf_content)

        # 컨텍스트에 leaf 정보 추가
        full_context = {
            **context,
            "leaf_id": leaf_id,
            "leaf_title": leaf_title,
            "section_type": self.get_section_type(),
        }

        # 대용량 LS 섹션 처리: LLM 기반 청킹 (Spec 6.4)
        if len(normalized_content) > LS_CHUNK_THRESHOLD:
            # Spec 6.4.1: 토큰 수 기반 청킹 필요 판단 (코드)
            # Spec 6.4.2: 청킹 경계는 LLM이 결정 (True Agentic AI)
            chunks = self._split_by_llm(normalized_content)
            chunks = self._merge_small_chunks(chunks)

            all_items = []
            item_sequence = 1

            for chunk in chunks:
                items = call_llm_for_items(
                    leaf_content=chunk,
                    context=full_context,
                    prompt_template=LS_PROMPT,
                )

                # ID 순차 재할당 (청크별 001부터 시작 방지)
                for item in items:
                    # ID 형식: RAN1_120_5_XXX
                    meeting_id = context.get("meeting_id", "")
                    item["id"] = f"{meeting_id}_{leaf_id}_{item_sequence:03d}"
                    item_sequence += 1

                    if "context" not in item:
                        item["context"] = {}
                    item["context"]["leaf_id"] = leaf_id

                all_items.extend(items)

            return all_items

        # 일반 처리 (작은 섹션)
        items = call_llm_for_items(
            leaf_content=normalized_content,
            context=full_context,
            prompt_template=LS_PROMPT,
        )

        # 각 Item에 context.leaf_id 추가 (role_3에서 필터링용)
        for item in items:
            if "context" not in item:
                item["context"] = {}
            item["context"]["leaf_id"] = leaf_id

        return items
