#!/usr/bin/env python3
"""
실전적인 CQ 테스트 스크립트

기존 validate_cq.py는 전체 통계용 참고 CQ.
이 스크립트는 실제 사용 시나리오 기반의 테스트 CQ.

테스트 케이스 분류:
1. 단일 회의 (Single Meeting)
2. 복수 회의 (Multiple Meetings)
3. 기간 기반 (Date Range)
4. 최근 N개 회의 (Recent N Meetings)
5. 특정 회사/WI 추적 (Entity Tracking)
6. 관계 체인 (Relationship Chain)
"""

import time
from neo4j import GraphDatabase
from typing import Dict, List, Any

URI = "bolt://localhost:7688"
AUTH = ("neo4j", "password123")


# =============================================================================
# 테스트 CQ 정의
# =============================================================================

TEST_CQS = {
    # =========================================================================
    # 1. 단일 회의 (Single Meeting)
    # =========================================================================
    "T1.1": {
        "category": "Single Meeting",
        "desc": "RAN1#99에서 Samsung이 제출한 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumber: "RAN1#99"})
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            WHERE c.companyName CONTAINS "Samsung"
            RETURN t.tdocNumber, t.title, t.status
            ORDER BY t.tdocNumber
            LIMIT 10
        """,
        "expect": "rows > 0"
    },
    "T1.2": {
        "category": "Single Meeting",
        "desc": "RAN1#99에서 approved된 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumber: "RAN1#99"})
            WHERE t.status = 'approved'
            RETURN t.tdocNumber, t.title
            ORDER BY t.tdocNumber
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },
    "T1.3": {
        "category": "Single Meeting",
        "desc": "RAN1#99에서 회사별 제출 수 Top 5",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumber: "RAN1#99"})
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            RETURN c.companyName, count(t) as cnt
            ORDER BY cnt DESC
            LIMIT 5
        """,
        "expect": "rows > 0"
    },
    "T1.4": {
        "category": "Single Meeting",
        "desc": "RAN1#99에 들어온 LS (LS in) 목록",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumber: "RAN1#99"})
            WHERE t.type = 'LS in'
            RETURN t.tdocNumber, t.title
            ORDER BY t.tdocNumber
        """,
        "expect": "rows >= 0"
    },

    # =========================================================================
    # 2. 복수 회의 (Multiple Meetings)
    # =========================================================================
    "T2.1": {
        "category": "Multiple Meetings",
        "desc": "RAN1#97, #98, #99에서 Huawei가 제출한 Tdoc 수",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            WHERE m.meetingNumber IN ["RAN1#97", "RAN1#98", "RAN1#99"]
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            WHERE c.companyName CONTAINS "Huawei"
            RETURN m.meetingNumber, count(t) as cnt
            ORDER BY m.meetingNumber
        """,
        "expect": "rows > 0"
    },
    "T2.2": {
        "category": "Multiple Meetings",
        "desc": "RAN1#98, #98b, #99에서 approved된 Tdoc 비율",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            WHERE m.meetingNumber IN ["RAN1#98", "RAN1#98b", "RAN1#99"]
            WITH m.meetingNumber as meeting, count(t) as total,
                 sum(CASE WHEN t.status = 'approved' THEN 1 ELSE 0 END) as approved
            RETURN meeting, total, approved,
                   round(100.0 * approved / total, 1) as approval_rate
            ORDER BY meeting
        """,
        "expect": "rows > 0"
    },
    "T2.3": {
        "category": "Multiple Meetings",
        "desc": "RAN1#95~#99에서 LS out 발송 대상 WG 분포",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            WHERE m.meetingNumber IN ["RAN1#95", "RAN1#96", "RAN1#97", "RAN1#98", "RAN1#99"]
            AND t.type = 'LS out'
            MATCH (t)-[:SENT_TO]->(wg:WorkingGroup)
            RETURN wg.wgName, count(t) as cnt
            ORDER BY cnt DESC
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },

    # =========================================================================
    # 3. 최근 N개 회의 (Recent N Meetings)
    # =========================================================================
    "T3.1": {
        "category": "Recent N Meetings",
        "desc": "최근 5개 회의에서 가장 활발한 회사 Top 10",
        "query": """
            MATCH (m:Meeting)
            WITH m ORDER BY m.meetingNumber DESC LIMIT 5
            WITH collect(m) as recentMeetings
            UNWIND recentMeetings as m
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            RETURN c.companyName, count(t) as cnt
            ORDER BY cnt DESC
            LIMIT 10
        """,
        "expect": "rows > 0"
    },
    "T3.2": {
        "category": "Recent N Meetings",
        "desc": "최근 3개 회의에서 가장 많이 논의된 Work Item",
        "query": """
            MATCH (m:Meeting)
            WITH m ORDER BY m.meetingNumber DESC LIMIT 3
            WITH collect(m) as recentMeetings
            UNWIND recentMeetings as m
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m)
            MATCH (t)-[:RELATED_TO]->(w:WorkItem)
            RETURN w.workItemCode, count(t) as cnt
            ORDER BY cnt DESC
            LIMIT 10
        """,
        "expect": "rows > 0"
    },
    "T3.3": {
        "category": "Recent N Meetings",
        "desc": "최근 10개 회의의 회의별 Tdoc 수",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            WITH m, count(t) as tdocCount
            ORDER BY m.meetingNumber DESC
            LIMIT 10
            RETURN m.meetingNumber, tdocCount
            ORDER BY m.meetingNumber
        """,
        "expect": "rows > 0"
    },

    # =========================================================================
    # 4. 특정 회사/WI 추적 (Entity Tracking)
    # =========================================================================
    "T4.1": {
        "category": "Entity Tracking",
        "desc": "Qualcomm이 제출한 CR 중 Rel-18 대상 목록",
        "query": """
            MATCH (t:CR)-[:SUBMITTED_BY]->(c:Company)
            WHERE c.companyName CONTAINS "Qualcomm"
            MATCH (t)-[:TARGET_RELEASE]->(r:Release)
            WHERE r.releaseName CONTAINS "Rel-18"
            RETURN t.tdocNumber, t.title, t.status
            ORDER BY t.tdocNumber
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },
    "T4.2": {
        "category": "Entity Tracking",
        "desc": "NR_NTN_enh Work Item 관련 전체 Tdoc 이력",
        "query": """
            MATCH (t:Tdoc)-[:RELATED_TO]->(w:WorkItem)
            WHERE w.workItemCode CONTAINS "NTN"
            MATCH (t)-[:PRESENTED_AT]->(m:Meeting)
            RETURN m.meetingNumber, count(t) as cnt
            ORDER BY m.meetingNumber
        """,
        "expect": "rows >= 0"
    },
    "T4.3": {
        "category": "Entity Tracking",
        "desc": "Nokia와 Ericsson이 같은 Agenda에서 경쟁한 횟수",
        "query": """
            MATCH (t1:Tdoc)-[:SUBMITTED_BY]->(c1:Company)
            WHERE c1.companyName CONTAINS "Nokia"
            MATCH (t1)-[:BELONGS_TO]->(a:AgendaItem)
            MATCH (t2:Tdoc)-[:BELONGS_TO]->(a)
            MATCH (t2)-[:SUBMITTED_BY]->(c2:Company)
            WHERE c2.companyName CONTAINS "Ericsson"
            AND t1 <> t2
            RETURN a.agendaItemNumber, count(DISTINCT t1) as nokia_cnt,
                   count(DISTINCT t2) as ericsson_cnt
            ORDER BY nokia_cnt + ericsson_cnt DESC
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },
    "T4.4": {
        "category": "Entity Tracking",
        "desc": "RAN2에서 온 LS 목록과 관련 Agenda",
        "query": """
            MATCH (t:Tdoc)-[:ORIGINATED_FROM]->(wg:WorkingGroup {wgName: "RAN2"})
            MATCH (t)-[:BELONGS_TO]->(a:AgendaItem)
            RETURN t.tdocNumber, t.title, a.agendaItemNumber
            ORDER BY t.tdocNumber
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },

    # =========================================================================
    # 5. 관계 체인 (Relationship Chain)
    # =========================================================================
    "T5.1": {
        "category": "Relationship Chain",
        "desc": "R1-2400001의 전체 revision 체인",
        "query": """
            MATCH (t:Tdoc {tdocNumber: "R1-2400001"})
            OPTIONAL MATCH path = (t)-[:IS_REVISION_OF*1..5]->(prev:Tdoc)
            RETURN t.tdocNumber as original,
                   [n IN nodes(path) | n.tdocNumber] as revision_chain
        """,
        "expect": "rows >= 0"
    },
    "T5.2": {
        "category": "Relationship Chain",
        "desc": "revision이 3번 이상 된 Tdoc 목록",
        "query": """
            MATCH path = (t:Tdoc)-[:REVISED_TO*3..]->(final:Tdoc)
            RETURN t.tdocNumber as original,
                   length(path) as revision_count,
                   final.tdocNumber as final_version,
                   final.status as final_status
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },
    "T5.3": {
        "category": "Relationship Chain",
        "desc": "LS Reply 체인: 원본 LS → Reply → Reply",
        "query": """
            MATCH (reply:Tdoc)-[:REPLY_TO]->(original:Tdoc)
            RETURN original.tdocNumber as original_ls,
                   reply.tdocNumber as reply_ls,
                   original.title as original_title
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },
    "T5.4": {
        "category": "Relationship Chain",
        "desc": "특정 Spec (38.211)을 수정하는 CR과 그 결과",
        "query": """
            MATCH (t:CR)-[:MODIFIES]->(s:Spec)
            WHERE s.specNumber CONTAINS "38.211"
            RETURN t.tdocNumber, t.title, t.status, s.specNumber
            ORDER BY t.tdocNumber DESC
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },

    # =========================================================================
    # 6. 복합 분석 (Complex Analysis)
    # =========================================================================
    "T6.1": {
        "category": "Complex Analysis",
        "desc": "회사별 채택률 비교 (최근 5개 회의 기준)",
        "query": """
            MATCH (m:Meeting)
            WITH m ORDER BY m.meetingNumber DESC LIMIT 5
            WITH collect(m) as recentMeetings
            UNWIND recentMeetings as m
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            WITH c.companyName as company,
                 count(t) as total,
                 sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) as accepted
            WHERE total >= 20
            RETURN company, total, accepted,
                   round(100.0 * accepted / total, 1) as rate
            ORDER BY rate DESC
            LIMIT 10
        """,
        "expect": "rows > 0"
    },
    "T6.2": {
        "category": "Complex Analysis",
        "desc": "Agenda별 경쟁 강도 (참여 회사 수, Tdoc 수)",
        "query": """
            MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            MATCH (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumber: "RAN1#99"})
            WITH a, count(DISTINCT c) as company_count, count(t) as tdoc_count
            WHERE company_count >= 3
            RETURN a.agendaItemNumber, company_count, tdoc_count
            ORDER BY tdoc_count DESC
            LIMIT 10
        """,
        "expect": "rows >= 0"
    },
    "T6.3": {
        "category": "Complex Analysis",
        "desc": "Release별 CR 현황 (approved/rejected/pending)",
        "query": """
            MATCH (t:CR)-[:TARGET_RELEASE]->(r:Release)
            RETURN r.releaseName,
                   count(t) as total,
                   sum(CASE WHEN t.status = 'approved' THEN 1 ELSE 0 END) as approved,
                   sum(CASE WHEN t.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                   sum(CASE WHEN t.status = 'revised' THEN 1 ELSE 0 END) as revised
            ORDER BY r.releaseName
        """,
        "expect": "rows > 0"
    },
}


def run_test_cq(driver, cq_id: str, cq: Dict) -> Dict[str, Any]:
    """단일 테스트 CQ 실행"""
    start = time.time()

    try:
        with driver.session() as session:
            result = session.run(cq['query'])
            records = list(result)

        elapsed = time.time() - start

        # 결과 포맷팅
        if records:
            # 첫 몇 개 레코드 샘플 추출
            sample = []
            for r in records[:3]:
                sample.append(dict(r))

            return {
                "status": "✅",
                "rows": len(records),
                "time_ms": elapsed * 1000,
                "sample": sample
            }
        else:
            return {
                "status": "⚠️",
                "rows": 0,
                "time_ms": elapsed * 1000,
                "sample": []
            }

    except Exception as e:
        return {
            "status": "❌",
            "rows": 0,
            "time_ms": 0,
            "error": str(e)
        }


def main():
    print("=" * 70)
    print("실전적인 CQ 테스트")
    print("=" * 70)

    driver = GraphDatabase.driver(URI, auth=AUTH)

    try:
        results_by_category = {}

        for cq_id in sorted(TEST_CQS.keys()):
            cq = TEST_CQS[cq_id]
            category = cq['category']

            if category not in results_by_category:
                results_by_category[category] = []
                print(f"\n{'─' * 70}")
                print(f"📂 {category}")
                print(f"{'─' * 70}")

            print(f"\n[{cq_id}] {cq['desc']}")

            result = run_test_cq(driver, cq_id, cq)
            results_by_category[category].append({
                "id": cq_id,
                "desc": cq['desc'],
                **result
            })

            # 결과 출력
            print(f"  Status: {result['status']} | Rows: {result['rows']} | Time: {result['time_ms']:.1f}ms")

            if result.get('sample'):
                print(f"  Sample:")
                for s in result['sample']:
                    # 샘플 데이터 간략 출력
                    preview = str(s)[:100] + "..." if len(str(s)) > 100 else str(s)
                    print(f"    {preview}")

            if result.get('error'):
                print(f"  Error: {result['error']}")

        # 요약
        print("\n" + "=" * 70)
        print("Summary by Category")
        print("=" * 70)

        total_passed = 0
        total_warning = 0
        total_failed = 0

        for category, results in results_by_category.items():
            passed = sum(1 for r in results if r['status'] == '✅')
            warning = sum(1 for r in results if r['status'] == '⚠️')
            failed = sum(1 for r in results if r['status'] == '❌')

            print(f"\n{category}:")
            print(f"  ✅ Passed: {passed}, ⚠️ Warning: {warning}, ❌ Failed: {failed}")

            total_passed += passed
            total_warning += warning
            total_failed += failed

        print("\n" + "─" * 70)
        print(f"Total: ✅ {total_passed} | ⚠️ {total_warning} | ❌ {total_failed}")
        print("=" * 70)

        return results_by_category

    finally:
        driver.close()


if __name__ == "__main__":
    main()
