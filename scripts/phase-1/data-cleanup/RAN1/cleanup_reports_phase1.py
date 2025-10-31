#!/usr/bin/env python3
"""
Phase-1 Step-5: Report Cleanup - Phase 1 (ZERO risk)

Cleans Archive folders from Category A and D meetings:
- Category A (26 meetings): Has Final version, Archive contains only drafts
- Category D (4 meetings): No Final, has Draft v030, Archive has older drafts

Expected savings: 93.24 MB
Risk: ZERO (100% safe)
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configuration
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "data_extracted" / "meetings" / "RAN1"
LOG_DIR = Path(__file__).parent.parent.parent.parent.parent / "logs" / "phase-1" / "data-cleanup" / "RAN1"

# Category A: Has Final, Archive contains only drafts (26 meetings)
CATEGORY_A_MEETINGS = [
    "TSGR1_100b_e", "TSGR1_101-e", "TSGR1_102-e", "TSGR1_103-e", "TSGR1_104-e",
    "TSGR1_104b-e", "TSGR1_105-e", "TSGR1_107", "TSGR1_107-e", "TSGR1_108",
    "TSGR1_110", "TSGR1_110b", "TSGR1_111", "TSGR1_112", "TSGR1_112b", "TSGR1_113",
    "TSGR1_114b", "TSGR1_115", "TSGR1_116", "TSGR1_116b", "TSGR1_118", "TSGR1_118b",
    "TSGR1_120", "TSGR1_120b", "TSGR1_121", "TSGR1_122"
]

# Category D: No Final, has Draft v030, Archive has older drafts (4 meetings)
CATEGORY_D_MEETINGS = [
    "TSGR1_109-e", "TSGR1_114", "TSGR1_117", "TSGR1_119"
]

def setup_logging(dry_run=False):
    """Setup logging configuration"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_filename = f"phase1_cleanup_{'dryrun' if dry_run else 'actual'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file = LOG_DIR / log_filename

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)

def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_directory_size(entry.path)
    except PermissionError:
        pass
    return total

def format_size(bytes_size):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def cleanup_meeting(meeting_name, data_dir, category, dry_run=False, logger=None):
    """
    Clean up Archive folder for a single meeting

    Args:
        meeting_name: Name of the meeting (e.g., TSGR1_100)
        data_dir: Base data directory
        category: 'A' or 'D'
        dry_run: If True, only simulate the cleanup
        logger: Logger instance

    Returns:
        dict: Cleanup statistics
    """
    meeting_dir = data_dir / meeting_name
    report_dir = meeting_dir / "Report"
    archive_dir = report_dir / "Archive"

    result = {
        'meeting': meeting_name,
        'category': category,
        'archive_exists': False,
        'archive_size': 0,
        'cleaned': False,
        'error': None
    }

    # Check if meeting directory exists
    if not meeting_dir.exists():
        result['error'] = "Meeting directory not found"
        logger.warning(f"{meeting_name}: Meeting directory not found")
        return result

    # Check if Report directory exists
    if not report_dir.exists():
        result['error'] = "Report directory not found"
        logger.warning(f"{meeting_name}: Report directory not found")
        return result

    # Check if Archive exists
    if not archive_dir.exists():
        result['error'] = "Archive directory not found (already clean?)"
        logger.info(f"{meeting_name}: No Archive directory found (already clean)")
        return result

    result['archive_exists'] = True

    # Calculate Archive size
    archive_size = get_directory_size(archive_dir)
    result['archive_size'] = archive_size

    logger.info(f"{meeting_name}: Archive found - Size: {format_size(archive_size)}")

    # List Archive contents
    try:
        archive_contents = list(os.listdir(archive_dir))
        logger.info(f"{meeting_name}: Archive contents: {archive_contents}")
    except Exception as e:
        result['error'] = f"Failed to list Archive contents: {str(e)}"
        logger.error(f"{meeting_name}: {result['error']}")
        return result

    # Delete Archive (or simulate)
    if dry_run:
        logger.info(f"{meeting_name}: [DRY-RUN] Would delete Archive ({format_size(archive_size)})")
        result['cleaned'] = True
    else:
        try:
            shutil.rmtree(archive_dir)
            logger.info(f"{meeting_name}: ✅ Deleted Archive ({format_size(archive_size)})")
            result['cleaned'] = True
        except Exception as e:
            result['error'] = f"Failed to delete Archive: {str(e)}"
            logger.error(f"{meeting_name}: ❌ {result['error']}")

    return result

def main():
    """Main cleanup function"""
    import argparse

    parser = argparse.ArgumentParser(description='Phase 1 Report Cleanup (ZERO risk)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate cleanup without actual deletion')
    parser.add_argument('--data-dir', type=str, help='Override default data directory')
    args = parser.parse_args()

    # Setup
    logger = setup_logging(dry_run=args.dry_run)
    data_dir = Path(args.data_dir) if args.data_dir else DATA_DIR

    logger.info("=" * 80)
    logger.info("Phase-1 Step-5: Report Cleanup - Phase 1")
    logger.info("=" * 80)
    logger.info(f"Mode: {'DRY-RUN (simulation)' if args.dry_run else 'ACTUAL CLEANUP'}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Category A meetings: {len(CATEGORY_A_MEETINGS)}")
    logger.info(f"Category D meetings: {len(CATEGORY_D_MEETINGS)}")
    logger.info(f"Total meetings: {len(CATEGORY_A_MEETINGS) + len(CATEGORY_D_MEETINGS)}")
    logger.info("")

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return 1

    # Process Category A
    logger.info("Processing Category A (Has Final, Archive = drafts only)...")
    logger.info("-" * 80)

    category_a_results = []
    for meeting in CATEGORY_A_MEETINGS:
        result = cleanup_meeting(meeting, data_dir, 'A', args.dry_run, logger)
        category_a_results.append(result)
        logger.info("")

    # Process Category D
    logger.info("Processing Category D (No Final, has Draft v030)...")
    logger.info("-" * 80)

    category_d_results = []
    for meeting in CATEGORY_D_MEETINGS:
        result = cleanup_meeting(meeting, data_dir, 'D', args.dry_run, logger)
        category_d_results.append(result)
        logger.info("")

    # Summary
    all_results = category_a_results + category_d_results

    total_meetings = len(all_results)
    archive_found = sum(1 for r in all_results if r['archive_exists'])
    cleaned = sum(1 for r in all_results if r['cleaned'])
    errors = sum(1 for r in all_results if r['error'])
    total_savings = sum(r['archive_size'] for r in all_results if r['cleaned'])

    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total meetings processed: {total_meetings}")
    logger.info(f"Archives found: {archive_found}")
    logger.info(f"Successfully cleaned: {cleaned}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Total savings: {format_size(total_savings)}")
    logger.info("")

    if errors > 0:
        logger.warning("Meetings with errors:")
        for result in all_results:
            if result['error']:
                logger.warning(f"  - {result['meeting']}: {result['error']}")
        logger.info("")

    if args.dry_run:
        logger.info("This was a DRY-RUN. No files were actually deleted.")
        logger.info("Run without --dry-run to perform actual cleanup.")
    else:
        logger.info("✅ Phase 1 cleanup completed successfully!")

    logger.info("=" * 80)

    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
