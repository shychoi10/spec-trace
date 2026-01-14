#!/usr/bin/env python3
"""
Sub-step 2-4: CQ 25개 Cypher 쿼리 검증
각 CQ에 대해 쿼리 실행, 결과 확인, 성능 측정
"""

import time
from neo4j import GraphDatabase

URI = "bolt://localhost:7688"
AUTH = ("neo4j", "password123")

# CQ 쿼리 정의 (쿼리, 설명, 예상 결과 타입)
CQ_QUERIES = {
    # Tdoc 기본 검색 (9개)
    "CQ1": {
        "desc": "특정 회의에서 특정 Work Item 관련 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            MATCH (t)-[:RELATED_TO]->(w:WorkItem)
            RETURN count(t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ2": {
        "desc": "특정 회의에서 특정 Agenda Item 관련 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            MATCH (t)-[:BELONGS_TO]->(a:AgendaItem)
            RETURN count(DISTINCT t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ3": {
        "desc": "특정 회의에서 특정 회사가 제출한 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            RETURN count(DISTINCT t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ4": {
        "desc": "특정 Release에서 논의된 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release)
            RETURN count(t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ5": {
        "desc": "특정 회의에서 승인/합의된 Tdoc 목록",
        "query": """
            MATCH (t:Tdoc)
            WHERE t.status IN ['approved', 'agreed']
            RETURN count(t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ6": {
        "desc": "특정 Tdoc의 결정 결과(Status)",
        "query": """
            MATCH (t:Tdoc)
            WHERE t.status IS NOT NULL
            RETURN count(t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ7": {
        "desc": "특정 Tdoc의 목적(For)",
        "query": """
            MATCH (t:Tdoc)
            WHERE t.`for` IS NOT NULL
            RETURN count(t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ8": {
        "desc": "특정 Tdoc의 담당자(Contact)",
        "query": """
            MATCH (t:Tdoc)-[:HAS_CONTACT]->(c:Contact)
            RETURN count(DISTINCT c) AS count
        """,
        "expect": "count > 0"
    },
    "CQ9": {
        "desc": "회의별 Agenda 목록과 설명",
        "query": """
            MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem)
            RETURN count(DISTINCT a) AS count
        """,
        "expect": "count > 0"
    },

    # Tdoc 관계 추적 (7개)
    "CQ10": {
        "desc": "특정 Tdoc의 이전/이후 revision",
        "query": """
            MATCH (t:Tdoc)-[:IS_REVISION_OF]->(prev:Tdoc)
            RETURN count(*) AS count
        """,
        "expect": "count > 0"
    },
    "CQ11": {
        "desc": "LS가 어디서 왔고 어디로 갔나",
        "query": """
            MATCH (t:Tdoc)-[:SENT_TO]->(w:WorkingGroup)
            RETURN count(*) AS count
        """,
        "expect": "count > 0"
    },
    "CQ12": {
        "desc": "Tdoc이 어떤 LS의 답변(Reply)인가",
        "query": """
            MATCH (t:Tdoc)
            WHERE t._replyTo IS NOT NULL
            RETURN count(t) AS count
        """,
        "expect": "count >= 0"  # May be 0 if no reply relations
    },
    "CQ13": {
        "desc": "Tdoc이 어떤 TS/Spec을 변경하나",
        "query": """
            MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec)
            RETURN count(*) AS count
        """,
        "expect": "count > 0"
    },
    "CQ14": {
        "desc": "CR의 카테고리와 영향 범위",
        "query": """
            MATCH (t:Tdoc)
            WHERE t.crCategory IS NOT NULL
            RETURN count(t) AS count
        """,
        "expect": "count > 0"
    },
    "CQ15": {
        "desc": "회의에서 다음 회의로 연기된 Tdoc",
        "query": """
            MATCH (t:Tdoc)
            WHERE t.status = 'postponed'
            RETURN count(t) AS count
        """,
        "expect": "count >= 0"
    },
    "CQ16": {
        "desc": "회의에 들어온 LS 목록과 관련 Agenda Item",
        "query": """
            MATCH (t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem)
            RETURN count(*) AS count
        """,
        "expect": "count > 0"
    },

    # 회사/경쟁사 분석 (6개)
    "CQ17": {
        "desc": "특정 회사가 특정 Work Item에서 낸 기고 목록",
        "query": """
            MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company)
            MATCH (t)-[:RELATED_TO]->(w:WorkItem)
            RETURN count(*) AS count
        """,
        "expect": "count > 0"
    },
    "CQ18": {
        "desc": "특정 Agenda Item 관련 다른 회사 기고 목록",
        "query": """
            MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            RETURN count(DISTINCT c) AS count
        """,
        "expect": "count > 0"
    },
    "CQ19": {
        "desc": "Work Item에서 회사별 기고 수",
        "query": """
            MATCH (t:Tdoc)-[:RELATED_TO]->(w:WorkItem)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            RETURN c.companyName, count(t) AS tdocCount
            ORDER BY tdocCount DESC LIMIT 5
        """,
        "expect": "rows > 0"
    },
    "CQ20": {
        "desc": "특정 회사의 Tdoc 중 채택된 비율",
        "query": """
            MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company)
            WITH c.companyName AS company, count(t) AS total,
                 sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS accepted
            WHERE total > 100
            RETURN company, total, accepted, round(100.0 * accepted / total, 2) AS rate
            ORDER BY total DESC LIMIT 5
        """,
        "expect": "rows > 0"
    },
    "CQ21": {
        "desc": "특정 Tdoc과 같은 Agenda Item에서 다른 회사 기고",
        "query": """
            MATCH (t1:Tdoc)-[:BELONGS_TO]->(a:AgendaItem)
            MATCH (t2:Tdoc)-[:BELONGS_TO]->(a)
            WHERE t1 <> t2
            RETURN count(*) AS count LIMIT 1
        """,
        "expect": "count > 0"
    },
    "CQ22": {
        "desc": "특정 회사의 주력 기술 영역",
        "query": """
            MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company)
            MATCH (t)-[:RELATED_TO]->(w:WorkItem)
            WITH c.companyName AS company, w.workItemCode AS wi, count(t) AS cnt
            ORDER BY cnt DESC
            RETURN company, wi, cnt LIMIT 10
        """,
        "expect": "rows > 0"
    },

    # 히스토리/요약 (3개)
    "CQ23": {
        "desc": "특정 기술에서 우리 회사가 여러 회의에 걸쳐 낸 기고",
        "query": """
            MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company)
            MATCH (t)-[:RELATED_TO]->(w:WorkItem)
            MATCH (t)-[:PRESENTED_AT]->(m:Meeting)
            WITH c.companyName AS company, w.workItemCode AS wi,
                 count(DISTINCT m) AS meetings
            WHERE meetings > 3
            RETURN company, wi, meetings
            ORDER BY meetings DESC LIMIT 10
        """,
        "expect": "rows > 0"
    },
    "CQ24": {
        "desc": "회의에서 회사별 기고 결과 요약",
        "query": """
            MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting)
            MATCH (t)-[:SUBMITTED_BY]->(c:Company)
            WITH m.meetingNumber AS meeting, c.companyName AS company,
                 count(t) AS total,
                 sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS accepted
            WHERE total > 50
            RETURN meeting, company, total, accepted
            ORDER BY total DESC LIMIT 10
        """,
        "expect": "rows > 0"
    },
    "CQ25": {
        "desc": "Agenda Item에서 미결(not treated) Tdoc",
        "query": """
            MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem)
            WHERE t.status = 'not treated'
            RETURN count(t) AS count
        """,
        "expect": "count >= 0"
    },
}


def main():
    print("=" * 70)
    print("Sub-step 2-4: CQ 25개 Cypher 쿼리 검증")
    print("=" * 70)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    results = []

    try:
        for cq_id in sorted(CQ_QUERIES.keys(), key=lambda x: int(x[2:])):
            cq = CQ_QUERIES[cq_id]
            print(f"\n[{cq_id}] {cq['desc']}")

            start = time.time()
            with driver.session() as session:
                result = session.run(cq['query'])
                records = list(result)
            elapsed = time.time() - start

            # Check result
            if records:
                if 'count' in records[0].keys():
                    count = records[0]['count']
                    status = "✅" if count > 0 else "⚠️ (0 results)"
                    print(f"  Result: {count}, Time: {elapsed*1000:.1f}ms {status}")
                else:
                    status = "✅" if len(records) > 0 else "⚠️"
                    print(f"  Rows: {len(records)}, Time: {elapsed*1000:.1f}ms {status}")
                    # Show sample
                    if records and len(records) > 0:
                        sample = dict(records[0])
                        print(f"  Sample: {sample}")
            else:
                status = "❌"
                print(f"  No results {status}")

            results.append({
                "cq": cq_id,
                "desc": cq['desc'],
                "time_ms": elapsed * 1000,
                "status": status
            })

        # Summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)

        passed = sum(1 for r in results if "✅" in r['status'])
        warning = sum(1 for r in results if "⚠️" in r['status'])
        failed = sum(1 for r in results if "❌" in r['status'])

        print(f"  ✅ Passed: {passed}")
        print(f"  ⚠️ Warning (0 results): {warning}")
        print(f"  ❌ Failed: {failed}")
        print(f"  Total: {len(results)}")

        avg_time = sum(r['time_ms'] for r in results) / len(results)
        print(f"\n  Average query time: {avg_time:.1f}ms")

        return results

    finally:
        driver.close()


if __name__ == "__main__":
    results = main()
