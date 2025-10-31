#!/usr/bin/env python3
"""
Extract RAN1 Change Requests Data

This script extracts CR ZIP files from data/data_raw/change-requests/RAN1/ to data/data_extracted/change-requests/RAN1/
while preserving the exact directory structure.

Key Features:
- ZIP files (RP-XXXXXX.zip) → Extracted to folders (RP-XXXXXX/)
- Parallel processing (8 workers default)
- Progress tracking
- Error handling for corrupted ZIPs
- Resume capability for interrupted runs

Usage:
    python extract_change_requests.py [options]

Options:
    --source PATH       Source directory (default: data/data_raw/change-requests/RAN1)
    --dest PATH         Destination directory (default: data/data_extracted/change-requests/RAN1)
    --workers N         Number of parallel workers (default: 8)
    --release NAME      Extract only specific release (e.g., Rel-19)
    --resume            Skip already extracted items
    --dry-run           Show what would be done without executing
    --verbose           Show detailed progress

Author: Claude Code
Created: 2025-10-30
"""

import argparse
import logging
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import sys

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warning: tqdm not installed. Using simple progress display.")
    class SimpleTqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total or (len(iterable) if iterable else 0)
            self.desc = desc
            self.n = 0
            self.print_interval = max(1, self.total // 100)

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
            print()

    tqdm = SimpleTqdm


class ExtractionStats:
    """Track extraction statistics"""
    def __init__(self):
        self.zips_extracted = 0
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
            'errors': self.errors,
            'skipped': self.skipped,
            'duration_seconds': self.duration(),
            'errors_list': self.errors_list
        }


def setup_logging(log_file: Path, verbose: bool = False):
    """Setup logging configuration"""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def scan_source_tree(source_dir: Path, target_release: str = None) -> List[Path]:
    """
    Scan source directory and build list of ZIP files to extract

    Returns list of ZIP file paths
    """
    zip_files = []

    # Find all ZIP files in TSG folders
    for release_dir in source_dir.glob('Rel-*/TSG'):
        # Filter by release if specified
        if target_release:
            if release_dir.parent.name != target_release:
                continue

        # Add all ZIP files
        for zip_file in release_dir.glob('*.zip'):
            zip_files.append(zip_file)

    return sorted(zip_files)


def get_dest_path(source_file: Path, source_dir: Path, dest_dir: Path) -> Path:
    """
    Calculate destination path for a source ZIP file

    RP-191281.zip → RP-191281/ (folder)
    """
    relative_path = source_file.relative_to(source_dir)
    parent = relative_path.parent
    stem = source_file.stem  # filename without .zip
    return dest_dir / parent / stem


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


def process_zip(zip_file: Path, source_dir: Path, dest_dir: Path,
                resume: bool, stats: ExtractionStats) -> str:
    """
    Process a single ZIP file (extract)

    Returns: status message for logging
    """
    # Calculate destination path
    dest_path = get_dest_path(zip_file, source_dir, dest_dir)

    # Extract
    success, error = extract_zip_file(zip_file, dest_path, resume)

    if success:
        if "skipped" in error:
            stats.skipped += 1
        else:
            stats.zips_extracted += 1
        return f"EXTRACT: {zip_file.name} → {dest_path.name}/"
    else:
        stats.add_error(zip_file, error)
        return f"ERROR: {zip_file.name} - {error}"


def run_extraction(source_dir: Path, dest_dir: Path, workers: int,
                   target_release: str, resume: bool, dry_run: bool,
                   verbose: bool, logger: logging.Logger):
    """
    Main extraction workflow
    """
    logger.info("=" * 60)
    logger.info("RAN1 Change Requests Extraction")
    logger.info("=" * 60)
    logger.info(f"Source: {source_dir}")
    logger.info(f"Destination: {dest_dir}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Target release: {target_release or 'ALL'}")
    logger.info(f"Resume mode: {resume}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("")

    # Step 1: Scan source tree
    logger.info("Step 1: Scanning source directory...")
    zip_files = scan_source_tree(source_dir, target_release)

    # Count by release
    release_counts = {}
    for zip_file in zip_files:
        release = zip_file.parent.parent.name
        release_counts[release] = release_counts.get(release, 0) + 1

    logger.info(f"Found {len(zip_files)} ZIP files:")
    for release, count in sorted(release_counts.items()):
        logger.info(f"  - {release}: {count} ZIPs")
    logger.info("")

    if dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        logger.info("Sample operations:")
        for zip_file in zip_files[:10]:
            dest = get_dest_path(zip_file, source_dir, dest_dir)
            logger.info(f"  EXTRACT: {zip_file.name} → {dest}")
        return

    # Step 2: Process ZIPs in parallel
    logger.info(f"Step 2: Processing {len(zip_files)} ZIP files with {workers} workers...")

    stats = ExtractionStats()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_zip, zip_file, source_dir, dest_dir, resume, stats): zip_file
            for zip_file in zip_files
        }

        # Process with progress bar
        with tqdm(total=len(zip_files), desc="Extracting", unit="files") as pbar:
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
        description="Extract RAN1 Change Requests data while preserving directory structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all CRs with 8 workers
  python extract_change_requests.py --workers 8

  # Extract single release for testing
  python extract_change_requests.py --release Rel-19

  # Resume interrupted extraction
  python extract_change_requests.py --resume

  # Dry run to see what would be done
  python extract_change_requests.py --dry-run
        """
    )

    parser.add_argument('--source', type=Path,
                        default=Path('data/data_raw/change-requests/RAN1'),
                        help='Source directory (default: data/data_raw/change-requests/RAN1)')
    parser.add_argument('--dest', type=Path,
                        default=Path('data/data_extracted/change-requests/RAN1'),
                        help='Destination directory (default: data/data_extracted/change-requests/RAN1)')
    parser.add_argument('--workers', type=int, default=8,
                        help='Number of parallel workers (default: 8)')
    parser.add_argument('--release', type=str, default=None,
                        help='Extract only specific release (e.g., Rel-19)')
    parser.add_argument('--resume', action='store_true',
                        help='Skip already extracted items')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed progress')

    args = parser.parse_args()

    # Setup logging
    log_file = Path('logs/phase-1/change-requests/RAN1/extraction.log')
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
        target_release=args.release,
        resume=args.resume,
        dry_run=args.dry_run,
        verbose=args.verbose,
        logger=logger
    )


if __name__ == '__main__':
    main()
