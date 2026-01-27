"""
전체 58개 미팅 중 미검증 47개에 대한 전수 검증 테스트

이미 검증 완료:
- RAN1-112 (단일 검증)
- 10개 배치: 100b, 104b, 105, 106, 110, 110b, 113, 89, 94, 97

검증 항목:
1. 수식 추출 성공률 (valid/total)
2. offset 정합성 (content_raw[offset:len] == plain_text)
3. position 연속성
4. offset 단조증가
"""

import json
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from full_parse_test_v2 import ExperimentalReportParserV2

ALREADY_TESTED = {
    'RAN1-112', 'RAN1-100b', 'RAN1-104b', 'RAN1-105', 'RAN1-106',
    'RAN1-110', 'RAN1-110b', 'RAN1-113', 'RAN1-89', 'RAN1-94', 'RAN1-97',
}


def verify_equations(result: dict) -> dict:
    """수식 정합성 검증"""
    stats = {
        'total_equations': 0,
        'valid': 0,
        'invalid': 0,
        'offset_exact': 0,
        'offset_mismatch': 0,
        'position_ok': 0,
        'position_fail': 0,
        'monotonic_ok': 0,
        'monotonic_fail': 0,
        'decisions_with_eq': 0,
        'mismatches': [],
        'invalid_details': [],
    }

    for d in result['decisions']:
        eqs = d.get('equations', [])
        if eqs:
            stats['decisions_with_eq'] += 1

        raw = d.get('content_raw', '')

        for i, eq in enumerate(eqs):
            stats['total_equations'] += 1

            if eq.get('is_valid', False):
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                if len(stats['invalid_details']) < 20:
                    stats['invalid_details'].append({
                        'decision': d['decision_id'],
                        'eq_pos': eq['position'],
                        'plain_text': eq['plain_text'][:60],
                        'latex': eq.get('latex', '')[:80],
                        'note': eq.get('validation_note', ''),
                    })

            off = eq['char_offset']
            length = eq['char_length']
            segment = raw[off:off + length]
            if segment == eq['plain_text']:
                stats['offset_exact'] += 1
            else:
                stats['offset_mismatch'] += 1
                if len(stats['mismatches']) < 10:
                    stats['mismatches'].append({
                        'decision': d['decision_id'],
                        'eq_pos': eq['position'],
                        'expected': eq['plain_text'][:40],
                        'actual': segment[:40],
                    })

            if eq['position'] == i:
                stats['position_ok'] += 1
            else:
                stats['position_fail'] += 1

        for i in range(1, len(eqs)):
            if eqs[i]['char_offset'] > eqs[i - 1]['char_offset']:
                stats['monotonic_ok'] += 1
            else:
                stats['monotonic_fail'] += 1

    return stats


def main():
    report_dir = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report")
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    all_reports = sorted(report_dir.glob("Final_Report_RAN1-*.docx"))
    print(f"전체 Final Report: {len(all_reports)}개")

    # 미검증 미팅만 선택
    remaining = []
    for r in all_reports:
        meeting_name = r.stem.replace('Final_Report_', '')
        if meeting_name not in ALREADY_TESTED:
            remaining.append(r)

    remaining.sort(key=lambda x: x.stem)
    print(f"미검증 미팅: {len(remaining)}개")
    print(f"이미 검증: {len(all_reports) - len(remaining)}개 ({', '.join(sorted(ALREADY_TESTED))})")
    print()

    # 배치 실행
    all_results = []
    total_start = time.time()
    errors = []

    for i, report_path in enumerate(remaining):
        meeting = report_path.stem.replace('Final_Report_', '')
        print(f"[{i + 1}/{len(remaining)}] {meeting}...", end=" ", flush=True)

        start = time.time()
        try:
            parser = ExperimentalReportParserV2(report_path)
            result = parser.parse()
            elapsed = time.time() - start

            verification = verify_equations(result)

            summary = {
                'meeting': meeting,
                'elapsed': round(elapsed, 1),
                'decisions': len(result['decisions']),
                'total_equations': verification['total_equations'],
                'valid': verification['valid'],
                'invalid': verification['invalid'],
                'offset_exact': verification['offset_exact'],
                'offset_mismatch': verification['offset_mismatch'],
                'position_ok': verification['position_ok'],
                'position_fail': verification['position_fail'],
                'monotonic_ok': verification['monotonic_ok'],
                'monotonic_fail': verification['monotonic_fail'],
                'mismatches': verification['mismatches'],
                'invalid_details': verification['invalid_details'],
            }
            all_results.append(summary)

            eq = verification['total_equations']
            v = verification['valid']
            o = verification['offset_exact']
            eq_str = f"{v}/{eq}" if eq > 0 else "0/0"
            off_str = f"{o}/{eq}" if eq > 0 else "0/0"
            print(f"{elapsed:.1f}s | {len(result['decisions'])} dec | {eq_str} valid | {off_str} offset")

        except Exception as e:
            elapsed = time.time() - start
            print(f"ERROR ({elapsed:.1f}s): {e}")
            errors.append({'meeting': meeting, 'error': str(e)})
            all_results.append({'meeting': meeting, 'error': str(e)})

    total_elapsed = time.time() - total_start

    # 종합 결과
    success_results = [r for r in all_results if 'error' not in r]
    print()
    print("=" * 80)
    print(f"종합 결과 ({len(success_results)}/{len(remaining)} 성공, {len(errors)} 실패)")
    print("=" * 80)

    total_eq = sum(r['total_equations'] for r in success_results)
    total_valid = sum(r['valid'] for r in success_results)
    total_invalid = sum(r['invalid'] for r in success_results)
    total_offset_ok = sum(r['offset_exact'] for r in success_results)
    total_pos_ok = sum(r['position_ok'] for r in success_results)
    total_pos_fail = sum(r['position_fail'] for r in success_results)
    total_mono_ok = sum(r['monotonic_ok'] for r in success_results)
    total_mono_fail = sum(r['monotonic_fail'] for r in success_results)
    total_decisions = sum(r['decisions'] for r in success_results)

    print(f"총 소요시간: {total_elapsed:.1f}s ({total_elapsed/len(remaining):.1f}s/meeting avg)")
    print(f"총 Decision: {total_decisions}개")
    print(f"총 수식: {total_eq}개")
    print()

    if total_eq > 0:
        print(f"| 검증 항목 | 결과 |")
        print(f"|-----------|------|")
        print(f"| Valid | {total_valid}/{total_eq} ({total_valid/total_eq*100:.1f}%) |")
        print(f"| Invalid | {total_invalid}/{total_eq} ({total_invalid/total_eq*100:.1f}%) |")
        print(f"| offset 정합 | {total_offset_ok}/{total_eq} ({total_offset_ok/total_eq*100:.1f}%) |")
        print(f"| position 연속 | {total_pos_ok}/{total_eq} ({total_pos_ok/total_eq*100:.1f}%) |")
        mono_total = total_mono_ok + total_mono_fail
        if mono_total > 0:
            print(f"| offset 단조증가 | {total_mono_ok}/{mono_total} ({total_mono_ok/mono_total*100:.1f}%) |")

    # 미팅별 상세
    print()
    print("미팅별 상세:")
    print(f"| 미팅 | 시간 | Decision | 수식 | Valid | offset |")
    print(f"|------|------|----------|------|-------|--------|")
    for r in all_results:
        if 'error' in r:
            print(f"| {r['meeting']} | ERROR | - | - | - | - |")
        else:
            eq = r['total_equations']
            v = r['valid']
            o = r['offset_exact']
            v_pct = f"{v/eq*100:.0f}%" if eq > 0 else "-"
            o_pct = f"{o/eq*100:.0f}%" if eq > 0 else "-"
            print(f"| {r['meeting']} | {r['elapsed']}s | {r['decisions']} | {eq} | {v} ({v_pct}) | {o} ({o_pct}) |")

    # Invalid 상세
    all_invalids = []
    for r in success_results:
        all_invalids.extend(r.get('invalid_details', []))
    if all_invalids:
        print()
        print(f"=== Invalid 수식 상세 ({len(all_invalids)}개) ===")
        for inv in all_invalids:
            print(f"  {inv['decision']} eq[{inv['eq_pos']}]: {inv['plain_text']}")
            print(f"    latex: {inv['latex']}")
            print(f"    note: {inv['note']}")

    # offset 불일치 상세
    all_mismatches = []
    for r in success_results:
        all_mismatches.extend(r.get('mismatches', []))
    if all_mismatches:
        print()
        print(f"=== offset 불일치 상세 ({len(all_mismatches)}개) ===")
        for m in all_mismatches[:20]:
            print(f"  {m['decision']} eq[{m['eq_pos']}]: expected='{m['expected']}', actual='{m['actual']}'")

    # 에러 상세
    if errors:
        print()
        print(f"=== 에러 상세 ({len(errors)}개) ===")
        for e in errors:
            print(f"  {e['meeting']}: {e['error']}")

    # 결과 저장
    summary_output = output_dir / "batch_test_remaining47_summary.json"
    with open(summary_output, 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': '미검증 47개 미팅 전수 검증',
            'meetings_tested': len(success_results),
            'meetings_failed': len(errors),
            'total_elapsed': round(total_elapsed, 1),
            'total_decisions': total_decisions,
            'total_equations': total_eq,
            'valid_rate': round(total_valid/total_eq*100, 2) if total_eq > 0 else 0,
            'offset_accuracy': round(total_offset_ok/total_eq*100, 2) if total_eq > 0 else 0,
            'position_accuracy': round(total_pos_ok/total_eq*100, 2) if total_eq > 0 else 0,
            'per_meeting': [{k: v for k, v in r.items() if k != 'invalid_details'} for r in all_results],
            'invalid_equations': all_invalids,
            'errors': errors,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {summary_output}")

    # 전체 58개 종합 (기존 11개 + 신규 47개)
    print()
    print("=" * 80)
    print("전체 58개 미팅 종합 (기존 11개 + 신규 47개)")
    print("=" * 80)
    prev_eq = 1100 + 248  # 10 batch + RAN1-112
    prev_valid = 1100 + 248
    grand_eq = prev_eq + total_eq
    grand_valid = prev_valid + total_valid
    grand_invalid = total_invalid  # 기존은 0
    print(f"총 수식: {grand_eq}개")
    print(f"Valid: {grand_valid}/{grand_eq} ({grand_valid/grand_eq*100:.2f}%)")
    if grand_invalid > 0:
        print(f"Invalid: {grand_invalid}개")


if __name__ == "__main__":
    main()
