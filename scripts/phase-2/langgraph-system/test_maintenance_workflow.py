#!/usr/bin/env python3
"""
Maintenance Workflow Test Script

Ground Truth 형식 출력을 테스트하기 위한 스크립트
RAN1_120의 Maintenance Section을 처리합니다.

Usage:
    python test_maintenance_workflow.py                # 기본 미팅 (RAN1_120)
    python test_maintenance_workflow.py --meeting RAN1_119  # 특정 미팅 지정
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.config_loader import ConfigLoader
from src.workflows.maintenance_workflow import MaintenanceWorkflow
from src.utils.document_parser import DocumentParser
from src.utils.llm_manager import LLMManager


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="Maintenance Workflow Test")
    parser.add_argument("--meeting", type=str, default="RAN1_120", help="Meeting ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    print("=" * 60)
    print("Phase-2 LangGraph System - Maintenance Workflow Test")
    print("=" * 60)

    # 1. Config 로드
    print("\n[1] Loading Configuration...")
    config = ConfigLoader()
    meeting = config.load_meeting(args.meeting)
    print(f"    Meeting: {meeting.id} (#{meeting.number})")
    print(f"    Input: {meeting.final_minutes_path.name}")

    if not meeting.final_minutes_path.exists():
        print(f"ERROR: File not found: {meeting.final_minutes_path}")
        return 1

    # 2. LLM Manager 초기화
    print("\n[2] Initializing LLM Manager...")
    llm_manager = LLMManager()
    print(f"    Model: {llm_manager.model}")

    # 3. Maintenance Section 추출
    print("\n[3] Extracting Maintenance Section...")
    doc_parser = DocumentParser(meeting.final_minutes_path, llm_manager)
    doc_parser.parse_paragraphs()

    # "maintenance"로 콘텐츠 기반 추출 (Section 번호 사용 X)
    maintenance_text = doc_parser.get_section_text("maintenance")

    if not maintenance_text:
        print("ERROR: Maintenance section not found")
        return 1

    print(f"    Extracted: {len(maintenance_text)} characters")
    print(f"    Preview: {maintenance_text[:200]}...")

    # 4. Maintenance Workflow 실행
    print("\n[4] Running Maintenance Workflow...")
    workflow = MaintenanceWorkflow()

    state = workflow.run(
        section_text=maintenance_text,
        meeting_number=meeting.number,
        section_metadata=None  # 자동 감지
    )

    issues = state.get("issues", [])  # 올바른 키 이름
    markdown_output = state.get("markdown_output", "")

    # 5. 결과 저장
    print("\n[5] Saving Results...")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    output_file = config.output_dir / f"{meeting.id}_maintenance.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_output)

    # 6. 결과 요약
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    print(f"  Total Issues: {len(issues)}")

    if issues:
        # Issue Type 분포
        from collections import Counter
        type_counts = Counter(str(getattr(i, 'issue_type', 'Unknown')) for i in issues)
        print(f"\n  Issue Type Distribution:")
        for issue_type, count in type_counts.items():
            print(f"    - {issue_type}: {count}")

        # Origin Type 분포
        origin_counts = Counter(
            str(getattr(getattr(i, 'origin', None), 'type', 'Unknown'))
            for i in issues
        )
        print(f"\n  Origin Type Distribution:")
        for origin_type, count in origin_counts.items():
            print(f"    - {origin_type}: {count}")

    print(f"\n  Output: {output_file}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
