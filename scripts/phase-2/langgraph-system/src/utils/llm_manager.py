"""
LLM Manager: OpenRouter를 통한 Gemini 2.5 Pro 호출 관리
"""

import os
from openai import OpenAI


class LLMManager:
    """OpenRouter를 통해 LLM을 호출하는 매니저"""

    def __init__(self, model: str = "google/gemini-2.5-flash"):
        """
        Args:
            model: 사용할 모델 (기본값: Gemini 2.5 Flash)
        """
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """
        LLM으로부터 응답 생성

        Args:
            prompt: 전송할 프롬프트
            temperature: 샘플링 온도 (0.0-2.0)
            max_tokens: 최대 토큰 수

        Returns:
            LLM의 응답 텍스트
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"LLM 호출 실패: {e}")
            return ""

    def generate_with_system(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 4000
    ) -> str:
        """
        System prompt와 함께 응답 생성

        Args:
            system_prompt: 시스템 프롬프트 (역할 정의)
            user_prompt: 사용자 프롬프트 (작업 지시)
            temperature: 샘플링 온도
            max_tokens: 최대 토큰 수

        Returns:
            LLM의 응답 텍스트
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"LLM 호출 실패: {e}")
            return ""
