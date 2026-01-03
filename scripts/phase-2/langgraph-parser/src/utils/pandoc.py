"""
Pandoc 유틸리티

.docx → Markdown 변환
"""

import re
import shutil
import subprocess
from pathlib import Path


def validate_pandoc_installation() -> tuple[bool, str]:
    """pandoc 설치 여부 확인

    Returns:
        tuple[bool, str]: (설치됨, 버전 또는 에러 메시지)
    """
    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # 첫 줄에서 버전 추출 (예: "pandoc 2.9.2.1")
        version_line = result.stdout.split("\n")[0]
        return True, version_line
    except FileNotFoundError:
        return False, "pandoc not found. Install with: sudo apt install pandoc"
    except subprocess.CalledProcessError as e:
        return False, f"pandoc error: {e.stderr}"


def extract_meeting_id(file_path: str | Path) -> str:
    """파일 경로에서 meeting_id 추출

    패턴 1: Final_Minutes_report_RAN1#120_v100.docx → RAN1_120
    패턴 2: TSGR1_120/... → RAN1_120

    Args:
        file_path: .docx 파일 경로

    Returns:
        meeting_id (예: RAN1_120), 추출 실패 시 "unknown"
    """
    file_path = Path(file_path)
    path_str = str(file_path)

    # 패턴 1: 파일명에서 RAN1#NNN 추출
    match = re.search(r"RAN1[#_](\d+)", path_str)
    if match:
        return f"RAN1_{match.group(1)}"

    # 패턴 2: 경로에서 TSGR1_NNN 추출
    match = re.search(r"TSGR1_(\d+\w*)", path_str)
    if match:
        meeting_num = match.group(1)
        return f"RAN1_{meeting_num}"

    return "unknown"


def convert_docx_to_markdown(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    extract_media: bool = True,
) -> tuple[str, str | None]:
    """DOCX 파일을 Markdown으로 변환

    Args:
        input_path: 입력 .docx 파일 경로
        output_dir: 출력 디렉토리 (None이면 임시 디렉토리 사용)
        extract_media: 임베디드 이미지 추출 여부

    Returns:
        tuple[str, str | None]: (markdown_content, media_dir 또는 None)

    Raises:
        RuntimeError: pandoc 미설치
        subprocess.CalledProcessError: pandoc 실행 실패
        FileNotFoundError: 입력 파일 없음
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # pandoc 설치 확인
    installed, version_or_error = validate_pandoc_installation()
    if not installed:
        raise RuntimeError(version_or_error)

    # 출력 디렉토리 설정
    media_dir = None
    # --wrap=none: 줄바꿈 유지 (명세서 4.0장)
    cmd = ["pandoc", str(input_path), "-t", "markdown", "--wrap=none"]

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if extract_media:
            # media 폴더를 output_dir 내부에 직접 생성 (media/media 중첩 방지)
            media_dir = str(output_dir / "media")
            cmd.extend(["--extract-media", str(output_dir)])

    # pandoc 실행
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    markdown_content = result.stdout

    return markdown_content, media_dir


def save_converted_markdown(
    content: str,
    output_dir: str | Path,
    filename: str = "document.md",
) -> Path:
    """변환된 Markdown을 파일로 저장

    Args:
        content: Markdown 콘텐츠
        output_dir: 출력 디렉토리
        filename: 출력 파일명

    Returns:
        저장된 파일 경로
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return output_path
