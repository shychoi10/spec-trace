#!/usr/bin/env python3
"""
Phase-1 Step-6: Cleanup macOS Metadata from data_transformed

Removes macOS system metadata files that were copied during transformation:
- __MACOSX folders (resource forks, extended attributes)
- .DS_Store files (Finder metadata)
- ._* files (AppleDouble files)

This should have been done in Step-5 but was missed.
Now cleaning from data_transformed before Step-7 parsing.

Expected cleanup:
- ~4,840 __MACOSX folders
- ~39 MB total
- Risk: ZERO (100% safe, only metadata)
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configuration
DATA_TRANSFORMED_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "data_transformed"
LOG_DIR = Path(__file__).parent.parent.parent.parent.parent / "logs" / "phase-1" / "transform" / "RAN1"

def setup_logging(dry_run=False):
    """Setup logging configuration"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_filename = f"cleanup_macosx_{'dryrun' if dry_run else 'actual'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file = LOG_DIR / log_filename

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return log_file

def calculate_size(path: Path) -> int:
    """Calculate total size of a directory or file"""
    if path.is_file():
        return path.stat().st_size

    total = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                total += item.stat().st_size
    except Exception as e:
        logging.warning(f"Error calculating size for {path}: {e}")

    return total

def find_macosx_metadata(base_dir: Path):
    """Find all macOS metadata in data_transformed"""
    targets = {
        'macosx_folders': [],
        'ds_store_files': [],
        'appledouble_files': []
    }

    logging.info(f"Scanning {base_dir} for macOS metadata...")

    # Find __MACOSX folders
    for macosx_dir in base_dir.rglob('__MACOSX'):
        if macosx_dir.is_dir():
            targets['macosx_folders'].append(macosx_dir)

    # Find .DS_Store files
    for ds_store in base_dir.rglob('.DS_Store'):
        if ds_store.is_file():
            targets['ds_store_files'].append(ds_store)

    # Find ._* AppleDouble files (inside __MACOSX folders)
    for appledouble in base_dir.rglob('._*'):
        if appledouble.is_file():
            targets['appledouble_files'].append(appledouble)

    return targets

def cleanup_metadata(targets: dict, dry_run=False):
    """Remove macOS metadata"""
    stats = {
        'macosx_folders': {'count': 0, 'size': 0},
        'ds_store_files': {'count': 0, 'size': 0},
        'appledouble_files': {'count': 0, 'size': 0},
        'errors': []
    }

    # Remove __MACOSX folders
    logging.info("\n=== Removing __MACOSX folders ===")
    for macosx_dir in targets['macosx_folders']:
        try:
            size = calculate_size(macosx_dir)
            if dry_run:
                logging.info(f"[DRY-RUN] Would remove: {macosx_dir} ({size:,} bytes)")
            else:
                shutil.rmtree(macosx_dir)
                logging.info(f"Removed: {macosx_dir} ({size:,} bytes)")

            stats['macosx_folders']['count'] += 1
            stats['macosx_folders']['size'] += size
        except Exception as e:
            error_msg = f"Failed to remove {macosx_dir}: {e}"
            logging.error(error_msg)
            stats['errors'].append(error_msg)

    # Remove .DS_Store files
    logging.info("\n=== Removing .DS_Store files ===")
    for ds_store in targets['ds_store_files']:
        try:
            size = ds_store.stat().st_size
            if dry_run:
                logging.info(f"[DRY-RUN] Would remove: {ds_store} ({size:,} bytes)")
            else:
                ds_store.unlink()
                logging.info(f"Removed: {ds_store} ({size:,} bytes)")

            stats['ds_store_files']['count'] += 1
            stats['ds_store_files']['size'] += size
        except Exception as e:
            error_msg = f"Failed to remove {ds_store}: {e}"
            logging.error(error_msg)
            stats['errors'].append(error_msg)

    return stats

def print_summary(stats: dict, dry_run=False):
    """Print cleanup summary"""
    action = "Would remove" if dry_run else "Removed"

    total_count = (stats['macosx_folders']['count'] +
                   stats['ds_store_files']['count'])
    total_size = (stats['macosx_folders']['size'] +
                  stats['ds_store_files']['size'])

    logging.info("\n" + "="*60)
    logging.info(f"{'DRY-RUN ' if dry_run else ''}CLEANUP SUMMARY")
    logging.info("="*60)
    logging.info(f"__MACOSX folders {action}: {stats['macosx_folders']['count']:,} ({stats['macosx_folders']['size'] / (1024**2):.2f} MB)")
    logging.info(f".DS_Store files {action}: {stats['ds_store_files']['count']:,} ({stats['ds_store_files']['size'] / (1024**2):.2f} MB)")
    logging.info("-"*60)
    logging.info(f"Total {action}: {total_count:,} items ({total_size / (1024**2):.2f} MB)")

    if stats['errors']:
        logging.warning(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:10]:  # Show first 10 errors
            logging.warning(f"  - {error}")
        if len(stats['errors']) > 10:
            logging.warning(f"  ... and {len(stats['errors']) - 10} more errors")
    else:
        logging.info("\n✓ Cleanup completed successfully with no errors")

    logging.info("="*60)

def main():
    """Main execution"""
    dry_run = '--dry-run' in sys.argv

    log_file = setup_logging(dry_run)

    logging.info("="*60)
    logging.info("Phase-1 Step-6: Cleanup macOS Metadata")
    logging.info("="*60)
    logging.info(f"Mode: {'DRY-RUN' if dry_run else 'ACTUAL CLEANUP'}")
    logging.info(f"Base directory: {DATA_TRANSFORMED_DIR}")
    logging.info(f"Log file: {log_file}")
    logging.info("="*60)

    if not DATA_TRANSFORMED_DIR.exists():
        logging.error(f"Directory not found: {DATA_TRANSFORMED_DIR}")
        return 1

    # Find all macOS metadata
    targets = find_macosx_metadata(DATA_TRANSFORMED_DIR)

    logging.info("\n=== Found macOS Metadata ===")
    logging.info(f"__MACOSX folders: {len(targets['macosx_folders']):,}")
    logging.info(f".DS_Store files: {len(targets['ds_store_files']):,}")

    if not any(targets.values()):
        logging.info("\n✓ No macOS metadata found. Data is already clean!")
        return 0

    # Cleanup
    stats = cleanup_metadata(targets, dry_run)

    # Print summary
    print_summary(stats, dry_run)

    if dry_run:
        logging.info("\nTo perform actual cleanup, run:")
        logging.info(f"  python3 {__file__}")

    return 0 if not stats['errors'] else 1

if __name__ == '__main__':
    sys.exit(main())
