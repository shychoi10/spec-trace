#!/usr/bin/env python3
"""
Generate Realistic CQ Test Dataset for Phase-3 Validation.

CQ 테스트 케이스 설계 원칙:
1. Option A: 회의 + 아젠다 조합 필수화 (예: "RAN1#112 회의의 MIMO 관련 Agreement는?")
2. Option B: 주제명 기반 질의 (예: "'Multi-TRP enhancement' 관련 Resolution은?")
3. Option C: 구체적인 컨텍스트 제공 (예: 특정 Resolution ID, 특정 회사명)

- 맥락 없는 아젠다 번호만의 질문 금지
- 사용자가 실제로 물어볼 만한 자연스러운 질문만 생성
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
PARSED_DIR = BASE_DIR / "ontology" / "output" / "parsed_reports" / "v2"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"


def load_rich_data():
    """Load data with agenda topics and meeting context."""
    data = {
        "meetings": [],
        "agenda_topics": defaultdict(dict),  # {meeting: {agenda: title}}
        "agreements": [],
        "conclusions": [],
        "working_assumptions": [],
        "session_notes": [],
        "fl_summaries": [],
        "moderator_summaries": [],
        "companies": set(),
        "top_referenced_agreements": [],  # Agreements with most Tdoc refs
    }

    for f in sorted(PARSED_DIR.glob("RAN1_*_v2.json")):
        with open(f) as fp:
            parsed = json.load(fp)
            meeting_id = parsed["meeting_id"]
            data["meetings"].append(meeting_id)

            # TOC → agenda + topic 매핑
            for toc in parsed.get("toc_entries", []):
                agenda = toc.get("agenda_number", "")
                title = toc.get("title", "")
                if agenda and title:
                    data["agenda_topics"][meeting_id][agenda] = title

            # Agreements
            for agr in parsed["agreements"]:
                item = {
                    "meeting": meeting_id,
                    "id": agr["decision_id"],
                    "agenda": agr["agenda_item"],
                    "content": agr["content"][:200],
                    "tdocs": agr.get("referenced_tdocs", []),
                    "topic": data["agenda_topics"][meeting_id].get(agr["agenda_item"], "")
                }
                data["agreements"].append(item)
                if len(item["tdocs"]) >= 5:
                    data["top_referenced_agreements"].append(item)

            # Conclusions
            for conc in parsed["conclusions"]:
                data["conclusions"].append({
                    "meeting": meeting_id,
                    "id": conc["decision_id"],
                    "agenda": conc["agenda_item"],
                    "content": conc["content"][:200],
                    "topic": data["agenda_topics"][meeting_id].get(conc["agenda_item"], "")
                })

            # Working Assumptions
            for wa in parsed["working_assumptions"]:
                data["working_assumptions"].append({
                    "meeting": meeting_id,
                    "id": wa["decision_id"],
                    "agenda": wa["agenda_item"],
                    "content": wa["content"][:200],
                    "topic": data["agenda_topics"][meeting_id].get(wa["agenda_item"], "")
                })

            # Session Notes
            for sn in parsed["session_notes"]:
                data["session_notes"].append({
                    "meeting": meeting_id,
                    "tdoc": sn.get("tdoc_number", ""),
                    "agenda": sn.get("agenda_item", ""),
                    "company": sn.get("company", "")
                })
                if sn.get("company"):
                    data["companies"].add(sn.get("company"))

            # FL Summaries
            for fl in parsed["fl_summaries"]:
                data["fl_summaries"].append({
                    "meeting": meeting_id,
                    "tdoc": fl.get("tdoc_number", ""),
                    "title": fl.get("title", ""),
                    "agenda": fl.get("agenda_item", ""),
                    "company": fl.get("company", "")
                })
                if fl.get("company"):
                    data["companies"].add(fl.get("company"))

            # Moderator Summaries
            for ms in parsed["moderator_summaries"]:
                data["moderator_summaries"].append({
                    "meeting": meeting_id,
                    "tdoc": ms.get("tdoc_number", ""),
                    "title": ms.get("title", ""),
                    "agenda": ms.get("agenda_item", ""),
                    "company": ms.get("company", "")
                })
                if ms.get("company"):
                    data["companies"].add(ms.get("company"))

    # Sort top referenced agreements
    data["top_referenced_agreements"].sort(key=lambda x: len(x["tdocs"]), reverse=True)
    data["companies"] = list(data["companies"])

    return data


def generate_realistic_test_cases(data: dict) -> list:
    """Generate 100 realistic CQ test cases with proper context."""
    test_cases = []
    case_id = 1

    meetings = data["meetings"]
    agenda_topics = data["agenda_topics"]
    agreements = data["agreements"]
    conclusions = data["conclusions"]
    working_assumptions = data["working_assumptions"]
    fl_summaries = data["fl_summaries"]
    moderator_summaries = data["moderator_summaries"]
    session_notes = data["session_notes"]
    companies = [c for c in data["companies"] if c and c != "UNKNOWN"]
    top_refs = data["top_referenced_agreements"]

    # ==================== CQ1: Resolution 조회 (25 cases) ====================

    # CQ1-1: 특정 회의의 Agreement 목록 (5 cases)
    # Option A: 회의 기반 (명확한 컨텍스트)
    sample_meetings = ["RAN1#112", "RAN1#118", "RAN1#100", "RAN1#110", "RAN1#115"]
    for meeting in sample_meetings[:5]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ1-1",
            "question": f"{meeting} 회의에서 합의된 Agreement 목록은?",
            "cypher_query": f"""
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber
RETURN a.resolutionId AS id, a.content AS content
LIMIT 10""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting} 회의의 Agreement 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # CQ1-2: 특정 회의의 Conclusion 목록 (5 cases)
    for meeting in ["RAN1#103", "RAN1#109", "RAN1#114", "RAN1#120", "RAN1#122b"]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ1-2",
            "question": f"{meeting} 회의에서 도출된 Conclusion 목록은?",
            "cypher_query": f"""
MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber
RETURN c.resolutionId AS id, c.content AS content
LIMIT 10""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting} 회의의 Conclusion 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # CQ1-3: 특정 회의의 Working Assumption 목록 (5 cases)
    for meeting in ["RAN1#104", "RAN1#106", "RAN1#108", "RAN1#111", "RAN1#116"]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ1-3",
            "question": f"{meeting} 회의에서 설정된 Working Assumption은?",
            "cypher_query": f"""
MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber
RETURN wa.resolutionId AS id, wa.content AS content
LIMIT 10""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting} 회의의 Working Assumption 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # CQ1-4: 회의 + 아젠다 + 주제 조합 (5 cases)
    # Option A: 회의 + 아젠다 + 주제명 (완전한 컨텍스트)
    meeting_agenda_pairs = [
        ("RAN1#112", "8.1", "MIMO enhancement"),
        ("RAN1#118", "9.1.1", "beam management"),
        ("RAN1#110", "8.2", "52.6GHz to 71 GHz"),
        ("RAN1#103", "8.5", "Positioning Enhancements"),
        ("RAN1#109", "9.1.1", "Multi-TRP enhancement")
    ]
    for meeting, agenda, topic_hint in meeting_agenda_pairs:
        # Get actual topic from data if available
        actual_topic = agenda_topics.get(meeting, {}).get(agenda, topic_hint)
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ1-4",
            "question": f"{meeting} 회의 Agenda {agenda} ({actual_topic[:40]}) 관련 Resolution은?",
            "cypher_query": f"""
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber AND r.resolutionId CONTAINS '-{agenda}-'
RETURN r.resolutionId AS id, labels(r) AS types, r.content AS content
LIMIT 10""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting} 회의 Agenda {agenda}의 Resolution 목록",
            "parameters": {"meeting": meeting, "agenda": agenda, "topic": actual_topic}
        })
        case_id += 1

    # CQ1-5: 키워드/주제 기반 검색 (5 cases)
    # Option B: 주제명 기반 질의 (사용자가 실제로 검색할 키워드)
    keywords_with_context = [
        ("MIMO", "MIMO 관련 기술"),
        ("beam management", "빔 관리"),
        ("positioning", "측위/위치 결정"),
        ("power saving", "전력 절감"),
        ("Multi-TRP", "다중 TRP 전송")
    ]
    for keyword, desc in keywords_with_context:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ1-5",
            "question": f"'{keyword}' ({desc}) 관련 Resolution 목록은?",
            "cypher_query": f"""
MATCH (r:Resolution)
WHERE toLower(r.content) CONTAINS toLower('{keyword}')
RETURN r.resolutionId AS id, labels(r) AS types
LIMIT 20""",
            "expected_result_type": "list",
            "expected_answer": f"'{keyword}' 키워드 포함 Resolution 목록",
            "parameters": {"keyword": keyword, "description": desc}
        })
        case_id += 1

    # ==================== CQ2: Tdoc ↔ Resolution 추적 (20 cases) ====================

    # CQ2-1: 특정 Resolution의 참조 Tdoc (10 cases)
    # Option C: 구체적인 Resolution ID로 질의
    for agr in top_refs[:10]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ2-1",
            "question": f"Resolution {agr['id']}이 참조한 Tdoc 목록은? (이 Resolution은 {len(agr['tdocs'])}개의 Tdoc을 참조함)",
            "cypher_query": f"""
MATCH (r:Resolution {{resolutionId: '{agr['id']}'}})-[:REFERENCES]->(t:Tdoc)
RETURN t.tdocNumber AS tdoc
LIMIT 20""",
            "expected_result_type": "list",
            "expected_answer": f"Resolution {agr['id']}의 참조 Tdoc ({len(agr['tdocs'])}개 예상)",
            "parameters": {
                "resolution_id": agr['id'],
                "meeting": agr['meeting'],
                "expected_count": len(agr['tdocs'])
            }
        })
        case_id += 1

    # CQ2-2: Tdoc 참조 많은 Resolution Top N (10 cases)
    # 다양한 조건으로 Top N 질의
    for i, (meeting, min_refs) in enumerate([
        ("RAN1#87", 50),
        ("RAN1#103", 30),
        ("RAN1#122b", 40),
        ("RAN1#86b", 40),
        ("RAN1#88", 30),
        (None, 50),  # 전체
        (None, 30),
        (None, 20),
        (None, 10),
        (None, 5)
    ]):
        if meeting:
            question = f"{meeting} 회의에서 Tdoc을 {min_refs}개 이상 참조한 Resolution은?"
            query = f"""
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
MATCH (r)-[:MADE_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber
WITH r, count(t) AS tdoc_count
WHERE tdoc_count >= {min_refs}
RETURN r.resolutionId AS id, tdoc_count
ORDER BY tdoc_count DESC
LIMIT 10"""
        else:
            question = f"Tdoc을 가장 많이 참조한 Resolution Top 10은? (최소 {min_refs}개 이상)"
            query = f"""
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
WITH r, count(t) AS tdoc_count
WHERE tdoc_count >= {min_refs}
RETURN r.resolutionId AS id, tdoc_count
ORDER BY tdoc_count DESC
LIMIT 10"""
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ2-2",
            "question": question,
            "cypher_query": query,
            "expected_result_type": "ranked_list",
            "expected_answer": f"Tdoc 참조 {min_refs}개 이상 Resolution 순위",
            "parameters": {"meeting": meeting, "min_refs": min_refs}
        })
        case_id += 1

    # ==================== CQ3: 회사별 기여도 (20 cases) ====================

    # CQ3-1: 특정 회사의 FL Summary 목록 (10 cases)
    # 실제 존재하는 회사로 질의
    top_companies = ["Huawei", "Ericsson", "vivo", "Qualcomm", "OPPO",
                     "Samsung", "Nokia", "Apple", "ZTE", "MediaTek"]
    for company in top_companies:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ3-1",
            "question": f"{company}가 Moderator로 작성한 FL Summary 목록은?",
            "cypher_query": f"""
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
WHERE '{company}' IN c.companyName OR c.companyName[0] CONTAINS '{company}'
RETURN s.tdocNumber AS tdoc, s.title AS title, s.meetingId AS meeting
LIMIT 15""",
            "expected_result_type": "list",
            "expected_answer": f"{company}의 FL Summary 목록",
            "parameters": {"company": company}
        })
        case_id += 1

    # CQ3-2: 회사별 Moderator 담당 횟수 순위 (5 cases)
    for limit in [5, 10, 15, 20, 30]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ3-2",
            "question": f"FL Summary를 가장 많이 작성한 회사 Top {limit}은?",
            "cypher_query": f"""
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
RETURN c.companyName[0] AS company, count(s) AS summary_count
ORDER BY summary_count DESC
LIMIT {limit}""",
            "expected_result_type": "ranked_list",
            "expected_answer": f"FL Summary 작성 Top {limit} 회사",
            "parameters": {"limit": limit}
        })
        case_id += 1

    # CQ3-3: 두 회사 비교 (5 cases)
    company_pairs = [
        ("Huawei", "Ericsson"),
        ("Qualcomm", "Samsung"),
        ("Nokia", "Apple"),
        ("vivo", "OPPO"),
        ("ZTE", "MediaTek")
    ]
    for c1, c2 in company_pairs:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ3-3",
            "question": f"{c1}와 {c2}의 FL Summary 작성 횟수 비교는?",
            "cypher_query": f"""
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
WHERE c.companyName[0] IN ['{c1}', '{c2}']
RETURN c.companyName[0] AS company, count(s) AS count
ORDER BY count DESC""",
            "expected_result_type": "comparison",
            "expected_answer": f"{c1} vs {c2} FL Summary 비교",
            "parameters": {"company1": c1, "company2": c2}
        })
        case_id += 1

    # ==================== CQ4: 역할 (SessionNotes, Summary) (20 cases) ====================

    # CQ4-1: 특정 회의의 SessionNotes (5 cases)
    for meeting in ["RAN1#112", "RAN1#118", "RAN1#110", "RAN1#115", "RAN1#120"]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ4-1",
            "question": f"{meeting} 회의의 Session Notes 목록은?",
            "cypher_query": f"""
MATCH (sn:SessionNotes)-[:PRESENTED_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber
RETURN sn.tdocNumber AS tdoc, sn.agendaItem AS agenda, sn.title AS title""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting}의 Session Notes 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # CQ4-2: 특정 회의의 FL Summary (5 cases)
    for meeting in ["RAN1#112", "RAN1#118", "RAN1#103", "RAN1#109", "RAN1#114"]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ4-2",
            "question": f"{meeting} 회의의 FL Summary 목록은?",
            "cypher_query": f"""
MATCH (s:Summary)-[:PRESENTED_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber AND s.summaryType = 'FL'
RETURN s.tdocNumber AS tdoc, s.title AS title, s.agendaItem AS agenda
LIMIT 15""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting}의 FL Summary 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # CQ4-3: 특정 회의의 Moderator Summary (5 cases)
    for meeting in ["RAN1#112", "RAN1#118", "RAN1#100", "RAN1#106", "RAN1#110"]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ4-3",
            "question": f"{meeting} 회의의 Moderator Summary 목록은?",
            "cypher_query": f"""
MATCH (s:Summary)-[:PRESENTED_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber AND s.summaryType = 'Moderator'
RETURN s.tdocNumber AS tdoc, s.title AS title, s.agendaItem AS agenda
LIMIT 15""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting}의 Moderator Summary 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # CQ4-4: Ad-hoc Chair 조회 (5 cases)
    for meeting in ["RAN1#112", "RAN1#118", "RAN1#110", "RAN1#100", "RAN1#103"]:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ4-4",
            "question": f"{meeting} 회의의 Ad-hoc Session을 주관한 회사는?",
            "cypher_query": f"""
MATCH (sn:SessionNotes)-[:CHAIRED_BY]->(c:Company)
MATCH (sn)-[:PRESENTED_AT]->(m:Meeting)
WHERE '{meeting}' IN m.meetingNumber
RETURN sn.tdocNumber AS sessionNotes, sn.agendaItem AS agenda, c.companyName[0] AS company""",
            "expected_result_type": "list",
            "expected_answer": f"{meeting}의 Ad-hoc Chair 회사 목록",
            "parameters": {"meeting": meeting}
        })
        case_id += 1

    # ==================== CQ6: 트렌드/비교 (15 cases) ====================

    # CQ6-1: 회의별 Resolution 수 추이 (5 cases)
    meeting_ranges = [
        ("RAN1#100", "RAN1#110", "2020년"),
        ("RAN1#110", "RAN1#120", "2021-2022년"),
        ("RAN1#84", "RAN1#94", "초기 NR 표준화"),
        ("RAN1#100", "RAN1#122b", "전체"),
        ("RAN1#115", "RAN1#122b", "최근")
    ]
    for start, end, period in meeting_ranges:
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ6-1",
            "question": f"{start}부터 {end}까지 ({period}) 회의별 Resolution 수 추이는?",
            "cypher_query": f"""
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
RETURN m.meetingNumber[0] AS meeting, count(r) AS resolutions
ORDER BY meeting
LIMIT 30""",
            "expected_result_type": "trend",
            "expected_answer": f"{period} 회의별 Resolution 수 추이",
            "parameters": {"start": start, "end": end, "period": period}
        })
        case_id += 1

    # CQ6-2: Resolution 유형별 분포 (5 cases)
    for scope, desc in [
        (None, "전체"),
        ("RAN1#112", "RAN1#112 회의"),
        ("RAN1#118", "RAN1#118 회의"),
        ("RAN1#100", "RAN1#100 회의"),
        ("RAN1#103", "RAN1#103 회의")
    ]:
        if scope:
            question = f"{desc}의 Resolution 유형별(Agreement/Conclusion/WA) 분포는?"
            query = f"""
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WHERE '{scope}' IN m.meetingNumber
WITH r
UNWIND labels(r) AS type
WHERE type <> 'Resolution'
RETURN type, count(*) AS count
ORDER BY count DESC"""
        else:
            question = f"{desc} Resolution 유형별(Agreement/Conclusion/WA) 분포는?"
            query = """
MATCH (r:Resolution)
UNWIND labels(r) AS type
WHERE type <> 'Resolution'
RETURN type, count(*) AS count
ORDER BY count DESC"""
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ6-2",
            "question": question,
            "cypher_query": query,
            "expected_result_type": "distribution",
            "expected_answer": f"{desc} Agreement/Conclusion/WA 비율",
            "parameters": {"scope": scope}
        })
        case_id += 1

    # CQ6-3: 통계 (5 cases)
    stats_questions = [
        ("회의당 평균 Resolution 수는?", "avg"),
        ("Resolution이 가장 많았던 회의는?", "max"),
        ("Resolution이 가장 적었던 회의는?", "min"),
        ("Agreement와 Conclusion의 비율은?", "ratio"),
        ("Tdoc을 참조하는 Resolution 비율은?", "ref_ratio")
    ]
    for question, stat_type in stats_questions:
        if stat_type == "avg":
            query = """
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WITH m, count(r) AS resolutions
RETURN round(avg(resolutions)) AS avg_resolutions, min(resolutions) AS min, max(resolutions) AS max"""
        elif stat_type == "max":
            query = """
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WITH m.meetingNumber[0] AS meeting, count(r) AS resolutions
ORDER BY resolutions DESC
LIMIT 5
RETURN meeting, resolutions"""
        elif stat_type == "min":
            query = """
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WITH m.meetingNumber[0] AS meeting, count(r) AS resolutions
ORDER BY resolutions ASC
LIMIT 5
RETURN meeting, resolutions"""
        elif stat_type == "ratio":
            query = """
MATCH (r:Resolution)
UNWIND labels(r) AS type
WHERE type IN ['Agreement', 'Conclusion', 'WorkingAssumption']
WITH type, count(*) AS count
WITH collect({type: type, count: count}) AS stats
RETURN stats"""
        else:  # ref_ratio
            query = """
MATCH (r:Resolution)
OPTIONAL MATCH (r)-[:REFERENCES]->(t:Tdoc)
WITH r, count(t) AS refs
RETURN count(CASE WHEN refs > 0 THEN 1 END) AS with_refs, count(*) AS total,
       round(100.0 * count(CASE WHEN refs > 0 THEN 1 END) / count(*), 1) AS percentage"""
        test_cases.append({
            "id": f"TC-{case_id:03d}",
            "cq_type": "CQ6-3",
            "question": question,
            "cypher_query": query,
            "expected_result_type": "statistics",
            "expected_answer": question,
            "parameters": {"stat_type": stat_type}
        })
        case_id += 1

    return test_cases[:100]


def main():
    print("=" * 70)
    print("REALISTIC CQ TEST DATASET GENERATION")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    print("설계 원칙:")
    print("  - Option A: 회의 + 아젠다 조합 (완전한 컨텍스트)")
    print("  - Option B: 주제명 기반 질의 (사용자 친화적)")
    print("  - Option C: 구체적인 ID/회사명 (명확한 타겟)")
    print()

    # Load data
    print("[1/3] Loading data with agenda topics...")
    data = load_rich_data()
    print(f"  - Meetings: {len(data['meetings'])}")
    print(f"  - Agreements: {len(data['agreements'])}")
    print(f"  - Top Referenced: {len(data['top_referenced_agreements'])} (5+ Tdoc refs)")
    print(f"  - Companies: {len(data['companies'])}")
    print(f"  - Agenda Topics: {sum(len(v) for v in data['agenda_topics'].values())} mappings")

    # Generate test cases
    print("\n[2/3] Generating 100 realistic test cases...")
    test_cases = generate_realistic_test_cases(data)
    print(f"  - Generated: {len(test_cases)} test cases")

    # Count by CQ type
    cq_counts = {}
    for tc in test_cases:
        cq_type = tc["cq_type"]
        cq_counts[cq_type] = cq_counts.get(cq_type, 0) + 1

    print("\n  Test cases by CQ type:")
    for cq_type in sorted(cq_counts.keys()):
        print(f"    - {cq_type}: {cq_counts[cq_type]}")

    # Save
    print("\n[3/3] Saving test dataset...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "cq_test_dataset_100.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "version": "2.0-realistic",
        "design_principles": [
            "Option A: 회의 + 아젠다 조합 필수화",
            "Option B: 주제명 기반 질의",
            "Option C: 구체적인 컨텍스트 제공"
        ],
        "total_cases": len(test_cases),
        "cq_type_distribution": cq_counts,
        "test_cases": test_cases
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  - Saved to: {output_file}")

    # Summary
    print("\n" + "=" * 70)
    print("SAMPLE TEST CASES (New Realistic Design)")
    print("=" * 70)

    # Show examples of each option
    examples = [
        ("CQ1-4", "Option A (회의+아젠다+주제)"),
        ("CQ1-5", "Option B (주제명 기반)"),
        ("CQ2-1", "Option C (구체적 ID)")
    ]
    for cq_type, desc in examples:
        for tc in test_cases:
            if tc["cq_type"] == cq_type:
                print(f"\n[{tc['id']}] {tc['cq_type']} - {desc}")
                print(f"  Q: {tc['question']}")
                print(f"  Params: {tc['parameters']}")
                break

    return test_cases


if __name__ == "__main__":
    main()
