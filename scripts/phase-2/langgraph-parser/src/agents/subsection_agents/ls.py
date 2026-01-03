"""
LS SubSection Agent

LS (Liaison Statement) 섹션에서 Item 추출
"""

import re
from typing import Any

from .base import BaseSubSectionAgent
from ...prompts.subsection_prompts import LS_PROMPT
from ...utils.llm_client import call_llm_for_items


# 청크 분할 임계값 (chars) - LLM 응답 크기 제한 고려
LS_CHUNK_THRESHOLD = 8000


class LSSubAgent(BaseSubSectionAgent):
    """LS SubSection Agent

    명세서 5.2.5 참조:
    - 단위: 1 LS = 1 Item
    - 주요 결과: Decision
    - ls_in, ls_out 정보 추출

    대용량 LS 섹션 처리:
    - Release Category별로 분할하여 LLM 호출
    - 응답 크기 제한으로 인한 JSON 파싱 오류 방지
    """

    def get_section_type(self) -> str:
        """담당 section_type"""
        return "LS"

    def _split_by_release_category(self, content: str) -> list[str]:
        """Release Category별로 LS 섹션 분할

        패턴: **Rel-XX Topic** 또는 **CC-ed LSs** 등

        Args:
            content: LS 섹션 전체 내용

        Returns:
            Release Category별 청크 리스트
        """
        # 입력 정규화: python-docx 출력 표준화
        # RAN1_122 등 일부 문서에서 밑줄 서식이 Release Category 패턴을 깨뜨림
        # 1. <u> 태그 제거
        # 2. 연속된 **** 병합 (볼드 경계 정리)
        normalized = re.sub(r'</?u>', '', content)
        normalized = re.sub(r'\*{4,}', '', normalized)  # ****+ → 빈 문자열

        # Release category 패턴
        release_pattern = r'\*\*(?:Rel-\d+[^*]+|CC-ed[^*]+|LS received during[^*]+)\*\*'
        matches = list(re.finditer(release_pattern, normalized))

        if not matches:
            return [normalized]

        chunks = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(normalized)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)

        # 첫 번째 Release Category 이전 내용 (헤더) 처리
        if matches and matches[0].start() > 0:
            header = normalized[:matches[0].start()].strip()
            if header:
                # 헤더가 있으면 첫 번째 청크에 추가
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

        대용량 처리:
        - LS_CHUNK_THRESHOLD 초과 시 Release Category별 분할
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

        # 컨텍스트에 leaf 정보 추가
        full_context = {
            **context,
            "leaf_id": leaf_id,
            "leaf_title": leaf_title,
            "section_type": self.get_section_type(),
        }

        # 대용량 LS 섹션 처리: 청크 분할
        if len(leaf_content) > LS_CHUNK_THRESHOLD:
            chunks = self._split_by_release_category(leaf_content)
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
            leaf_content=leaf_content,
            context=full_context,
            prompt_template=LS_PROMPT,
        )

        # 각 Item에 context.leaf_id 추가 (role_3에서 필터링용)
        for item in items:
            if "context" not in item:
                item["context"] = {}
            item["context"]["leaf_id"] = leaf_id

        return items
