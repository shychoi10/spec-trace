#!/usr/bin/env python3
"""
Extract RAN1 Specifications Data

This script extracts spec ZIP files from data/data_raw/specs/RAN1/ to data/data_extracted/specs/RAN1/

Key Features:
- ZIP files (38XXX-j10.zip) → Extracted to same directory (flat structure)
- Sequential processing (only 5 files)
- Simple progress output
- Error handling for corrupted ZIPs

Usage:
    python extract_specs.py [options]

Options:
    --source PATH       Source directory (default: data/data_raw/specs/RAN1)
    --dest PATH         Destination directory (default: data/data_extracted/specs/RAN1)
    --dry-run           Show what would be done without executing
    --verbose           Show detailed progress

Author: Claude Code
Created: 2025-10-30
"""

import argparse
import logging
import zipfile
from pathlib import Path
from datetime import datetime
import sys


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


def extract_spec_zip(zip_file: Path, dest_dir: Path, logger: logging.Logger) -> bool:
    """
    Extract a spec ZIP file to destination directory (flat extraction)

    Returns: success (True/False)
    """
    try:
        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Extract ZIP to destination directory
        logger.info(f"  Extracting {zip_file.name}...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

        # List extracted files
        extracted_files = list(dest_dir.glob('*'))
        for f in extracted_files:
            if f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                logger.info(f"    ✓ {f.name} ({size_mb:.2f} MB)")

        return True

    except zipfile.BadZipFile:
        logger.error(f"    ✗ Corrupted ZIP file: {zip_file.name}")
        return False
    except Exception as e:
        logger.error(f"    ✗ Error: {e}")
        return False


def run_extraction(source_dir: Path, dest_dir: Path, dry_run: bool,
                   verbose: bool, logger: logging.Logger):
    """
    Main extraction workflow for specifications
    """
    logger.info("=" * 60)
    logger.info("RAN1 Specifications Extraction")
    logger.info("=" * 60)
    logger.info(f"Source: {source_dir}")
    logger.info(f"Destination: {dest_dir}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("")

    # Find all spec ZIP files
    spec_zips = []
    for spec_dir in sorted(source_dir.glob('38.*')):
        for zip_file in spec_dir.glob('*.zip'):
            spec_zips.append(zip_file)

    logger.info(f"Found {len(spec_zips)} specification ZIP files:")
    for zip_file in spec_zips:
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        logger.info(f"  - {zip_file.parent.name}/{zip_file.name} ({size_mb:.2f} MB)")
    logger.info("")

    if dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        logger.info("Would extract:")
        for zip_file in spec_zips:
            rel_path = zip_file.relative_to(source_dir)
            dest_path = dest_dir / rel_path.parent
            logger.info(f"  {zip_file.name} → {dest_path}/")
        return

    # Extract each spec
    logger.info("Extracting specifications...")
    logger.info("")

    start_time = datetime.now()
    success_count = 0
    error_count = 0

    for i, zip_file in enumerate(spec_zips, 1):
        logger.info(f"[{i}/{len(spec_zips)}] {zip_file.parent.name}")

        # Calculate destination
        rel_path = zip_file.relative_to(source_dir)
        dest_path = dest_dir / rel_path.parent

        # Extract
        success = extract_spec_zip(zip_file, dest_path, logger)

        if success:
            success_count += 1
        else:
            error_count += 1

        logger.info("")

    # Final report
    duration = (datetime.now() - start_time).total_seconds()

    logger.info("=" * 60)
    logger.info("Extraction Complete!")
    logger.info("=" * 60)
    logger.info(f"Specs extracted: {success_count}/{len(spec_zips)}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Duration: {duration:.1f} seconds")

    if error_count > 0:
        logger.warning(f"\n{error_count} specification(s) failed to extract. See log for details.")


def main():
    parser = argparse.ArgumentParser(
        description="Extract RAN1 Specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all specs
  python extract_specs.py

  # Dry run to see what would be done
  python extract_specs.py --dry-run

  # Verbose output
  python extract_specs.py --verbose
        """
    )

    parser.add_argument('--source', type=Path,
                        default=Path('data/data_raw/specs/RAN1'),
                        help='Source directory (default: data/data_raw/specs/RAN1)')
    parser.add_argument('--dest', type=Path,
                        default=Path('data/data_extracted/specs/RAN1'),
                        help='Destination directory (default: data/data_extracted/specs/RAN1)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed progress')

    args = parser.parse_args()

    # Setup logging
    log_file = Path('logs/phase-1/specs/RAN1/extraction.log')
    logger = setup_logging(log_file, args.verbose)

    # Validate paths
    if not args.source.exists():
        logger.error(f"Source directory does not exist: {args.source}")
        sys.exit(1)

    # Run extraction
    run_extraction(
        source_dir=args.source,
        dest_dir=args.dest,
        dry_run=args.dry_run,
        verbose=args.verbose,
        logger=logger
    )


if __name__ == '__main__':
    main()
