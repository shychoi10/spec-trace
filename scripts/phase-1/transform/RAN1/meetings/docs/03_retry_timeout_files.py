#!/usr/bin/env python3
"""
Phase-1 Step-6 Sub-step 4: Retry TIMEOUT DOC Files

LibreOffice timeout 연장 (30s → 120s)로 재변환 시도

Target: 13개 TIMEOUT 파일
"""

import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import logging

# 설정
BASE_DIR = Path("/home/sihyeon/workspace/spec-trace")
DATA_EXTRACTED = BASE_DIR / "data/data_extracted/meetings/RAN1"
DATA_TRANSFORMED = BASE_DIR / "data/data_transformed/meetings/RAN1"
LOG_DIR = BASE_DIR / "logs/phase-1/transform/RAN1/meetings/docs"
LOG_FILE = LOG_DIR / "timeout_retry.log"
REPORT_FILE = LOG_DIR / "timeout_retry_report.json"

# 기존 통계 파일
STATS_FILE = LOG_DIR / "transform_complete_stats.json"

# LibreOffice timeout (기존 30s → 120s)
TIMEOUT_SECONDS = 120

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_timeout_files():
    """기존 TIMEOUT 파일 목록 로드"""
    with open(STATS_FILE, 'r') as f:
        stats = json.load(f)

    timeout_files = stats.get('timeout_files', [])
    logger.info(f"Loaded {len(timeout_files)} timeout files from stats")

    # Path 객체로 변환
    timeout_list = []
    for file_path_str in timeout_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            # 출력 경로 계산
            rel_path = file_path.relative_to(DATA_EXTRACTED)
            output_path = DATA_TRANSFORMED / rel_path.with_suffix('.docx')

            timeout_list.append({
                'input': file_path,
                'output': output_path,
                'filename': file_path.name
            })
        else:
            logger.warning(f"File not found: {file_path}")

    logger.info(f"Found {len(timeout_list)} timeout files to retry")
    return timeout_list


def convert_doc_to_docx(doc_path, output_path, timeout=120):
    """
    LibreOffice로 DOC → DOCX 변환 (timeout 연장)

    Args:
        doc_path: 입력 DOC 파일 경로
        output_path: 출력 DOCX 파일 경로
        timeout: Timeout 초 (기본 120초)

    Returns:
        {'success': bool, 'error': str}
    """
    # LibreOffice 설치 확인
    if not shutil.which('soffice'):
        return {'success': False, 'error': 'LibreOffice not installed'}

    # 출력 디렉토리 생성
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 변환 명령
    cmd = [
        'soffice',
        '--headless',
        '--convert-to', 'docx',
        '--outdir', str(output_dir),
        str(doc_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # 출력 파일 확인
        if output_path.exists():
            file_size = output_path.stat().st_size
            return {
                'success': True,
                'file_size': file_size,
                'returncode': result.returncode,
                'stdout': result.stdout
            }
        else:
            return {
                'success': False,
                'error': 'Output file not created',
                'returncode': result.returncode,
                'stderr': result.stderr
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'TIMEOUT ({timeout}s) - process killed'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """메인 실행 함수"""
    logger.info("="*80)
    logger.info("Phase-1 Step-6 Sub-step 4: Retry TIMEOUT DOC Files")
    logger.info("="*80)

    start_time = datetime.now()

    # TIMEOUT 파일 로드
    timeout_files = load_timeout_files()
    total_files = len(timeout_files)

    logger.info(f"Target: {total_files} timeout DOC files")
    logger.info(f"Timeout: {TIMEOUT_SECONDS} seconds (extended from 30s)")
    logger.info(f"Start time: {start_time}")
    logger.info("")

    # LibreOffice 설치 확인
    if not shutil.which('soffice'):
        logger.error("LibreOffice not installed!")
        logger.error("Install: sudo apt install libreoffice-writer")
        return

    # 변환 시도
    results = []
    success_count = 0
    failed_count = 0
    still_timeout = []

    for i, file_info in enumerate(timeout_files, 1):
        input_path = file_info['input']
        output_path = file_info['output']
        filename = file_info['filename']

        logger.info(f"[{i}/{total_files}] Converting: {filename}")

        result = convert_doc_to_docx(input_path, output_path, TIMEOUT_SECONDS)

        if result['success']:
            success_count += 1
            logger.info(f"  ✓ Success: {result['file_size']} bytes")
            results.append({
                'filename': filename,
                'input': str(input_path),
                'output': str(output_path),
                'success': True,
                'file_size': result['file_size']
            })
        else:
            failed_count += 1
            error = result['error']
            logger.info(f"  ✗ Failed: {error}")

            if 'TIMEOUT' in error:
                still_timeout.append(str(input_path))

            results.append({
                'filename': filename,
                'input': str(input_path),
                'output': str(output_path),
                'success': False,
                'error': error
            })

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 리포트 생성
    report = {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration,
        'timeout_setting': TIMEOUT_SECONDS,
        'total_files': total_files,
        'success': success_count,
        'failed': failed_count,
        'still_timeout': len(still_timeout),
        'success_rate': f"{success_count*100/total_files:.1f}%" if total_files > 0 else "0%",
        'results': results,
        'still_timeout_files': still_timeout
    }

    # 리포트 저장
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 결과 출력
    logger.info("")
    logger.info("="*80)
    logger.info("Retry Results Summary")
    logger.info("="*80)
    logger.info(f"Total files: {total_files}")
    logger.info(f"Success: {success_count} ({success_count*100/total_files:.1f}%)")
    logger.info(f"Failed: {failed_count} ({failed_count*100/total_files:.1f}%)")
    if still_timeout:
        logger.info(f"Still timeout: {len(still_timeout)}")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("")

    if still_timeout:
        logger.warning("Files still timeout after 120s:")
        for f in still_timeout:
            logger.warning(f"  - {Path(f).name}")
        logger.warning("")
        logger.warning("These files are extremely large LTE spec drafts")
        logger.warning("Consider manual conversion or skip them")
        logger.warning("")

    logger.info(f"Report saved: {REPORT_FILE}")
    logger.info(f"Log saved: {LOG_FILE}")
    logger.info("")

    logger.info("="*80)
    logger.info("Retry Complete!")
    logger.info("="*80)


if __name__ == '__main__':
    main()
