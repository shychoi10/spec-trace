"""
10개 미팅 확장 검증 테스트

V2.1 수식 추출 로직을 10개 랜덤 미팅에 적용하여 검증.
검증 항목:
1. 수식 추출 성공률 (valid/total)
2. offset 정합성 (content_raw[offset:len] == plain_text)
3. position 연속성
4. offset 단조증가
"""

import json
import random
import time
from pathlib import Path

# V2.1 파서 import
import sys
sys.path.insert(0, str(Path(__file__).parent))
from full_parse_test_v2 import ExperimentalReportParserV2


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
    }

    for d in result['decisions']:
        eqs = d.get('equations', [])
        if eqs:
            stats['decisions_with_eq'] += 1

        raw = d.get('content_raw', '')

        for i, eq in enumerate(eqs):
            stats['total_equations'] += 1

            # Valid 검증
            if eq.get('is_valid', False):
                stats['valid'] += 1
            else:
                stats['invalid'] += 1

            # offset 정합성: content_raw[offset:offset+len] == plain_text
            off = eq['char_offset']
            length = eq['char_length']
            segment = raw[off:off + length]
            if segment == eq['plain_text']:
                stats['offset_exact'] += 1
            else:
                stats['offset_mismatch'] += 1
                if len(stats['mismatches']) < 5:
                    stats['mismatches'].append({
                        'decision': d['decision_id'],
                        'eq_pos': eq['position'],
                        'expected': eq['plain_text'][:40],
                        'actual': segment[:40],
                    })

            # position 연속성
            if eq['position'] == i:
                stats['position_ok'] += 1
            else:
                stats['position_fail'] += 1

        # offset 단조증가
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

    # 10개 랜덤 선택 (112는 이미 테스트됨 → 제외하고 선택)
    random.seed(42)  # 재현성
    candidates = [r for r in all_reports if '112' not in r.stem]
    selected = random.sample(candidates, 10)
    selected.sort(key=lambda x: x.stem)

    print(f"선택된 미팅: {[r.stem.replace('Final_Report_RAN1-', '') for r in selected]}")
    print()

    # 배치 실행
    all_results = []
    total_start = time.time()

    for i, report_path in enumerate(selected):
        meeting = report_path.stem.replace('Final_Report_', '')
        print(f"[{i + 1}/10] {meeting}...", end=" ", flush=True)

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
            }
            all_results.append(summary)

            eq_rate = f"{verification['valid']}/{verification['total_equations']}" if verification['total_equations'] > 0 else "0/0"
            off_rate = f"{verification['offset_exact']}/{verification['total_equations']}" if verification['total_equations'] > 0 else "0/0"
            print(f"{elapsed:.1f}s | {len(result['decisions'])} decisions | {eq_rate} valid | {off_rate} offset OK")

            # 결과 저장
            output_file = output_dir / f"parsed_{meeting.replace('-', '_').replace('RAN1_', 'RAN1_')}_with_equations_v2.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"ERROR: {e}")
            all_results.append({
                'meeting': meeting,
                'error': str(e),
            })

    total_elapsed = time.time() - total_start

    # 종합 결과
    print()
    print("=" * 80)
    print("종합 결과")
    print("=" * 80)

    total_eq = sum(r.get('total_equations', 0) for r in all_results if 'error' not in r)
    total_valid = sum(r.get('valid', 0) for r in all_results if 'error' not in r)
    total_invalid = sum(r.get('invalid', 0) for r in all_results if 'error' not in r)
    total_offset_ok = sum(r.get('offset_exact', 0) for r in all_results if 'error' not in r)
    total_offset_fail = sum(r.get('offset_mismatch', 0) for r in all_results if 'error' not in r)
    total_pos_ok = sum(r.get('position_ok', 0) for r in all_results if 'error' not in r)
    total_pos_fail = sum(r.get('position_fail', 0) for r in all_results if 'error' not in r)
    total_mono_ok = sum(r.get('monotonic_ok', 0) for r in all_results if 'error' not in r)
    total_mono_fail = sum(r.get('monotonic_fail', 0) for r in all_results if 'error' not in r)
    total_decisions = sum(r.get('decisions', 0) for r in all_results if 'error' not in r)
    success_count = sum(1 for r in all_results if 'error' not in r)
    error_count = sum(1 for r in all_results if 'error' in r)

    print(f"처리 미팅: {success_count}/10 성공, {error_count} 실패")
    print(f"총 소요시간: {total_elapsed:.1f}s")
    print(f"총 Decision: {total_decisions}개")
    print(f"총 수식: {total_eq}개")
    print()

    if total_eq > 0:
        print(f"| 검증 항목 | 결과 |")
        print(f"|-----------|------|")
        print(f"| Valid | {total_valid}/{total_eq} ({total_valid / total_eq * 100:.1f}%) |")
        print(f"| Invalid | {total_invalid}/{total_eq} ({total_invalid / total_eq * 100:.1f}%) |")
        print(f"| offset 정합 | {total_offset_ok}/{total_eq} ({total_offset_ok / total_eq * 100:.1f}%) |")
        print(f"| position 연속 | {total_pos_ok}/{total_eq} ({total_pos_ok / total_eq * 100:.1f}%) |")
        mono_total = total_mono_ok + total_mono_fail
        if mono_total > 0:
            print(f"| offset 단조증가 | {total_mono_ok}/{mono_total} ({total_mono_ok / mono_total * 100:.1f}%) |")
    else:
        print("수식 없음")

    # 미팅별 상세
    print()
    print("=" * 80)
    print("미팅별 상세")
    print("=" * 80)
    print(f"| 미팅 | 시간 | Decision | 수식 | Valid | offset OK |")
    print(f"|------|------|----------|------|-------|-----------|")
    for r in all_results:
        if 'error' in r:
            print(f"| {r['meeting']} | ERROR | - | - | - | - |")
        else:
            eq = r['total_equations']
            v = r['valid']
            o = r['offset_exact']
            v_pct = f"{v / eq * 100:.0f}%" if eq > 0 else "-"
            o_pct = f"{o / eq * 100:.0f}%" if eq > 0 else "-"
            print(f"| {r['meeting']} | {r['elapsed']}s | {r['decisions']} | {eq} | {v} ({v_pct}) | {o} ({o_pct}) |")

    # offset 불일치 상세
    all_mismatches = []
    for r in all_results:
        all_mismatches.extend(r.get('mismatches', []))
    if all_mismatches:
        print()
        print("=== offset 불일치 상세 ===")
        for m in all_mismatches[:10]:
            print(f"  {m['decision']} eq[{m['eq_pos']}]: expected={m['expected']}, actual={m['actual']}")

    # 종합 결과 저장
    summary_output = output_dir / "batch_test_10meetings_summary.json"
    with open(summary_output, 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'meetings_tested': success_count,
            'total_elapsed': round(total_elapsed, 1),
            'total_decisions': total_decisions,
            'total_equations': total_eq,
            'valid_rate': round(total_valid / total_eq * 100, 1) if total_eq > 0 else 0,
            'offset_accuracy': round(total_offset_ok / total_eq * 100, 1) if total_eq > 0 else 0,
            'per_meeting': all_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {summary_output}")


if __name__ == "__main__":
    main()
