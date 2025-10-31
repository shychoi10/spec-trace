#!/usr/bin/env python3
"""
Extract RAN1 Meetings Data

This script extracts ZIP files from data/data_raw/meetings/RAN1/ to data/data_extracted/meetings/RAN1/
while preserving the exact directory structure.

Key Features:
- ZIP files (xxx.zip) → Extracted to folders (xxx/)
- Regular files (XLSX, XLSM, etc.) → Copied as-is
- Parallel processing (8 workers default)
- Progress tracking with tqdm
- Error handling for corrupted ZIPs
- Resume capability for interrupted runs

Usage:
    python extract_meetings.py [options]

Options:
    --source PATH       Source directory (default: data/data_raw/meetings/RAN1)
    --dest PATH         Destination directory (default: data/data_extracted/meetings/RAN1)
    --workers N         Number of parallel workers (default: 8)
    --meeting NAME      Extract only specific meeting (e.g., TSGR1_100)
    --resume            Skip already extracted items
    --dry-run           Show what would be done without executing
    --verbose           Show detailed progress

Author: Claude Code
Created: 2025-10-30
"""

import argparse
import logging
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import sys

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warning: tqdm not installed. Using simple progress display.")
    # Fallback: simple progress without context manager
    class SimpleTqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total or (len(iterable) if iterable else 0)
            self.desc = desc
            self.n = 0
            self.print_interval = max(1, self.total // 100)  # Update every 1%

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

        def __iter__(self):
            for item in self.iterable:
                yield item
                self.update(1)

        def update(self, n=1):
            self.n += n
            if self.total > 0 and (self.n % self.print_interval == 0 or self.n == self.total):
                pct = (self.n / self.total) * 100
                print(f"\r{self.desc}: {self.n}/{self.total} ({pct:.1f}%)", end='', flush=True)

        def close(self):
            print()  # New line after progress

    tqdm = SimpleTqdm

# Optional RAR support
try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    RAR_SUPPORT = False


class ExtractionStats:
    """Track extraction statistics"""
    def __init__(self):
        self.zips_extracted = 0
        self.files_copied = 0
        self.errors = 0
        self.skipped = 0
        self.start_time = datetime.now()
        self.errors_list = []

    def add_error(self, path: Path, error: str):
        self.errors += 1
        self.errors_list.append((str(path), error))

    def duration(self):
        return (datetime.now() - self.start_time).total_seconds()

    def summary(self):
        return {
            'zips_extracted': self.zips_extracted,
            'files_copied': self.files_copied,
            'errors': self.errors,
            'skipped': self.skipped,
            'duration_seconds': self.duration(),
            'errors_list': self.errors_list
        }


def setup_logging(log_file: Path, verbose: bool = False):
    """Setup logging configuration"""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # File handler - always detailed
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler - varies by verbose flag
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def scan_source_tree(source_dir: Path, target_meeting: str = None) -> List[Tuple[Path, str]]:
    """
    Scan source directory and build list of (file_path, action) tuples

    Actions: 'extract_zip', 'copy_file', 'skip'
    """
    items = []

    # Walk through all files
    for file_path in source_dir.rglob('*'):
        if not file_path.is_file():
            continue

        # Filter by meeting if specified
        if target_meeting:
            if not any(target_meeting == part for part in file_path.parts):
                continue

        # Determine action based on file type
        suffix = file_path.suffix.lower()

        if suffix == '.zip':
            items.append((file_path, 'extract_zip'))
        elif suffix == '.rar':
            if RAR_SUPPORT:
                items.append((file_path, 'extract_rar'))
            else:
                items.append((file_path, 'skip'))
                logging.warning(f"RAR support not available, skipping: {file_path.name}")
        elif suffix in ['.xlsx', '.xlsm', '.xls', '.doc', '.docx', '.pdf', '.ppt', '.pptx']:
            items.append((file_path, 'copy_file'))
        elif suffix in ['.tmp', '.md'] or '__MACOSX' in str(file_path):
            items.append((file_path, 'skip'))
        else:
            # Unknown file type - copy as-is
            items.append((file_path, 'copy_file'))
            logging.debug(f"Unknown file type, will copy: {file_path.name}")

    return items


def get_dest_path(source_file: Path, source_dir: Path, dest_dir: Path, action: str) -> Path:
    """
    Calculate destination path for a source file

    For ZIP files: xxx.zip → xxx/
    For other files: preserve exact path
    """
    relative_path = source_file.relative_to(source_dir)

    if action in ['extract_zip', 'extract_rar']:
        # Remove extension and create directory path
        # e.g., TSGR1_84/Docs/R1-123456.zip → TSGR1_84/Docs/R1-123456/
        parent = relative_path.parent
        stem = source_file.stem  # filename without extension
        return dest_dir / parent / stem
    else:
        # Regular file - preserve path
        return dest_dir / relative_path


def extract_zip_file(source_file: Path, dest_dir: Path, resume: bool) -> Tuple[bool, str]:
    """
    Extract a single ZIP file to destination directory

    Returns: (success, error_message)
    """
    try:
        # Check if already extracted (resume mode)
        if resume and dest_dir.exists() and any(dest_dir.iterdir()):
            return (True, "skipped (already exists)")

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Extract ZIP
        with zipfile.ZipFile(source_file, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

        return (True, "")

    except zipfile.BadZipFile:
        return (False, "Corrupted ZIP file")
    except PermissionError as e:
        return (False, f"Permission denied: {e}")
    except Exception as e:
        return (False, f"Unexpected error: {e}")


def extract_rar_file(source_file: Path, dest_dir: Path, resume: bool) -> Tuple[bool, str]:
    """
    Extract a single RAR file to destination directory

    Returns: (success, error_message)
    """
    if not RAR_SUPPORT:
        return (False, "RAR support not available (install rarfile)")

    try:
        # Check if already extracted (resume mode)
        if resume and dest_dir.exists() and any(dest_dir.iterdir()):
            return (True, "skipped (already exists)")

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Extract RAR
        with rarfile.RarFile(source_file, 'r') as rar_ref:
            rar_ref.extractall(dest_dir)

        return (True, "")

    except Exception as e:
        return (False, f"RAR extraction failed: {e}")


def copy_file(source_file: Path, dest_file: Path, resume: bool) -> Tuple[bool, str]:
    """
    Copy a regular file to destination

    Returns: (success, error_message)
    """
    try:
        # Check if already copied (resume mode)
        if resume and dest_file.exists():
            return (True, "skipped (already exists)")

        # Create destination directory
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source_file, dest_file)

        return (True, "")

    except Exception as e:
        return (False, f"Copy failed: {e}")


def process_item(item: Tuple[Path, str], source_dir: Path, dest_dir: Path,
                 resume: bool, stats: ExtractionStats) -> str:
    """
    Process a single item (extract ZIP or copy file)

    Returns: status message for logging
    """
    source_file, action = item

    if action == 'skip':
        stats.skipped += 1
        return f"SKIP: {source_file.name}"

    # Calculate destination path
    dest_path = get_dest_path(source_file, source_dir, dest_dir, action)

    # Execute action
    if action == 'extract_zip':
        success, error = extract_zip_file(source_file, dest_path, resume)
        if success:
            stats.zips_extracted += 1
            return f"EXTRACT: {source_file.name} → {dest_path.name}/"
        else:
            stats.add_error(source_file, error)
            return f"ERROR: {source_file.name} - {error}"

    elif action == 'extract_rar':
        success, error = extract_rar_file(source_file, dest_path, resume)
        if success:
            stats.zips_extracted += 1
            return f"EXTRACT (RAR): {source_file.name} → {dest_path.name}/"
        else:
            stats.add_error(source_file, error)
            return f"ERROR: {source_file.name} - {error}"

    elif action == 'copy_file':
        success, error = copy_file(source_file, dest_path, resume)
        if success:
            stats.files_copied += 1
            return f"COPY: {source_file.name}"
        else:
            stats.add_error(source_file, error)
            return f"ERROR: {source_file.name} - {error}"

    else:
        stats.add_error(source_file, f"Unknown action: {action}")
        return f"ERROR: Unknown action {action} for {source_file.name}"


def run_extraction(source_dir: Path, dest_dir: Path, workers: int,
                   target_meeting: str, resume: bool, dry_run: bool,
                   verbose: bool, logger: logging.Logger):
    """
    Main extraction workflow
    """
    logger.info("=" * 60)
    logger.info("RAN1 Meetings Extraction")
    logger.info("=" * 60)
    logger.info(f"Source: {source_dir}")
    logger.info(f"Destination: {dest_dir}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Target meeting: {target_meeting or 'ALL'}")
    logger.info(f"Resume mode: {resume}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("")

    # Step 1: Scan source tree
    logger.info("Step 1: Scanning source directory...")
    items = scan_source_tree(source_dir, target_meeting)

    # Count by action
    action_counts = {}
    for _, action in items:
        action_counts[action] = action_counts.get(action, 0) + 1

    logger.info(f"Found {len(items)} items:")
    for action, count in sorted(action_counts.items()):
        logger.info(f"  - {action}: {count}")
    logger.info("")

    if dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        logger.info("Sample operations:")
        for item, action in items[:10]:
            dest = get_dest_path(item, source_dir, dest_dir, action)
            logger.info(f"  {action}: {item.name} → {dest}")
        return

    # Step 2: Process items in parallel
    logger.info(f"Step 2: Processing {len(items)} items with {workers} workers...")

    stats = ExtractionStats()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_item, item, source_dir, dest_dir, resume, stats): item
            for item in items
        }

        # Process with progress bar
        with tqdm(total=len(items), desc="Extracting", unit="files") as pbar:
            for future in as_completed(futures):
                result = future.result()
                if verbose:
                    logger.debug(result)
                pbar.update(1)

    # Step 3: Final report
    logger.info("")
    logger.info("=" * 60)
    logger.info("Extraction Complete!")
    logger.info("=" * 60)
    logger.info(f"ZIPs extracted: {stats.zips_extracted}")
    logger.info(f"Files copied: {stats.files_copied}")
    logger.info(f"Skipped: {stats.skipped}")
    logger.info(f"Errors: {stats.errors}")
    logger.info(f"Duration: {stats.duration():.1f} seconds")

    if stats.errors > 0:
        logger.info("")
        logger.info("Errors encountered:")
        for path, error in stats.errors_list[:10]:  # Show first 10
            logger.info(f"  - {path}: {error}")
        if len(stats.errors_list) > 10:
            logger.info(f"  ... and {len(stats.errors_list) - 10} more (see log file)")


def main():
    parser = argparse.ArgumentParser(
        description="Extract RAN1 Meetings data while preserving directory structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all meetings with 8 workers
  python extract_meetings.py --workers 8

  # Extract single meeting for testing
  python extract_meetings.py --meeting TSGR1_100

  # Resume interrupted extraction
  python extract_meetings.py --resume

  # Dry run to see what would be done
  python extract_meetings.py --dry-run
        """
    )

    parser.add_argument('--source', type=Path,
                        default=Path('data/data_raw/meetings/RAN1'),
                        help='Source directory (default: data/data_raw/meetings/RAN1)')
    parser.add_argument('--dest', type=Path,
                        default=Path('data/data_extracted/meetings/RAN1'),
                        help='Destination directory (default: data/data_extracted/meetings/RAN1)')
    parser.add_argument('--workers', type=int, default=8,
                        help='Number of parallel workers (default: 8)')
    parser.add_argument('--meeting', type=str, default=None,
                        help='Extract only specific meeting (e.g., TSGR1_100)')
    parser.add_argument('--resume', action='store_true',
                        help='Skip already extracted items')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed progress')

    args = parser.parse_args()

    # Setup logging
    log_file = Path('logs/phase-1/meetings/RAN1/extraction.log')
    logger = setup_logging(log_file, args.verbose)

    # Validate paths
    if not args.source.exists():
        logger.error(f"Source directory does not exist: {args.source}")
        sys.exit(1)

    # Run extraction
    run_extraction(
        source_dir=args.source,
        dest_dir=args.dest,
        workers=args.workers,
        target_meeting=args.meeting,
        resume=args.resume,
        dry_run=args.dry_run,
        verbose=args.verbose,
        logger=logger
    )


if __name__ == '__main__':
    main()
