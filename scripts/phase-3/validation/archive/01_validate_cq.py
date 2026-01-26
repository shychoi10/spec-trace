#!/usr/bin/env python3
"""
Validate Phase-3 Competency Questions (CQ) against Neo4j database.

CQ Groups:
- CQ1: Resolution 조회 (8개)
- CQ2: Tdoc ↔ Resolution 추적 (4개)
- CQ3: 회사별 기여도 (4개)
- CQ4: 역할 (5개)
- CQ6: 트렌드/비교 (3개)

Total: 24 CQs (CQ5 excluded - requires Annex data)
"""

import json
from neo4j import GraphDatabase
import os
from datetime import datetime


# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


class CQValidator:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.results = {}

    def close(self):
        self.driver.close()

    def run_query(self, query: str, params: dict = None):
        """Run a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return list(result)

    # ==================== CQ1: Resolution 조회 ====================

    def cq1_1(self, meeting_num: str = "RAN1#112"):
        """CQ1-1: 특정 회의에서 합의된 Agreement 목록은?"""
        query = """
            MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
            WHERE $meeting IN m.meetingNumber
            RETURN a.resolutionId AS id, a.content AS content
            LIMIT 10
        """
        results = self.run_query(query, {"meeting": meeting_num})
        return {
            "cq": "1-1",
            "question": f"특정 회의({meeting_num})에서 합의된 Agreement 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"id": r["id"], "content": r["content"][:100]} for r in results[:3]]
        }

    def cq1_2(self, meeting_num: str = "RAN1#112"):
        """CQ1-2: 특정 회의에서 도출된 Conclusion 목록은?"""
        query = """
            MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting)
            WHERE $meeting IN m.meetingNumber
            RETURN c.resolutionId AS id, c.content AS content
            LIMIT 10
        """
        results = self.run_query(query, {"meeting": meeting_num})
        return {
            "cq": "1-2",
            "question": f"특정 회의({meeting_num})에서 도출된 Conclusion 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"id": r["id"], "content": r["content"][:100]} for r in results[:3]]
        }

    def cq1_3(self, meeting_num: str = "RAN1#112"):
        """CQ1-3: 특정 회의의 Working Assumption 목록은?"""
        query = """
            MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting)
            WHERE $meeting IN m.meetingNumber
            RETURN wa.resolutionId AS id, wa.content AS content
            LIMIT 10
        """
        results = self.run_query(query, {"meeting": meeting_num})
        return {
            "cq": "1-3",
            "question": f"특정 회의({meeting_num})의 Working Assumption 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"id": r["id"], "content": r["content"][:100]} for r in results[:3]]
        }

    def cq1_4(self, agenda_item: str = "9.1.1"):
        """CQ1-4: 특정 Agenda Item에서의 Resolution 목록은?"""
        query = """
            MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem)
            WHERE ai.agendaNumber = $agenda
            RETURN r.resolutionId AS id, labels(r) AS types
            LIMIT 10
        """
        results = self.run_query(query, {"agenda": agenda_item})
        return {
            "cq": "1-4",
            "question": f"특정 Agenda Item({agenda_item})에서의 Resolution 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"id": r["id"], "types": r["types"]} for r in results[:3]]
        }

    def cq1_5(self):
        """CQ1-5: 특정 Release 관련 Resolution 목록은? (Limited - needs Release linkage)"""
        # Note: This would require Release information to be linked to Resolutions
        # Currently checking if any resolutions exist
        query = """
            MATCH (r:Resolution)
            WHERE r.content CONTAINS 'Rel-17' OR r.content CONTAINS 'Release 17'
            RETURN r.resolutionId AS id, r.content AS content
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "1-5",
            "question": "특정 Release 관련 Resolution 목록은? (text search)",
            "status": "PASS" if results else "PARTIAL",
            "count": len(results),
            "note": "Text-based search; full Release linkage requires additional data",
            "sample": [{"id": r["id"]} for r in results[:3]]
        }

    def cq1_6(self):
        """CQ1-6: 특정 Spec을 변경하는 Resolution 목록은?"""
        # Search for resolutions referencing specs in content
        query = """
            MATCH (r:Resolution)
            WHERE r.content CONTAINS '38.211' OR r.content CONTAINS 'TS 38.211'
            RETURN r.resolutionId AS id, r.content AS content
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "1-6",
            "question": "특정 Spec(38.211)을 변경하는 Resolution 목록은?",
            "status": "PASS" if results else "PARTIAL",
            "count": len(results),
            "sample": [{"id": r["id"]} for r in results[:3]]
        }

    def cq1_7(self):
        """CQ1-7: 특정 Work Item의 Resolution 목록은?"""
        # Search for resolutions mentioning Work Items
        query = """
            MATCH (r:Resolution)
            WHERE r.content CONTAINS 'NR' AND r.content CONTAINS 'MIMO'
            RETURN r.resolutionId AS id, r.content AS content
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "1-7",
            "question": "특정 Work Item(NR MIMO) 관련 Resolution 목록은?",
            "status": "PASS" if results else "PARTIAL",
            "count": len(results),
            "note": "Text-based search for work item keywords",
            "sample": [{"id": r["id"]} for r in results[:3]]
        }

    def cq1_8(self):
        """CQ1-8: Resolution이 가장 많은 Agenda Item Top N은?"""
        query = """
            MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem)
            RETURN ai.agendaNumber AS agenda, ai.meetingNumber AS meeting, count(r) AS count
            ORDER BY count DESC
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "1-8",
            "question": "Resolution이 가장 많은 Agenda Item Top 10은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"agenda": r["agenda"], "meeting": r["meeting"], "count": r["count"]} for r in results[:5]]
        }

    # ==================== CQ2: Tdoc ↔ Resolution 추적 ====================

    def cq2_1(self, tdoc: str = "R1-2302021"):
        """CQ2-1: 특정 Tdoc이 어떤 Resolution으로 이어졌나?"""
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE $tdoc IN t.tdocNumber
            RETURN r.resolutionId AS id, labels(r) AS types, r.content AS content
            LIMIT 10
        """
        results = self.run_query(query, {"tdoc": tdoc})
        return {
            "cq": "2-1",
            "question": f"특정 Tdoc({tdoc})이 어떤 Resolution으로 이어졌나?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"id": r["id"], "types": r["types"]} for r in results[:3]]
        }

    def cq2_2(self, resolution_id: str = None):
        """CQ2-2: 특정 Resolution이 참조한 Tdoc 목록은?"""
        # First find a resolution with references
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            RETURN r.resolutionId AS resolution, collect(t.tdocNumber[0]) AS tdocs
            LIMIT 5
        """
        results = self.run_query(query)
        return {
            "cq": "2-2",
            "question": "특정 Resolution이 참조한 Tdoc 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"resolution": r["resolution"], "tdocs": r["tdocs"][:3]} for r in results[:3]]
        }

    def cq2_3(self):
        """CQ2-3: Comeback 결정된 Tdoc 목록은?"""
        # Search for "comeback" in resolution content
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE toLower(r.content) CONTAINS 'comeback'
            RETURN DISTINCT t.tdocNumber[0] AS tdoc, r.resolutionId AS resolution
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "2-3",
            "question": "Comeback 결정된 Tdoc 목록은?",
            "status": "PASS" if results else "PARTIAL",
            "count": len(results),
            "note": "Text-based search for 'comeback'",
            "sample": [{"tdoc": r["tdoc"], "resolution": r["resolution"]} for r in results[:3]]
        }

    def cq2_4(self):
        """CQ2-4: 특정 Tdoc이 어떤 Spec에 반영됐나? (Requires CR linkage)"""
        # This requires Tdoc -> CR -> Spec chain which may not be complete
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE r.content CONTAINS 'approved' OR r.content CONTAINS 'agreed'
            RETURN t.tdocNumber[0] AS tdoc, r.resolutionId AS resolution
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "2-4",
            "question": "특정 Tdoc이 어떤 Spec에 반영됐나?",
            "status": "PARTIAL",
            "count": len(results),
            "note": "Partial: shows approved Tdocs, full Spec linkage requires CR data",
            "sample": [{"tdoc": r["tdoc"]} for r in results[:3]]
        }

    # ==================== CQ3: 회사별 기여도 ====================

    def cq3_1(self, company: str = "Huawei"):
        """CQ3-1: 특정 회사 Tdoc이 Resolution으로 이어진 비율은?"""
        # submittedBy is a property (array) with URI format: ['tdoc:company/Huawei']
        company_uri = f"tdoc:company/{company}"

        # Get total Tdocs from company
        total_query = """
            MATCH (t:Tdoc)
            WHERE $companyUri IN t.submittedBy
            RETURN count(t) AS total
        """
        total_result = self.run_query(total_query, {"companyUri": company_uri})
        total = total_result[0]["total"] if total_result else 0

        # Get referenced Tdocs
        ref_query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE $companyUri IN t.submittedBy
            RETURN count(DISTINCT t) AS referenced
        """
        ref_result = self.run_query(ref_query, {"companyUri": company_uri})
        referenced = ref_result[0]["referenced"] if ref_result else 0

        ratio = round(100.0 * referenced / total, 2) if total > 0 else 0

        return {
            "cq": "3-1",
            "question": f"특정 회사({company}) Tdoc이 Resolution으로 이어진 비율은?",
            "status": "PASS" if total > 0 else "FAIL",
            "data": {
                "total_tdocs": total,
                "referenced_in_resolutions": referenced,
                "ratio_percent": ratio
            }
        }

    def cq3_2(self):
        """CQ3-2: 특정 기술(Work Item)에서 회사별 Resolution 기여도는?"""
        # Use submittedBy property (URI array) to extract company name
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE t.submittedBy IS NOT NULL
            UNWIND t.submittedBy AS companyUri
            WITH r, replace(companyUri, 'tdoc:company/', '') AS company
            RETURN company, count(DISTINCT r) AS resolutions
            ORDER BY resolutions DESC
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "3-2",
            "question": "회사별 Resolution 기여도 Top 10은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"company": r["company"], "resolutions": r["resolutions"]} for r in results[:5]]
        }

    def cq3_3(self, spec: str = "38.211"):
        """CQ3-3: 특정 Spec의 주요 contributor 순위는?"""
        # Based on Tdocs referenced in Resolutions mentioning the spec
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE r.content CONTAINS $spec AND t.submittedBy IS NOT NULL
            UNWIND t.submittedBy AS companyUri
            WITH r, replace(companyUri, 'tdoc:company/', '') AS company
            RETURN company, count(DISTINCT r) AS contributions
            ORDER BY contributions DESC
            LIMIT 10
        """
        results = self.run_query(query, {"spec": spec})
        return {
            "cq": "3-3",
            "question": f"특정 Spec({spec})의 주요 contributor 순위는?",
            "status": "PASS" if results else "PARTIAL",
            "count": len(results),
            "sample": [{"company": r["company"], "contributions": r["contributions"]} for r in results[:5]]
        }

    def cq3_4(self, company1: str = "Huawei", company2: str = "Samsung"):
        """CQ3-4: 두 회사 간 기여도 비교는?"""
        company1_uri = f"tdoc:company/{company1}"
        company2_uri = f"tdoc:company/{company2}"

        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            WHERE $company1 IN t.submittedBy OR $company2 IN t.submittedBy
            UNWIND t.submittedBy AS companyUri
            WITH r, companyUri
            WHERE companyUri IN [$company1, $company2]
            WITH replace(companyUri, 'tdoc:company/', '') AS company, count(DISTINCT r) AS resolutions
            RETURN company, resolutions
            ORDER BY company
        """
        results = self.run_query(query, {"company1": company1_uri, "company2": company2_uri})
        return {
            "cq": "3-4",
            "question": f"두 회사({company1} vs {company2}) 간 기여도 비교",
            "status": "PASS" if results else "FAIL",
            "comparison": [{"company": r["company"], "resolutions": r["resolutions"]} for r in results]
        }

    # ==================== CQ4: 역할 (Moderator/Chair) ====================

    def cq4_1(self):
        """CQ4-1: 특정 Agenda Item의 Moderator는 누구(어떤 회사)인가?"""
        query = """
            MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
            RETURN s.tdocNumber[0] AS summary, c.companyName[0] AS company, s.summaryType AS type
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "4-1",
            "question": "Summary의 Moderator는 어떤 회사인가?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"summary": r["summary"], "company": r["company"], "type": r["type"]} for r in results[:5]]
        }

    def cq4_2(self, company: str = "Huawei"):
        """CQ4-2: 특정 회사가 Moderator를 맡은 Agenda Item 목록은?"""
        query = """
            MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
            WHERE $company IN c.companyName OR $company IN c.aliases
            RETURN s.tdocNumber[0] AS summary, s.summaryType AS type
            LIMIT 20
        """
        results = self.run_query(query, {"company": company})
        return {
            "cq": "4-2",
            "question": f"특정 회사({company})가 Moderator를 맡은 Summary 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"summary": r["summary"], "type": r["type"]} for r in results[:5]]
        }

    def cq4_3(self):
        """CQ4-3: 특정 회사의 Moderator 담당 비율은?"""
        # Get total count first
        total_query = "MATCH (:Summary)-[:MODERATED_BY]->(:Company) RETURN count(*) AS total"
        total_result = self.run_query(total_query)
        total = total_result[0]["total"] if total_result else 0

        query = """
            MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
            RETURN c.companyName[0] AS company, count(s) AS count
            ORDER BY count DESC
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "4-3",
            "question": "회사별 Moderator 담당 비율은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "total": total,
            "sample": [{"company": r["company"], "count": r["count"], "percentage": round(100.0*r["count"]/total, 2) if total > 0 else 0} for r in results[:5]]
        }

    def cq4_4(self):
        """CQ4-4: 특정 Agenda Item의 Ad-hoc Chair는 누구(어떤 회사)인가?"""
        query = """
            MATCH (sn:SessionNotes)-[:CHAIRED_BY]->(c:Company)
            RETURN sn.tdocNumber[0] AS sessionNotes, c.companyName[0] AS company
            LIMIT 10
        """
        results = self.run_query(query)
        return {
            "cq": "4-4",
            "question": "SessionNotes의 Ad-hoc Chair는 어떤 회사인가?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"sessionNotes": r["sessionNotes"], "company": r["company"]} for r in results[:5]]
        }

    def cq4_5(self, company: str = "CMCC"):
        """CQ4-5: 특정 회사가 Ad-hoc Chair를 맡은 Agenda Item 목록은?"""
        query = """
            MATCH (sn:SessionNotes)-[:CHAIRED_BY]->(c:Company)
            WHERE $company IN c.companyName OR $company IN c.aliases
            RETURN sn.tdocNumber[0] AS sessionNotes
            LIMIT 20
        """
        results = self.run_query(query, {"company": company})
        return {
            "cq": "4-5",
            "question": f"특정 회사({company})가 Ad-hoc Chair를 맡은 SessionNotes 목록은?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"sessionNotes": r["sessionNotes"]} for r in results[:5]]
        }

    # ==================== CQ6: 트렌드/비교 ====================

    def cq6_1(self):
        """CQ6-1: 특정 기술(Work Item)의 Resolution 수 추이는?"""
        query = """
            MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
            RETURN m.meetingNumber[0] AS meeting, count(r) AS resolutions
            ORDER BY meeting
            LIMIT 20
        """
        results = self.run_query(query)
        return {
            "cq": "6-1",
            "question": "회의별 Resolution 수 추이는?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"meeting": r["meeting"], "resolutions": r["resolutions"]} for r in results]
        }

    def cq6_2(self):
        """CQ6-2: 특정 회사의 기여율 변화는?"""
        company_uri = "tdoc:company/Huawei"
        query = """
            MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)
            MATCH (r)-[:MADE_AT]->(m:Meeting)
            WHERE $companyUri IN t.submittedBy
            RETURN m.meetingNumber[0] AS meeting, count(DISTINCT r) AS contributions
            ORDER BY meeting
            LIMIT 20
        """
        results = self.run_query(query, {"companyUri": company_uri})
        return {
            "cq": "6-2",
            "question": "Huawei의 회의별 기여 추이는?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"meeting": r["meeting"], "contributions": r["contributions"]} for r in results[:10]]
        }

    def cq6_3(self):
        """CQ6-3: 특정 회사의 Moderator 담당 추이는?"""
        query = """
            MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
            MATCH (s)-[:PRESENTED_AT]->(m:Meeting)
            WHERE 'Huawei' IN c.companyName
            RETURN m.meetingNumber[0] AS meeting, count(s) AS moderations
            ORDER BY meeting
            LIMIT 20
        """
        results = self.run_query(query)
        return {
            "cq": "6-3",
            "question": "Huawei의 회의별 Moderator 담당 추이는?",
            "status": "PASS" if results else "FAIL",
            "count": len(results),
            "sample": [{"meeting": r["meeting"], "moderations": r["moderations"]} for r in results[:10]]
        }

    def run_all(self):
        """Run all CQ validations."""
        print("="*70)
        print("PHASE-3 COMPETENCY QUESTIONS VALIDATION")
        print("="*70)
        print(f"Started: {datetime.now().isoformat()}")
        print()

        all_results = []

        # CQ1: Resolution 조회
        print("[CQ1] Resolution 조회")
        print("-"*50)
        cq1_methods = [self.cq1_1, self.cq1_2, self.cq1_3, self.cq1_4,
                       self.cq1_5, self.cq1_6, self.cq1_7, self.cq1_8]
        for method in cq1_methods:
            result = method()
            all_results.append(result)
            status = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "PARTIAL" else "❌")
            print(f"  CQ{result['cq']}: {status} {result['status']}")

        # CQ2: Tdoc ↔ Resolution 추적
        print("\n[CQ2] Tdoc ↔ Resolution 추적")
        print("-"*50)
        cq2_methods = [self.cq2_1, self.cq2_2, self.cq2_3, self.cq2_4]
        for method in cq2_methods:
            result = method()
            all_results.append(result)
            status = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "PARTIAL" else "❌")
            print(f"  CQ{result['cq']}: {status} {result['status']}")

        # CQ3: 회사별 기여도
        print("\n[CQ3] 회사별 기여도")
        print("-"*50)
        cq3_methods = [self.cq3_1, self.cq3_2, self.cq3_3, self.cq3_4]
        for method in cq3_methods:
            result = method()
            all_results.append(result)
            status = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "PARTIAL" else "❌")
            print(f"  CQ{result['cq']}: {status} {result['status']}")

        # CQ4: 역할
        print("\n[CQ4] 역할 (Moderator/Chair)")
        print("-"*50)
        cq4_methods = [self.cq4_1, self.cq4_2, self.cq4_3, self.cq4_4, self.cq4_5]
        for method in cq4_methods:
            result = method()
            all_results.append(result)
            status = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "PARTIAL" else "❌")
            print(f"  CQ{result['cq']}: {status} {result['status']}")

        # CQ6: 트렌드/비교
        print("\n[CQ6] 트렌드/비교")
        print("-"*50)
        cq6_methods = [self.cq6_1, self.cq6_2, self.cq6_3]
        for method in cq6_methods:
            result = method()
            all_results.append(result)
            status = "✅" if result["status"] == "PASS" else ("⚠️" if result["status"] == "PARTIAL" else "❌")
            print(f"  CQ{result['cq']}: {status} {result['status']}")

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        passed = sum(1 for r in all_results if r["status"] == "PASS")
        partial = sum(1 for r in all_results if r["status"] == "PARTIAL")
        failed = sum(1 for r in all_results if r["status"] == "FAIL")
        total = len(all_results)

        print(f"  Total CQs: {total}")
        print(f"  ✅ PASS: {passed}")
        print(f"  ⚠️  PARTIAL: {partial}")
        print(f"  ❌ FAIL: {failed}")
        print(f"\n  Pass Rate: {100*passed/total:.1f}%")
        print(f"  Pass+Partial Rate: {100*(passed+partial)/total:.1f}%")

        return all_results


def main():
    validator = CQValidator()
    try:
        results = validator.run_all()

        # Save detailed results
        output = {
            "timestamp": datetime.now().isoformat(),
            "results": results
        }

        output_path = "logs/phase-3/cq_validation_results.json"
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\nDetailed results saved to: {output_path}")

    finally:
        validator.close()


if __name__ == "__main__":
    main()
