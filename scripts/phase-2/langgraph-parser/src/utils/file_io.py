"""
파일 I/O 유틸리티

YAML 파일 읽기/쓰기
"""

import re
from pathlib import Path
from typing import Any

import yaml


def ensure_output_dir(output_dir: str | Path) -> Path:
    """출력 디렉토리 생성 (없으면)

    Args:
        output_dir: 출력 디렉토리 경로

    Returns:
        Path 객체
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_yaml(data: Any, file_path: str | Path) -> None:
    """데이터를 YAML 파일로 저장

    Args:
        data: 저장할 데이터 (dict, list 등)
        file_path: 저장할 파일 경로

    Raises:
        IOError: 파일 쓰기 실패
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def load_yaml(file_path: str | Path) -> Any:
    """YAML 파일 로드

    Args:
        file_path: 로드할 파일 경로

    Returns:
        로드된 데이터

    Raises:
        FileNotFoundError: 파일 없음
        yaml.YAMLError: YAML 파싱 실패
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_items_yaml(items: list[dict], file_path: str | Path) -> None:
    """Item 리스트를 가독성 좋은 YAML 파일로 저장

    각 Item 사이에 빈 줄을 추가하여 가독성을 높임.

    Args:
        items: Item 딕셔너리 리스트
        file_path: 저장할 파일 경로
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 일반 YAML 덤프
    yaml_content = yaml.dump(
        items,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    # 각 Item 시작 부분 (- id:) 앞에 빈 줄 추가
    # 첫 번째 Item 제외하고 "- id:" 패턴 앞에 빈 줄 삽입
    formatted_content = re.sub(r'\n(- id:)', r'\n\n\1', yaml_content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_content)
