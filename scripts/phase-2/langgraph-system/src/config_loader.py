"""
ConfigLoader - 설정 파일 로드 및 관리

하드코딩 제거를 위한 중앙 설정 관리 시스템
모든 경로, 값은 이 클래스를 통해 접근
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class MeetingConfig:
    """미팅별 설정 데이터 클래스"""

    id: str
    number: str
    working_group: str
    folder_name: str
    final_minutes_path: Path
    tdoc_list_path: Optional[Path] = None
    expected_counts: dict = field(default_factory=dict)
    source_wgs: list = field(default_factory=list)


class ConfigLoader:
    """
    중앙 설정 로더

    사용법:
        config = ConfigLoader()
        config.load_meeting("RAN1_120")
        docx_path = config.get_docx_path()
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: 설정 디렉토리 경로 (None이면 자동 감지)
        """
        if config_dir is None:
            # 현재 파일 위치 기준으로 config 디렉토리 찾기
            self._script_dir = Path(__file__).parent.parent
            config_dir = self._script_dir / "config"

        self.config_dir = Path(config_dir)
        self._settings: dict = {}
        self._meeting: Optional[MeetingConfig] = None
        self._domain_hints: dict = {}

        # 프로젝트 루트 설정
        self._project_root = self._script_dir.parent.parent.parent

        # 설정 파일 로드
        self._load_settings()
        self._load_domain_hints()

    def _load_settings(self) -> None:
        """메인 설정 파일 로드"""
        settings_path = self.config_dir / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                self._settings = yaml.safe_load(f) or {}

    def _load_domain_hints(self) -> None:
        """도메인 힌트 로드"""
        hints_path = self.config_dir / "domain_hints.yaml"
        if hints_path.exists():
            with open(hints_path, "r", encoding="utf-8") as f:
                self._domain_hints = yaml.safe_load(f) or {}

    def _resolve_path(self, path_str: str) -> Path:
        """
        경로 문자열을 실제 Path로 변환

        지원하는 변수:
        - ${PROJECT_ROOT}: 프로젝트 루트
        - ${ENV_VAR}: 환경 변수
        """
        # PROJECT_ROOT 치환
        path_str = path_str.replace("${PROJECT_ROOT}", str(self._project_root))

        # 환경 변수 치환
        env_pattern = r"\$\{([A-Z_]+)\}"
        for match in re.finditer(env_pattern, path_str):
            env_var = match.group(1)
            env_value = os.environ.get(env_var, "")
            path_str = path_str.replace(f"${{{env_var}}}", env_value)

        return Path(path_str)

    def load_meeting(self, meeting_id: str) -> MeetingConfig:
        """
        미팅 설정 로드

        Args:
            meeting_id: 미팅 ID (예: "RAN1_120")

        Returns:
            MeetingConfig 객체
        """
        meeting_file = self.config_dir / "meetings" / f"{meeting_id}.yaml"

        if not meeting_file.exists():
            raise FileNotFoundError(f"Meeting config not found: {meeting_file}")

        with open(meeting_file, "r", encoding="utf-8") as f:
            meeting_data = yaml.safe_load(f)

        meeting_info = meeting_data.get("meeting", {})
        hints = meeting_info.get("hints", {})

        # 데이터 경로 기준
        data_base = self._project_root / "data" / "data_transformed"

        # Final Minutes 경로 구성
        final_minutes_rel = meeting_info.get("input", {}).get("final_minutes", "")
        final_minutes_path = data_base / final_minutes_rel

        # Tdoc List 경로 구성 (선택적)
        tdoc_list_rel = meeting_info.get("input", {}).get("tdoc_list", "")
        tdoc_list_path = data_base / tdoc_list_rel if tdoc_list_rel else None

        self._meeting = MeetingConfig(
            id=meeting_info.get("id", meeting_id),
            number=meeting_info.get("number", ""),
            working_group=meeting_info.get("working_group", ""),
            folder_name=meeting_info.get("folder_name", ""),
            final_minutes_path=final_minutes_path,
            tdoc_list_path=tdoc_list_path,
            expected_counts=hints.get("expected_counts", {}),
            source_wgs=hints.get("source_wgs", []),
        )

        return self._meeting

    @property
    def meeting(self) -> MeetingConfig:
        """현재 로드된 미팅 설정"""
        if self._meeting is None:
            raise ValueError("No meeting loaded. Call load_meeting() first.")
        return self._meeting

    @property
    def project_root(self) -> Path:
        """프로젝트 루트 경로"""
        return self._project_root

    @property
    def output_dir(self) -> Path:
        """결과 출력 디렉토리"""
        return self._project_root / "output" / "phase-2" / "langgraph-system" / "results"

    @property
    def ground_truth_dir(self) -> Path:
        """Ground Truth 디렉토리"""
        return self._project_root / "output" / "phase-2" / "langgraph-system" / "ground_truth"

    @property
    def domain_hints(self) -> dict:
        """도메인 힌트"""
        return self._domain_hints

    @property
    def settings(self) -> dict:
        """전체 설정"""
        return self._settings

    def get_llm_config(self) -> dict:
        """LLM 설정 반환"""
        return self._settings.get("llm", {})

    def get_output_filename(self, content_type: str, suffix: str = "output") -> str:
        """
        출력 파일명 생성

        Args:
            content_type: 콘텐츠 타입 (예: "incoming_ls")
            suffix: 접미사 (예: "output", "ground_truth")

        Returns:
            파일명 (예: "RAN1_120_incoming_ls_output.md")
        """
        if self._meeting is None:
            raise ValueError("No meeting loaded")

        return f"{self._meeting.id}_{content_type}_{suffix}.md"
