#!/usr/bin/env python3
"""
RAN1 #110-118 배치 실행 스크립트

Usage:
    python batch_run.py                    # 모든 미팅 실행
    python batch_run.py --meetings 110 111 # 특정 미팅만 실행
    python batch_run.py --dry-run          # 실행 없이 계획만 출력
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.config_loader import ConfigLoader
from src.workflows.incoming_ls_workflow import IncomingLSWorkflow

# 실행할 미팅 목록 (110-118)
ALL_MEETINGS = [
    "RAN1_110", "RAN1_110b_e", "RAN1_111", "RAN1_112", "RAN1_112b_e",
    "RAN1_113", "RAN1_114", "RAN1_114b", "RAN1_115", "RAN1_116",
    "RAN1_117", "RAN1_118"
]

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

def run_single_meeting(meeting_id: str, config: ConfigLoader) -> dict:
    """단일 미팅 처리"""
    result = {
        "meeting_id": meeting_id,
        "status": "unknown",
        "primary_issues": 0,
        "cc_only_items": 0,
        "processing_time": 0,
        "error": None,
    }

    start_time = time.time()

    try:
        # Config 로드
        meeting = config.load_meeting(meeting_id)

        if not meeting.final_minutes_path.exists():
            result["status"] = "error"
            result["error"] = f"File not found: {meeting.final_minutes_path}"
            return result

        # Workflow 실행
        workflow = IncomingLSWorkflow()
        state = workflow.run(str(meeting.final_minutes_path))

        issues = state.get("issues", [])
        cc_only = state.get("cc_only_items", [])

        # 결과 저장
        output_file = config.output_dir / f"{meeting.id}_incoming_ls.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(state.get("markdown_output", ""))

        result["status"] = "success"
        result["primary_issues"] = len(issues)
        result["cc_only_items"] = len(cc_only)
        result["output_file"] = str(output_file)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["processing_time"] = round(time.time() - start_time, 1)
    return result

def main():
    parser = argparse.ArgumentParser(description="Batch run LangGraph on multiple meetings")
    parser.add_argument("--meetings", nargs="+", help="Specific meeting numbers (e.g., 110 111)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without execution")
    args = parser.parse_args()

    setup_logging()

    # 실행할 미팅 결정
    if args.meetings:
        meetings = [f"RAN1_{m}" for m in args.meetings]
    else:
        meetings = ALL_MEETINGS

    print("=" * 70)
    print("RAN1 Batch Processing")
    print("=" * 70)
    print(f"Meetings to process: {len(meetings)}")
    for m in meetings:
        print(f"  - {m}")

    if args.dry_run:
        print("\n[DRY RUN] No actual processing performed.")
        return 0

    print("\n" + "-" * 70)

    # Config 로드
    config = ConfigLoader()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_start = time.time()

    for i, meeting_id in enumerate(meetings, 1):
        print(f"\n[{i}/{len(meetings)}] Processing {meeting_id}...")

        result = run_single_meeting(meeting_id, config)
        results.append(result)

        if result["status"] == "success":
            print(f"  ✅ Success: {result['primary_issues']} issues, "
                  f"{result['cc_only_items']} CC-only ({result['processing_time']}s)")
        else:
            print(f"  ❌ Error: {result['error']}")

    total_time = round(time.time() - total_start, 1)

    # 결과 요약
    print("\n" + "=" * 70)
    print("BATCH RESULTS SUMMARY")
    print("=" * 70)

    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"\nTotal: {len(results)} meetings")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Error: {error_count}")
    print(f"  ⏱️  Time: {total_time}s")

    print("\n" + "-" * 70)
    print("DETAILED RESULTS")
    print("-" * 70)
    print(f"{'Meeting':<20} {'Status':<10} {'Issues':<10} {'CC-only':<10} {'Time':<10}")
    print("-" * 70)

    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        issues = str(r["primary_issues"]) if r["status"] == "success" else "-"
        cc_only = str(r["cc_only_items"]) if r["status"] == "success" else "-"
        time_str = f"{r['processing_time']}s"
        print(f"{r['meeting_id']:<20} {status:<10} {issues:<10} {cc_only:<10} {time_str:<10}")

    # 결과 JSON 저장
    summary_file = config.output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_meetings": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "total_time": total_time,
            "results": results,
        }, f, indent=2)

    print(f"\nSummary saved: {summary_file}")
    print("=" * 70)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
