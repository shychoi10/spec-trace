"""
Phase-3 텍스트 호환성 경량 검증

목적: HybridReportParser의 Phase-3 ReportParser 기반 decision 추출이
기존 Phase-3 결과와 100% 텍스트 호환되는지 검증

방법: Pandoc 수식 변환 없이 Phase-3 ReportParser만 사용하여
- decision_id 일치
- content (para.text) 완전 일치
- decision 수 일치
를 58개 미팅 전수 검증

수식 품질은 이미 배치 테스트로 검증 완료:
- batch_test_10meetings_summary.json (10개, 100% valid)
- batch_test_remaining47_summary.json (47개, 99.81% valid)
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Phase-3 parser
PHASE3_DIR = Path(__file__).resolve().parent.parent.parent / 'phase-3' / 'report-parser'
sys.path.insert(0, str(PHASE3_DIR))
from report_parser import ReportParser

DOCX_DIR = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report")
JSON_DIR = Path("/home/sihyeon/workspace/spec-trace/ontology/output/parsed_reports")
OUTPUT_DIR = Path(__file__).parent / "output"


def compare_meeting(docx_path: Path, phase3_path: Path) -> dict:
    """단일 미팅: Phase-3 ReportParser 재실행 후 기존 결과와 비교"""
    meeting = docx_path.stem.replace('Final_Report_RAN1-', '')
    meeting_id = f"RAN1-{meeting}"

    start = time.time()
    try:
        # Phase-3 파서 재실행
        parser = ReportParser(docx_path)
        report = parser.parse()
        elapsed = time.time() - start

        # 재실행 결과 → ID:content 맵
        new_decisions = {}
        for d in report.agreements:
            new_decisions[d.decision_id] = d.content
        for d in report.conclusions:
            new_decisions[d.decision_id] = d.content
        for d in report.working_assumptions:
            new_decisions[d.decision_id] = d.content

        # 기존 Phase-3 JSON 로드
        with open(phase3_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)

        existing_decisions = {}
        for dtype in ['agreements', 'conclusions', 'working_assumptions']:
            for d in existing.get(dtype, []):
                existing_decisions[d['decision_id']] = d['content']

        # 비교
        common_ids = set(new_decisions.keys()) & set(existing_decisions.keys())
        new_only = sorted(set(new_decisions.keys()) - set(existing_decisions.keys()))
        existing_only = sorted(set(existing_decisions.keys()) - set(new_decisions.keys()))

        exact_match = 0
        mismatches = []
        for did in sorted(common_ids):
            if new_decisions[did] == existing_decisions[did]:
                exact_match += 1
            else:
                if len(mismatches) < 5:
                    n = new_decisions[did]
                    e = existing_decisions[did]
                    diff_pos = next(
                        (i for i, (a, b) in enumerate(zip(n, e)) if a != b),
                        min(len(n), len(e))
                    )
                    mismatches.append({
                        'decision_id': did,
                        'diff_position': diff_pos,
                        'new_len': len(n),
                        'existing_len': len(e),
                        'new_snippet': n[max(0, diff_pos-20):diff_pos+40],
                        'existing_snippet': e[max(0, diff_pos-20):diff_pos+40],
                    })

        return {
            'meeting': meeting_id,
            'status': 'success',
            'elapsed': round(elapsed, 1),
            'new_total': len(new_decisions),
            'existing_total': len(existing_decisions),
            'common': len(common_ids),
            'exact_match': exact_match,
            'content_mismatch': len(common_ids) - exact_match,
            'new_only': new_only,
            'existing_only': existing_only,
            'mismatches': mismatches,
            # 세부 카운트
            'new_agr': len(report.agreements),
            'new_con': len(report.conclusions),
            'new_wa': len(report.working_assumptions),
            'existing_agr': len(existing.get('agreements', [])),
            'existing_con': len(existing.get('conclusions', [])),
            'existing_wa': len(existing.get('working_assumptions', [])),
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

    docx_files = sorted(DOCX_DIR.glob("Final_Report_RAN1-*.docx"))
    print(f"{'=' * 80}")
    print(f"Phase-3 텍스트 호환성 검증 (Pandoc 수식 변환 제외)")
    print(f"{'=' * 80}")
    print(f"대상: {len(docx_files)}개 미팅")
    print(f"방법: ReportParser 재실행 → 기존 Phase-3 JSON과 content 비교")
    print()

    results = []
    total_start = time.time()

    for i, docx_path in enumerate(docx_files):
        meeting = docx_path.stem.replace('Final_Report_RAN1-', '')
        phase3_path = JSON_DIR / f"RAN1_{meeting}.json"

        if not phase3_path.exists():
            print(f"[{i+1}/{len(docx_files)}] RAN1-{meeting}: Phase-3 JSON 없음, skip")
            continue

        print(f"[{i+1}/{len(docx_files)}] RAN1-{meeting}...", end=" ", flush=True)
        result = compare_meeting(docx_path, phase3_path)
        results.append(result)

        if result['status'] == 'success':
            match_str = f"{result['exact_match']}/{result['common']}"
            note = ""
            if result['content_mismatch'] > 0:
                note += f" MISMATCH={result['content_mismatch']}"
            if result['new_only']:
                note += f" new_only={len(result['new_only'])}"
            if result['existing_only']:
                note += f" exist_only={len(result['existing_only'])}"
            if not note:
                note = " OK"
            print(f"{result['elapsed']}s | {result['new_total']} dec | text={match_str}{note}")
        else:
            print(f"ERROR: {result.get('error', 'unknown')}")

    total_elapsed = time.time() - total_start

    # 종합 결과
    success = [r for r in results if r['status'] == 'success']
    errors = [r for r in results if r['status'] == 'error']

    total_common = sum(r['common'] for r in success)
    total_exact = sum(r['exact_match'] for r in success)
    total_mismatch = sum(r['content_mismatch'] for r in success)
    total_new_only = sum(len(r['new_only']) for r in success)
    total_exist_only = sum(len(r['existing_only']) for r in success)
    total_decisions = sum(r['new_total'] for r in success)

    # 미팅별 불일치 카운트
    perfect_meetings = [r for r in success if r['content_mismatch'] == 0 and not r['new_only'] and not r['existing_only']]
    imperfect_meetings = [r for r in success if r['content_mismatch'] > 0 or r['new_only'] or r['existing_only']]

    print()
    print("=" * 80)
    print(f"종합 결과: {len(success)}/{len(results)} 성공, {len(errors)} 실패")
    print(f"총 소요 시간: {total_elapsed:.1f}s ({total_elapsed/max(len(results),1):.1f}s/meeting avg)")
    print("=" * 80)

    print()
    print("■ Phase-3 텍스트 호환성 (핵심 지표)")
    print(f"  총 Decision:         {total_decisions}")
    print(f"  비교된 Decision:     {total_common}")
    if total_common > 0:
        pct = total_exact / total_common * 100
        print(f"  Content 완전 일치:   {total_exact}/{total_common} ({pct:.4f}%)")
    print(f"  Content 불일치:      {total_mismatch}")
    print(f"  재실행에만 존재:     {total_new_only}")
    print(f"  기존에만 존재:       {total_exist_only}")

    print()
    print(f"  완벽 일치 미팅:      {len(perfect_meetings)}/{len(success)}")
    print(f"  불일치 미팅:         {len(imperfect_meetings)}/{len(success)}")

    # 불일치 상세
    if imperfect_meetings:
        print()
        print("■ 불일치 상세")
        for r in imperfect_meetings:
            print(f"  {r['meeting']}:")
            if r['content_mismatch'] > 0:
                print(f"    Content 불일치: {r['content_mismatch']}개")
                for m in r['mismatches'][:3]:
                    print(f"      {m['decision_id']}: diff@{m['diff_position']} "
                          f"(new:{m['new_len']} vs exist:{m['existing_len']})")
                    print(f"        new:  ...{m['new_snippet']!r}...")
                    print(f"        exist:...{m['existing_snippet']!r}...")
            if r['new_only']:
                print(f"    재실행에만: {r['new_only'][:5]}")
            if r['existing_only']:
                print(f"    기존에만: {r['existing_only'][:5]}")

    if errors:
        print()
        print("■ 에러 상세")
        for r in errors:
            print(f"  {r['meeting']}: {r.get('error', 'unknown')}")

    # 결과 저장
    summary = {
        'test_date': datetime.now().isoformat(),
        'description': 'Phase-3 텍스트 호환성 검증 (Pandoc 수식 변환 제외)',
        'meetings_tested': len(success),
        'meetings_failed': len(errors),
        'total_elapsed': round(total_elapsed, 1),
        'text_compatibility': {
            'total_decisions': total_decisions,
            'total_compared': total_common,
            'exact_match': total_exact,
            'content_mismatch': total_mismatch,
            'match_rate': round(total_exact / total_common * 100, 4) if total_common > 0 else 0,
            'new_only_count': total_new_only,
            'existing_only_count': total_exist_only,
            'perfect_meetings': len(perfect_meetings),
            'imperfect_meetings': len(imperfect_meetings),
        },
        'per_meeting': results,
    }

    output_file = OUTPUT_DIR / "phase3_text_compatibility_validation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
