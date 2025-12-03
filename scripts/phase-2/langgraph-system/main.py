#!/usr/bin/env python3
"""
Phase-2 LangGraph System - Incoming LS Pipeline

Usage:
    python main.py                      # 기본 미팅 (RAN1_120)
    python main.py --meeting RAN1_119   # 특정 미팅 지정
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
from src.workflows.incoming_ls_workflow import IncomingLSWorkflow


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="Phase-2 LangGraph System")
    parser.add_argument("--meeting", type=str, default="RAN1_120", help="Meeting ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    print("=" * 60)
    print("Phase-2 LangGraph System - Incoming LS Pipeline")
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

    # 2. Workflow 실행
    print("\n[2] Running Pipeline...")
    workflow = IncomingLSWorkflow()
    state = workflow.run(str(meeting.final_minutes_path))

    issues = state.get("issues", [])
    cc_only = state.get("cc_only_items", [])

    # 3. 결과 저장
    print("\n[3] Saving Results...")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    output_file = config.output_dir / f"{meeting.id}_incoming_ls.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(state.get("markdown_output", ""))

    # 4. 결과 요약
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    print(f"  Primary Issues: {len(issues)}")
    print(f"  CC-only Items:  {len(cc_only)}")
    print(f"  Total:          {len(issues) + len(cc_only)}")

    if issues:
        actionable = sum(1 for i in issues if "Actionable" in str(getattr(i, 'issue_type', '')))
        non_action = sum(1 for i in issues if "Non-action" in str(getattr(i, 'issue_type', '')))
        print(f"\n  Issue Types:")
        print(f"    - Actionable: {actionable}")
        print(f"    - Non-action: {non_action}")

    print(f"\n  Output: {output_file}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
