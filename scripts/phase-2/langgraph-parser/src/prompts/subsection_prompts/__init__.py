"""
SubSection Agent 프롬프트 패키지

각 section_type별 Item 추출 프롬프트
"""

from .maintenance import MAINTENANCE_PROMPT
from .release import RELEASE_PROMPT
from .study import STUDY_PROMPT
from .ue_features import UE_FEATURES_PROMPT
from .ls import LS_PROMPT
from .annex import ANNEX_PROMPTS, ANNEX_B_PROMPT, ANNEX_C1_PROMPT, ANNEX_C2_PROMPT

__all__ = [
    "MAINTENANCE_PROMPT",
    "RELEASE_PROMPT",
    "STUDY_PROMPT",
    "UE_FEATURES_PROMPT",
    "LS_PROMPT",
    "ANNEX_PROMPTS",
    "ANNEX_B_PROMPT",
    "ANNEX_C1_PROMPT",
    "ANNEX_C2_PROMPT",
]
