#!/usr/bin/env python3
"""
Phase-1 Step-4 Sub-step 6: Advanced Multi-tool ZIP Recovery

복구 전략:
1. 7z (return code 2 허용 - Warning but success)
2. file 명령으로 RAR 감지
3. unrar (RAR 파일인 경우)
4. Empty archive 확인

예상 복구: 17-26개 / 44개 (38.6% - 59.1%)
"""

import json
import subprocess
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import logging

# 설정
BASE_DIR = Path("/home/sihyeon/workspace/spec-trace")
DATA_RAW = BASE_DIR / "data/data_raw/meetings/RAN1"
DATA_EXTRACTED = BASE_DIR / "data/data_extracted/meetings/RAN1"
LOG_DIR = BASE_DIR / "logs/phase-1/meetings/RAN1"
LOG_FILE = LOG_DIR / "advanced_recovery.log"
REPORT_FILE = LOG_DIR / "advanced_recovery_report.json"

# 기존 실패 리포트
FAILED_REPORT = LOG_DIR / "empty_zip_recovery_report.json"

# 병렬 처리 workers
MAX_WORKERS = 8

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


def load_failed_zips():
    """기존 실패 ZIP 목록 로드"""
    with open(FAILED_REPORT, 'r') as f:
        report = json.load(f)

    failed_list = []
    for item in report['failed_details']:
        zip_rel_path = item['zip']
        error = item['error']
        failed_list.append({
            'relative_path': zip_rel_path,
            'full_path': DATA_RAW / zip_rel_path,
            'output_dir': DATA_EXTRACTED / zip_rel_path.replace('.zip', ''),
            'original_error': error
        })

    logger.info(f"Loaded {len(failed_list)} failed ZIPs from report")
    return failed_list


def count_files(directory):
    """디렉토리 내 파일 수 카운트"""
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.rglob('*') if _.is_file())


def check_file_type(zip_path):
    """file 명령으로 실제 파일 타입 확인"""
    try:
        result = subprocess.run(
            ['file', str(zip_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def try_7z_tolerant(zip_path, output_dir):
    """
    7z 추출 (return code 2 허용)

    7z return codes:
    0 = Success
    1 = Warning (non-fatal errors)
    2 = Fatal error

    하지만 실제로는 return code 2여도 파일이 추출될 수 있음
    """
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ['7z', 'x', str(zip_path), f'-o{output_dir}', '-y']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        # 파일이 추출되었는지 확인
        file_count = count_files(output_dir)

        if file_count > 0:
            # 파일이 있으면 성공
            return {
                'success': True,
                'tool': '7z',
                'files': file_count,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            # 파일이 없으면 실패
            return {
                'success': False,
                'tool': '7z',
                'files': 0,
                'returncode': result.returncode,
                'error': result.stderr if result.stderr else "No files extracted"
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'tool': '7z',
            'files': 0,
            'error': 'Timeout (120s)'
        }
    except Exception as e:
        return {
            'success': False,
            'tool': '7z',
            'files': 0,
            'error': str(e)
        }


def try_unrar(zip_path, output_dir):
    """unrar 추출 (RAR 파일용)"""
    # unrar 설치 여부 확인
    if not shutil.which('unrar'):
        return {
            'success': False,
            'tool': 'unrar',
            'files': 0,
            'error': 'unrar not installed'
        }

    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ['unrar', 'x', '-y', str(zip_path), str(output_dir) + '/']

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        file_count = count_files(output_dir)

        if result.returncode == 0 and file_count > 0:
            return {
                'success': True,
                'tool': 'unrar',
                'files': file_count,
                'returncode': result.returncode,
                'stdout': result.stdout
            }
        else:
            return {
                'success': False,
                'tool': 'unrar',
                'files': file_count,
                'returncode': result.returncode,
                'error': result.stderr if result.stderr else "Extraction failed"
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'tool': 'unrar',
            'files': 0,
            'error': 'Timeout (120s)'
        }
    except Exception as e:
        return {
            'success': False,
            'tool': 'unrar',
            'files': 0,
            'error': str(e)
        }


def extract_with_fallback(zip_info):
    """다중 도구 복구 전략"""
    zip_path = zip_info['full_path']
    output_dir = zip_info['output_dir']
    original_error = zip_info['original_error']

    logger.info(f"Processing: {zip_info['relative_path']}")

    # 파일 존재 확인
    if not zip_path.exists():
        return {
            'zip': zip_info['relative_path'],
            'success': False,
            'tool': 'none',
            'files': 0,
            'error': 'ZIP file not found',
            'original_error': original_error
        }

    # 파일 크기 확인
    file_size = zip_path.stat().st_size
    if file_size == 0:
        return {
            'zip': zip_info['relative_path'],
            'success': False,
            'tool': 'none',
            'files': 0,
            'error': 'Zero byte file',
            'file_size': 0,
            'original_error': original_error
        }

    # 파일 타입 확인
    file_type = check_file_type(zip_path)

    # Strategy 1: 7z (가장 관대한 파서)
    logger.info(f"  Trying 7z (tolerant mode)...")
    result = try_7z_tolerant(zip_path, output_dir)

    if result['success']:
        logger.info(f"  ✓ 7z succeeded: {result['files']} files extracted")
        return {
            'zip': zip_info['relative_path'],
            'success': True,
            'tool': '7z',
            'files': result['files'],
            'file_size': file_size,
            'file_type': file_type,
            'returncode': result.get('returncode'),
            'original_error': original_error
        }
    else:
        logger.info(f"  ✗ 7z failed: {result.get('error', 'Unknown')}")

    # Strategy 2: unrar (RAR 파일인 경우)
    if 'RAR archive' in file_type:
        logger.info(f"  RAR file detected, trying unrar...")
        result = try_unrar(zip_path, output_dir)

        if result['success']:
            logger.info(f"  ✓ unrar succeeded: {result['files']} files extracted")
            return {
                'zip': zip_info['relative_path'],
                'success': True,
                'tool': 'unrar',
                'files': result['files'],
                'file_size': file_size,
                'file_type': file_type,
                'returncode': result.get('returncode'),
                'original_error': original_error
            }
        else:
            logger.info(f"  ✗ unrar failed: {result.get('error', 'Unknown')}")

    # 모든 전략 실패
    logger.info(f"  ✗ All recovery methods failed")
    return {
        'zip': zip_info['relative_path'],
        'success': False,
        'tool': 'all_failed',
        'files': 0,
        'file_size': file_size,
        'file_type': file_type,
        'error': result.get('error', 'All methods failed'),
        'original_error': original_error
    }


def main():
    """메인 실행 함수"""
    logger.info("="*80)
    logger.info("Phase-1 Step-4 Sub-step 6: Advanced Multi-tool ZIP Recovery")
    logger.info("="*80)

    start_time = datetime.now()

    # 기존 실패 ZIP 로드
    failed_zips = load_failed_zips()
    total_zips = len(failed_zips)

    logger.info(f"Target: {total_zips} failed ZIPs")
    logger.info(f"Workers: {MAX_WORKERS}")
    logger.info(f"Start time: {start_time}")
    logger.info("")

    # unrar 설치 확인
    has_unrar = shutil.which('unrar') is not None
    logger.info(f"unrar available: {has_unrar}")
    if not has_unrar:
        logger.warning("unrar not installed - RAR files will not be recovered")
    logger.info("")

    # 병렬 처리
    results = []
    success_count = 0
    failed_count = 0

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(extract_with_fallback, zip_info): zip_info
            for zip_info in failed_zips
        }

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)

            if result['success']:
                success_count += 1
            else:
                failed_count += 1

            logger.info(f"Progress: {i}/{total_zips} ({i*100//total_zips}%) - "
                       f"Success: {success_count}, Failed: {failed_count}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 통계 계산
    success_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    total_files_recovered = sum(r['files'] for r in success_results)

    # 도구별 통계
    tool_stats = {}
    for r in success_results:
        tool = r['tool']
        if tool not in tool_stats:
            tool_stats[tool] = {'count': 0, 'files': 0}
        tool_stats[tool]['count'] += 1
        tool_stats[tool]['files'] += r['files']

    # 실패 원인 분석
    failure_reasons = {}
    for r in failed_results:
        error = r.get('error', 'Unknown')
        # 간략화
        if 'Zero byte' in error:
            reason = 'Zero byte file'
        elif 'No files extracted' in error or '7zip succeeded but no files' in r.get('original_error', ''):
            reason = 'Empty archive'
        elif 'RAR archive' in r.get('file_type', ''):
            reason = 'RAR file (unrar not installed)' if not has_unrar else 'RAR extraction failed'
        elif 'Wrong password' in r.get('original_error', ''):
            reason = 'Password protected'
        elif 'Can not open' in error:
            reason = 'Cannot open as archive'
        else:
            reason = 'Other error'

        if reason not in failure_reasons:
            failure_reasons[reason] = []
        failure_reasons[reason].append(r['zip'])

    # 리포트 생성
    report = {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration,
        'total_attempts': total_zips,
        'success': success_count,
        'failed': failed_count,
        'success_rate': f"{success_count*100/total_zips:.1f}%",
        'total_files_recovered': total_files_recovered,
        'unrar_available': has_unrar,
        'tool_statistics': tool_stats,
        'failure_reasons': {k: len(v) for k, v in failure_reasons.items()},
        'success_details': success_results,
        'failed_details': failed_results,
        'failure_breakdown': failure_reasons
    }

    # 리포트 저장
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 결과 출력
    logger.info("")
    logger.info("="*80)
    logger.info("Recovery Results Summary")
    logger.info("="*80)
    logger.info(f"Total attempts: {total_zips}")
    logger.info(f"Success: {success_count} ({success_count*100/total_zips:.1f}%)")
    logger.info(f"Failed: {failed_count} ({failed_count*100/total_zips:.1f}%)")
    logger.info(f"Files recovered: {total_files_recovered}")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("")

    logger.info("Tool Statistics:")
    for tool, stats in tool_stats.items():
        logger.info(f"  {tool}: {stats['count']} ZIPs, {stats['files']} files")
    logger.info("")

    logger.info("Failure Reasons:")
    for reason, count in failure_reasons.items():
        logger.info(f"  {reason}: {count} ZIPs")
    logger.info("")

    logger.info(f"Report saved: {REPORT_FILE}")
    logger.info(f"Log saved: {LOG_FILE}")
    logger.info("")

    if not has_unrar:
        rar_count = len([r for r in failed_results if 'RAR archive' in r.get('file_type', '')])
        if rar_count > 0:
            logger.warning(f"Note: {rar_count} RAR files detected but unrar not installed")
            logger.warning("Install unrar to recover these files:")
            logger.warning("  sudo apt install -y unrar")
            logger.warning("")

    logger.info("="*80)
    logger.info("Recovery Complete!")
    logger.info("="*80)


if __name__ == '__main__':
    main()
