#!/usr/bin/env python3
"""
LangGraph Parser - 3GPP Final Minutes Report 파서

실행 진입점

Usage:
    python main.py --input <docx_path> --output <output_dir>
    python main.py --meeting RAN1_120

Examples:
    # 단일 파일 처리
    python main.py --input data/data_extracted/meetings/RAN1/TSGR1_120/Report/Final_Minutes.docx \
                   --output output/phase-2/langgraph-parser/results/RAN1_120

    # 회의 ID로 처리 (자동 경로 탐색)
    python main.py --meeting RAN1_120
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.state import create_initial_state
from src.graph import create_parser_graph


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """로깅 설정

    Args:
        log_level: 로그 레벨

    Returns:
        설정된 로거
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("langgraph-parser")


def load_config() -> dict:
    """설정 파일 로드

    Returns:
        설정 딕셔너리
    """
    config_path = PROJECT_ROOT / "config" / "settings.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_input_file(meeting_id: str, config: dict) -> Path:
    """회의 ID로 입력 파일 경로 탐색

    Args:
        meeting_id: 회의 ID (예: RAN1_120)
        config: 설정 딕셔너리

    Returns:
        입력 파일 경로

    Raises:
        FileNotFoundError: 입력 파일 없음
    """
    # 프로젝트 루트 기준 경로
    spec_trace_root = PROJECT_ROOT.parent.parent.parent  # scripts/phase-2/langgraph-parser -> root

    # meeting_id에서 정보 추출 (예: RAN1_120 -> TSGR1_120)
    parts = meeting_id.split("_")
    if len(parts) != 2:
        raise ValueError(f"Invalid meeting_id format: {meeting_id}")

    wg_code = parts[0]  # RAN1
    meeting_num = parts[1]  # 120
    # RAN1 → R1 변환 (폴더명 형식: TSGR1_120)
    wg_short = wg_code.replace("RAN", "R")  # RAN1 → R1
    meeting_folder = f"TSG{wg_short}_{meeting_num}"  # TSGR1_120

    # 입력 경로 탐색
    input_base = spec_trace_root / config["paths"]["input_base"]
    report_dir = input_base / meeting_folder / "Report"

    if not report_dir.exists():
        raise FileNotFoundError(f"Report directory not found: {report_dir}")

    # Final Minutes 파일 찾기 (하위 폴더 포함)
    for pattern in ["**/Final_Minutes*.docx", "**/*Final*Minutes*.docx", "*.docx"]:
        files = list(report_dir.glob(pattern))
        if files:
            return files[0]

    raise FileNotFoundError(f"No Final Minutes file found in: {report_dir}")


def run_parser(input_path: Path, output_dir: Path, config: dict) -> dict:
    """파서 실행

    Args:
        input_path: 입력 .docx 파일 경로
        output_dir: 출력 디렉토리
        config: 설정 딕셔너리

    Returns:
        최종 상태 딕셔너리
    """
    logger = logging.getLogger("langgraph-parser")

    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_dir}")

    # 초기 상태 생성
    initial_state = create_initial_state(
        input_path=str(input_path),
        output_dir=str(output_dir),
    )

    # 그래프 생성 및 실행
    graph = create_parser_graph()

    logger.info("Starting parser pipeline...")

    # 파이프라인 실행
    final_state = graph.invoke(initial_state)

    logger.info("Parser pipeline completed.")

    return final_state


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="LangGraph Parser - 3GPP Final Minutes Report 파서"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input",
        type=str,
        help="입력 .docx 파일 경로",
    )
    group.add_argument(
        "--meeting",
        type=str,
        help="회의 ID (예: RAN1_120)",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="출력 디렉토리 (기본값: 자동 생성)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨",
    )

    args = parser.parse_args()

    # 환경 변수 로드
    load_dotenv()

    # 로깅 설정
    logger = setup_logging(args.log_level)

    # 설정 로드
    try:
        config = load_config()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 입력 파일 결정
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
        meeting_id = input_path.stem.replace("Final_Minutes_report_", "").split("_v")[0]
    else:
        meeting_id = args.meeting
        try:
            input_path = find_input_file(meeting_id, config)
        except (FileNotFoundError, ValueError) as e:
            logger.error(str(e))
            sys.exit(1)

    # 출력 디렉토리 결정
    if args.output:
        output_dir = Path(args.output)
    else:
        spec_trace_root = PROJECT_ROOT.parent.parent.parent
        output_dir = spec_trace_root / config["paths"]["output_base"] / meeting_id

    # 파서 실행
    try:
        final_state = run_parser(input_path, output_dir, config)

        # 결과 요약 출력
        logger.info("=" * 50)
        logger.info("Parser Result Summary")
        logger.info("=" * 50)
        logger.info(f"Meeting ID: {final_state.get('meeting_id', 'N/A')}")
        logger.info(f"Current Step: {final_state.get('current_step', 'N/A')}")
        logger.info(f"Errors: {len(final_state.get('errors', []))}")
        logger.info(f"Warnings: {len(final_state.get('warnings', []))}")

    except Exception as e:
        logger.exception(f"Parser failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
