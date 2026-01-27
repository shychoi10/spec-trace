"""
HybridReportParser vs Phase-3 전체 비교 검증

목적: HybridReportParser가 Phase-3 기존 결과와 텍스트 레벨에서 100% 호환되는지 검증
- Decision ID 일치 여부
- Content (para.text 기반) 완전 일치 여부
- Decision 수 일치 여부
- 수식 추출 품질 통계 (부가)

사용 파서: HybridReportParser (hybrid_parser.py)
  - Phase-3 ReportParser를 내부 사용 → decision_id, content 동일 보장
  - content_raw, equations 추가 (Phase-3 대비 확장)
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from hybrid_parser import HybridReportParser, compare_with_phase3


DOCX_DIR = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report")
PHASE3_DIR = Path("/home/sihyeon/workspace/spec-trace/ontology/output/parsed_reports")
OUTPUT_DIR = Path(__file__).parent / "output"


def run_single_meeting(docx_path: Path, phase3_path: Path) -> dict:
    """단일 미팅 검증"""
    meeting = docx_path.stem.replace('Final_Report_RAN1-', '')
    meeting_id = f"RAN1-{meeting}"

    start = time.time()
    try:
        parser = HybridReportParser(docx_path)
        report, enriched, eq_stats = parser.parse()
        elapsed = time.time() - start

        # Phase-3 비교
        comparison = compare_with_phase3(enriched, phase3_path)

        return {
            'meeting': meeting_id,
            'status': 'success',
            'elapsed': round(elapsed, 1),
            # Phase-3 비교
            'phase3_total': comparison['phase3_total'],
            'hybrid_total': comparison['hybrid_total'],
            'common': comparison['common'],
            'content_exact_match': comparison['content_exact_match'],
            'content_mismatch': comparison['content_mismatch'],
            'phase3_only': comparison['phase3_only'],
            'hybrid_only': comparison['hybrid_only'],
            'mismatches': comparison['mismatches'],
            # 수식 통계
            'total_equations': eq_stats['total_equations_in_decisions'],
            'valid': eq_stats['valid'],
            'invalid': eq_stats['invalid'],
            'offset_exact': eq_stats['offset_exact'],
            'offset_failed': eq_stats['offset_failed'],
            'decisions_with_equations': eq_stats['decisions_with_equations'],
        }

    except Exception as e:
        elapsed = time.time() - start
        return {
            'meeting': meeting_id,
            'status': 'error',
            'elapsed': round(elapsed, 1),
            'error': str(e),
        }


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 대상 파일 수집
    docx_files = sorted(DOCX_DIR.glob("Final_Report_RAN1-*.docx"))
    print(f"{'=' * 80}")
    print(f"HybridReportParser vs Phase-3 전체 비교 검증")
    print(f"{'=' * 80}")
    print(f"대상: {len(docx_files)}개 미팅")
    print(f"DOCX: {DOCX_DIR}")
    print(f"Phase-3 JSON: {PHASE3_DIR}")
    print()

    results = []
    total_start = time.time()

    for i, docx_path in enumerate(docx_files):
        meeting = docx_path.stem.replace('Final_Report_RAN1-', '')
        phase3_path = PHASE3_DIR / f"RAN1_{meeting}.json"

        if not phase3_path.exists():
            print(f"[{i+1}/{len(docx_files)}] RAN1-{meeting}: Phase-3 JSON 없음, 건너뜀")
            continue

        print(f"\n[{i+1}/{len(docx_files)}] RAN1-{meeting}...")
        result = run_single_meeting(docx_path, phase3_path)
        results.append(result)

        if result['status'] == 'success':
            match_str = f"{result['content_exact_match']}/{result['common']}"
            eq_str = f"{result['valid']}/{result['total_equations']}" if result['total_equations'] > 0 else "0/0"
            mismatch_note = ""
            if result['content_mismatch'] > 0:
                mismatch_note = f" ⚠️ MISMATCH={result['content_mismatch']}"
            if result['phase3_only']:
                mismatch_note += f" P3only={len(result['phase3_only'])}"
            if result['hybrid_only']:
                mismatch_note += f" Honly={len(result['hybrid_only'])}"
            print(f"  → {result['elapsed']}s | text={match_str} | eq={eq_str}{mismatch_note}")
        else:
            print(f"  → ERROR: {result.get('error', 'unknown')}")

    total_elapsed = time.time() - total_start

    # 종합 결과
    success = [r for r in results if r['status'] == 'success']
    errors = [r for r in results if r['status'] == 'error']

    print()
    print("=" * 80)
    print(f"종합 결과: {len(success)}/{len(results)} 성공, {len(errors)} 실패")
    print(f"총 소요 시간: {total_elapsed:.1f}s ({total_elapsed/len(results):.1f}s/meeting avg)")
    print("=" * 80)

    # Phase-3 텍스트 호환성
    total_common = sum(r['common'] for r in success)
    total_exact = sum(r['content_exact_match'] for r in success)
    total_mismatch = sum(r['content_mismatch'] for r in success)
    total_p3only = sum(len(r['phase3_only']) for r in success)
    total_honly = sum(len(r['hybrid_only']) for r in success)

    print()
    print("■ Phase-3 텍스트 호환성")
    print(f"  총 Decision 비교:    {total_common}")
    print(f"  Content 완전 일치:   {total_exact}/{total_common} ({total_exact/total_common*100:.2f}%)" if total_common > 0 else "  N/A")
    print(f"  Content 불일치:      {total_mismatch}")
    print(f"  Phase-3에만 존재:    {total_p3only}")
    print(f"  Hybrid에만 존재:     {total_honly}")

    # 수식 통계
    total_eq = sum(r['total_equations'] for r in success)
    total_valid = sum(r['valid'] for r in success)
    total_invalid = sum(r['invalid'] for r in success)
    total_offset_ok = sum(r['offset_exact'] for r in success)
    total_offset_fail = sum(r['offset_failed'] for r in success)
    total_dec_eq = sum(r['decisions_with_equations'] for r in success)

    print()
    print("■ 수식 추출 품질")
    if total_eq > 0:
        print(f"  총 수식:             {total_eq}")
        print(f"  Valid:               {total_valid}/{total_eq} ({total_valid/total_eq*100:.2f}%)")
        print(f"  Invalid:             {total_invalid}")
        print(f"  Offset 정합:         {total_offset_ok}/{total_eq} ({total_offset_ok/total_eq*100:.2f}%)")
        print(f"  Offset 실패:         {total_offset_fail}")
        print(f"  수식 포함 Decision:  {total_dec_eq}")
    else:
        print("  수식 없음")

    # 불일치 상세
    mismatch_meetings = [r for r in success if r['content_mismatch'] > 0 or r['phase3_only'] or r['hybrid_only']]
    if mismatch_meetings:
        print()
        print("■ 불일치 상세")
        for r in mismatch_meetings:
            print(f"  {r['meeting']}:")
            if r['content_mismatch'] > 0:
                print(f"    Content 불일치: {r['content_mismatch']}개")
                for m in r['mismatches'][:3]:
                    print(f"      {m['decision_id']}: diff@{m['diff_position']} "
                          f"(p3:{m['phase3_len']} vs hy:{m['hybrid_len']})")
            if r['phase3_only']:
                print(f"    Phase-3에만: {r['phase3_only'][:5]}")
            if r['hybrid_only']:
                print(f"    Hybrid에만: {r['hybrid_only'][:5]}")

    # 에러 상세
    if errors:
        print()
        print("■ 에러 상세")
        for r in errors:
            print(f"  {r['meeting']}: {r.get('error', 'unknown')}")

    # 결과 저장
    summary = {
        'test_date': datetime.now().isoformat(),
        'description': 'HybridReportParser vs Phase-3 전체 비교 검증',
        'meetings_tested': len(success),
        'meetings_failed': len(errors),
        'total_elapsed': round(total_elapsed, 1),
        'phase3_compatibility': {
            'total_decisions_compared': total_common,
            'content_exact_match': total_exact,
            'content_mismatch': total_mismatch,
            'match_rate': round(total_exact / total_common * 100, 4) if total_common > 0 else 0,
            'phase3_only_count': total_p3only,
            'hybrid_only_count': total_honly,
        },
        'equation_quality': {
            'total_equations': total_eq,
            'valid': total_valid,
            'invalid': total_invalid,
            'valid_rate': round(total_valid / total_eq * 100, 4) if total_eq > 0 else 0,
            'offset_exact': total_offset_ok,
            'offset_failed': total_offset_fail,
            'offset_accuracy': round(total_offset_ok / total_eq * 100, 4) if total_eq > 0 else 0,
            'decisions_with_equations': total_dec_eq,
        },
        'per_meeting': results,
    }

    output_file = OUTPUT_DIR / "hybrid_vs_phase3_full_validation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
