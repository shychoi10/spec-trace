"""
LLM 클라이언트 (OpenRouter API via requests)

명세서 4.1 참조: 정규식 실패 시 LLM fallback
"""

import json
import os
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv


def load_llm_config() -> dict:
    """config/settings.yaml에서 LLM 설정 로드

    Returns:
        LLM 설정 dict (model, base_url, max_tokens, temperature)
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config["llm"]


class OpenRouterClient:
    """OpenRouter API 클라이언트 (requests 기반)"""

    def __init__(self, api_key: str, model: str, base_url: str, max_tokens: int, temperature: float):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature

    def invoke(self, prompt: str) -> Any:
        """LLM 호출

        Args:
            prompt: 프롬프트 텍스트

        Returns:
            응답 객체 (content 속성 포함)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        # SSL 검증 비활성화 (WSL 환경 호환)
        # 프로덕션에서는 verify=True 또는 CA 번들 설정 권장
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
            verify=False,
        )
        response.raise_for_status()

        result = response.json()

        # 응답 객체 생성 (LangChain 호환 인터페이스)
        class Response:
            def __init__(self, content: str):
                self.content = content

        return Response(result["choices"][0]["message"]["content"])


def get_llm_client() -> OpenRouterClient:
    """LLM 클라이언트 초기화 (OpenRouter API)

    Returns:
        설정된 LLM 인스턴스

    Raises:
        ValueError: API KEY 환경변수 미설정 시
    """
    load_dotenv()
    config = load_llm_config()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY 환경변수가 설정되지 않았습니다")

    return OpenRouterClient(
        api_key=api_key,
        model=config["model"],
        base_url=config["base_url"],
        max_tokens=config["max_tokens"],
        temperature=config["temperature"],
    )


def call_llm_for_metadata(
    header_text: str,
    partial_data: dict | None,
    prompt_template: str,
) -> dict:
    """LLM으로 메타데이터 추출/보완

    정규식 파싱 실패 시 LLM fallback으로 호출

    Args:
        header_text: 원본 헤더 텍스트
        partial_data: 정규식으로 추출된 부분 데이터 (None 가능)
        prompt_template: 프롬프트 템플릿 (format용)

    Returns:
        완성된 메타데이터 dict

    Raises:
        json.JSONDecodeError: LLM 응답이 유효한 JSON이 아닐 때
        Exception: LLM 호출 실패 시
    """
    llm = get_llm_client()

    # 프롬프트 생성
    prompt = prompt_template.format(
        header_content=header_text,
        partial_data=json.dumps(partial_data, indent=2, ensure_ascii=False)
        if partial_data
        else "None",
    )

    # LLM 호출
    response = llm.invoke(prompt)

    # JSON 추출 (```json ... ``` 블록 처리)
    content = response.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content.strip())


def _extract_json_from_response(content: str) -> str:
    """LLM 응답에서 JSON 블록 추출"""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return content.strip()


def _split_toc_by_top_level(toc_content: str) -> list[str]:
    """TOC를 top-level 섹션별로 분할

    Args:
        toc_content: 전체 TOC 텍스트

    Returns:
        top-level 섹션별 TOC 청크 리스트
    """
    import re

    lines = toc_content.split("\n")
    chunks = []
    current_chunk = []

    for line in lines:
        # top-level 패턴: [숫자 또는 [숫자. 로 시작하는 줄
        if re.match(r"^\[?\d+[\.\s\]]", line.strip()):
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            current_chunk = [line]
        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def call_llm_for_items(
    leaf_content: str,
    context: dict,
    prompt_template: str,
) -> list[dict]:
    """LLM으로 Item 추출

    명세서 5.2, 6.5 참조:
    - SubSection Agent가 Leaf 내용에서 Item 추출
    - Item 경계 판단 (의미 기반)
    - 마커 패턴 인식

    Args:
        leaf_content: Leaf 섹션 본문
        context: 컨텍스트 (meeting_id, section_id, leaf_id 등)
        prompt_template: 프롬프트 템플릿

    Returns:
        Item 데이터 리스트

    Raises:
        json.JSONDecodeError: LLM 응답이 유효한 JSON이 아닐 때
        Exception: LLM 호출 실패 시
    """
    llm = get_llm_client()

    # 프롬프트 생성
    prompt = prompt_template.format(
        section_content=leaf_content,
        meeting_id=context.get("meeting_id", ""),
        section_id=context.get("section_id", ""),
        leaf_id=context.get("leaf_id", ""),
        leaf_title=context.get("leaf_title", ""),
        section_type=context.get("section_type", ""),
    )

    # LLM 호출
    response = llm.invoke(prompt)
    content = _extract_json_from_response(response.content)

    try:
        result = json.loads(content)
        # 배열로 감싸기 (단일 객체인 경우)
        if isinstance(result, dict):
            return [result]
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        # 빈 결과 반환
        return []


def call_llm_for_annex(
    annex_content: str,
    annex_id: str,
    prompt_template: str,
) -> list[dict]:
    """LLM으로 Annex Entry 추출

    명세서 5.2.6, 6.5.6 참조:
    - AnnexSubAgent가 Annex 내용에서 Entry 추출
    - 표 파싱 중심
    - 크로스체크용 데이터

    Args:
        annex_content: Annex 본문
        annex_id: annex_b, annex_c1, annex_c2
        prompt_template: 프롬프트 템플릿

    Returns:
        Entry 데이터 리스트

    Raises:
        json.JSONDecodeError: LLM 응답이 유효한 JSON이 아닐 때
        Exception: LLM 호출 실패 시
    """
    llm = get_llm_client()

    # 프롬프트 생성
    prompt = prompt_template.format(
        annex_content=annex_content,
        annex_id=annex_id,
    )

    # LLM 호출
    response = llm.invoke(prompt)
    content = _extract_json_from_response(response.content)

    try:
        result = json.loads(content)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


def call_llm_for_toc(
    toc_content: str,
    prompt_template: str,
) -> list[dict]:
    """LLM으로 TOC 파싱 (청크 분할 방식)

    명세서 4.2, 6.3 참조:
    - TOC 구조 파싱
    - section_type 판단 (의미 기반)
    - Virtual Numbering 처리
    - skip 여부 결정

    대용량 TOC의 경우 top-level 섹션별로 분할하여 처리

    Args:
        toc_content: TOC 영역 텍스트
        prompt_template: 프롬프트 템플릿

    Returns:
        TOCSection 데이터 리스트

    Raises:
        json.JSONDecodeError: LLM 응답이 유효한 JSON이 아닐 때
        Exception: LLM 호출 실패 시
    """
    llm = get_llm_client()

    # TOC가 10,000자 이상이면 청크 분할
    if len(toc_content) > 10000:
        chunks = _split_toc_by_top_level(toc_content)
        all_sections = []

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            prompt = prompt_template.format(toc_content=chunk)
            response = llm.invoke(prompt)
            content = _extract_json_from_response(response.content)

            try:
                sections = json.loads(content)
                if isinstance(sections, list):
                    all_sections.extend(sections)
            except json.JSONDecodeError:
                # 파싱 실패 시 부분 JSON 복구 시도
                content = content.rstrip(",\n ") + "]"
                if not content.startswith("["):
                    content = "[" + content
                try:
                    sections = json.loads(content)
                    if isinstance(sections, list):
                        all_sections.extend(sections)
                except json.JSONDecodeError:
                    # 복구 실패 시 해당 청크 건너뛰기
                    pass

        return all_sections

    # 작은 TOC는 한번에 처리
    prompt = prompt_template.format(toc_content=toc_content)
    response = llm.invoke(prompt)
    content = _extract_json_from_response(response.content)

    return json.loads(content)
