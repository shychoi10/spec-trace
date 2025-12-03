"""
LLM Manager: Google Gemini API 직접 호출 관리

지원 모델:
- gemini-2.5-flash (기본값, 가장 빠름)
- gemini-2.5-pro (고품질)
- gemini-2.0-flash (안정 버전)
"""

import os
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class LLMManager:
    """Google Gemini API를 직접 호출하는 매니저"""

    # Safety 설정 (기술 문서 분석이므로 필터링 완화)
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Args:
            model: 사용할 모델 (기본값: Gemini 2.5 Flash)
        """
        self.model_name = model

        # Google API Key 설정
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")

        genai.configure(api_key=api_key)

        # Safety Settings를 모델 생성 시 적용
        self.model = genai.GenerativeModel(
            model,
            safety_settings=self.SAFETY_SETTINGS,
        )

    # 최소/최대 토큰 상수
    MIN_OUTPUT_TOKENS = 1024  # 최소 출력 토큰 (너무 낮으면 응답 실패)
    MAX_OUTPUT_TOKENS = 65536  # Gemini 2.5 Flash의 최대 출력 토큰 (65K)

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 8192) -> str:
        """
        LLM으로부터 응답 생성

        Args:
            prompt: 전송할 프롬프트
            temperature: 샘플링 온도 (0.0-2.0)
            max_tokens: 최대 토큰 수 (기본값: 8192)

        Returns:
            LLM의 응답 텍스트
        """
        # 최소 토큰 보장 (너무 낮으면 응답 실패)
        actual_max_tokens = max(self.MIN_OUTPUT_TOKENS, min(max_tokens, self.MAX_OUTPUT_TOKENS))

        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=actual_max_tokens,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            # 응답 검증
            if response.candidates and response.candidates[0].content.parts:
                # finish_reason 확인 (1=STOP 정상, 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER)
                finish_reason = response.candidates[0].finish_reason
                if finish_reason == 2:
                    print(f"[Warning] 응답이 max_tokens에 의해 잘림 (finish_reason=MAX_TOKENS)")
                return response.text
            else:
                # 응답이 비어있는 경우
                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    # finish_reason 코드: 1=STOP, 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER
                    reason_names = {1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}
                    reason_name = reason_names.get(finish_reason, f"UNKNOWN({finish_reason})")
                    print(f"[Error] LLM 응답 없음 (finish_reason={reason_name})")

                    # SAFETY 블록인 경우 프롬프트 일부 출력
                    if finish_reason == 3:
                        print(f"[Debug] 프롬프트 앞부분: {prompt[:200]}...")
                return ""

        except Exception as e:
            print(f"[Error] LLM 호출 실패: {e}")
            return ""

    def generate_with_system(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 8192
    ) -> str:
        """
        System prompt와 함께 응답 생성

        Args:
            system_prompt: 시스템 프롬프트 (역할 정의)
            user_prompt: 사용자 프롬프트 (작업 지시)
            temperature: 샘플링 온도
            max_tokens: 최대 토큰 수 (기본값: 8192)

        Returns:
            LLM의 응답 텍스트
        """
        # 최소 토큰 보장
        actual_max_tokens = max(self.MIN_OUTPUT_TOKENS, min(max_tokens, self.MAX_OUTPUT_TOKENS))

        try:
            # Gemini는 system_instruction을 모델 생성 시 설정
            model_with_system = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt,
                safety_settings=self.SAFETY_SETTINGS,
            )

            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=actual_max_tokens,
            )

            response = model_with_system.generate_content(
                user_prompt,
                generation_config=generation_config,
            )

            # 응답 검증
            if response.candidates and response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason
                if finish_reason == 2:
                    print(f"[Warning] 응답이 max_tokens에 의해 잘림 (finish_reason=MAX_TOKENS)")
                return response.text
            else:
                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    reason_names = {1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}
                    reason_name = reason_names.get(finish_reason, f"UNKNOWN({finish_reason})")
                    print(f"[Error] LLM 응답 없음 (finish_reason={reason_name})")
                return ""

        except Exception as e:
            print(f"[Error] LLM 호출 실패: {e}")
            return ""
