#!/usr/bin/env python3
"""
Validate CQ Test Cases using LlamaIndex Text2Cypher + Neo4j.

자연어 질문을 LlamaIndex의 Text2CypherRetriever가 Cypher로 변환하여 실행.
PropertyGraphStore 대신 Text2CypherRetriever를 사용하여 배열 속성 문제 우회.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# SSL 경고 비활성화 (WSL 환경)
import urllib3
import httpx
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# httpx SSL 검증 비활성화 패치
_original_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

_original_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init

from neo4j import GraphDatabase
from llama_index.llms.openrouter import OpenRouter
from llama_index.core import Settings

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
TEST_DATASET = BASE_DIR / "logs" / "phase-3" / "cq_test_dataset_100_v4.json"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Neo4j 스키마 정보 (Phase-2 + Phase-3)
# Note: n10s applyNeo4jNaming converts camelCase to UPPERCASE (no underscores)
SCHEMA_INFO = """
Node Labels:
- Tdoc: Base class for all technical documents
  - CR: Change Request (subclass of Tdoc) - 변경 요청
  - LS: Liaison Statement (subclass of Tdoc) - 연락문서
- Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup
- Resolution: Base class for decisions (with subtypes: Agreement, Conclusion, WorkingAssumption)
- Summary, SessionNotes

IMPORTANT - Class Hierarchy:
- CR and LS are SUBCLASSES of Tdoc
- When querying for CR/LS in Resolution references, use the label directly:
  - Resolution-[:REFERENCES]->CR (3,033 relationships)
  - Resolution-[:REFERENCES]->LS (2,266 relationships)

Relationships:
# Phase-2 관계 (Note: ALL UPPERCASE, NO UNDERSCORES - this is how n10s stores them)
- (Tdoc)-[:PRESENTEDAT]->(Meeting)
- (Tdoc)-[:SUBMITTEDBY]->(Company)
- (Tdoc)-[:HASCONTACT]->(Contact)
- (Tdoc)-[:BELONGSTO]->(AgendaItem)
- (CR)-[:MODIFIES]->(Spec)  # CR이 어떤 Spec을 변경하는지
- (LS)-[:SENTTO]->(WorkingGroup)
- (LS)-[:ORIGINATEDFROM]->(WorkingGroup)
- (LS)-[:REPLYTO]->(Tdoc)

# Phase-3 관계 (Resolution)
- (Resolution)-[:MADE_AT]->(Meeting)
- (Resolution)-[:RESOLUTION_BELONGS_TO]->(AgendaItem)
- (Resolution)-[:REFERENCES]->(Tdoc)  # Tdoc, CR, LS 모두 포함!

# Phase-3 관계 (Role)
- (Summary)-[:MODERATED_BY]->(Company)
- (Summary)-[:PRESENTED_AT]->(Meeting)
- (SessionNotes)-[:CHAIRED_BY]->(Company)
- (SessionNotes)-[:PRESENTED_AT]->(Meeting)

Key Properties:
- Tdoc: tdocNumber (array), title, type, status, for
- CR: tdocNumber (array), crNumber, title, crCategory (F=Fix/A=Addition/B=Backward/D=Deletion), status
- LS: tdocNumber (array), title, direction (in=수신/out=발신)
- Company: companyName (array), aliases (array)
- Meeting: meetingNumber (STRING, e.g., 'RAN1#112', NOT array!)
- Spec: specNumber (STRING, e.g., '38.211')
- Resolution: resolutionId, content, hasFFS, hasTBD
- Agreement: resolutionId, content, hasFFS, hasTBD
- Conclusion: resolutionId, content, hasConsensus
- WorkingAssumption: resolutionId, content, hasFFS, hasTBD
- Summary: tdocNumber (array), summaryType, roundNumber
- SessionNotes: tdocNumber (array)
- AgendaItem: agendaNumber, meetingNumber
- WorkingGroup: wgName (STRING, e.g., 'RAN4', 'SA2', NOT 'name'!)

CRITICAL Property Type Notes:
1. meetingNumber is a STRING, NOT an array! Use: m.meetingNumber = 'RAN1#112'
2. tdocNumber, companyName, aliases are arrays. Use: 'value' IN t.tdocNumber
3. For e-meeting suffix matching: m.meetingNumber STARTS WITH 'RAN1#100' matches both 'RAN1#100' and 'RAN1#100-e'

IMPORTANT - Company Search Pattern:
- To find documents submitted by a company, use [:SUBMITTEDBY] relationship:
  MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE 'Huawei' IN c.companyName
- NEVER search company name in Tdoc properties directly (t.title, t.tdocNumber 등에 회사명 없음!)
- Company names in DB: Huawei, Ericsson, Samsung, Qualcomm, ZTE, Nokia, LG Electronics, Intel, MediaTek, Apple, etc.

IMPORTANT - Language Rule:
- ALL data in DB is in ENGLISH. NEVER use Korean keywords in queries!
- Wrong: r.content CONTAINS '정확도' (Korean)
- Correct: r.content CONTAINS 'accuracy' (English)

IMPORTANT - FFS/TBD Search:
- For open issues, check BOTH hasFFS and hasTBD: (r.hasFFS = true OR r.hasTBD = true)
- hasFFS = true means "For Further Study" items exist
- hasTBD = true means "To Be Determined" items exist

IMPORTANT - CR Status:
- CR.status values are from 3GPP system (not 'approved')
- To find CR-related agreements, use Resolution-[:REFERENCES]->CR pattern
- Don't filter by cr.status = 'approved', use Agreement instead
"""

# Few-shot Cypher 예시 (복잡한 쿼리 패턴)
CYPHER_EXAMPLES = """
=== FEW-SHOT EXAMPLES ===

Example 1: 특정 회의의 Agreement 조회
Q: RAN1#112 회의에서 합의된 Agreement 목록은?
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WHERE m.meetingNumber = 'RAN1#112' OR m.meetingNumber STARTS WITH 'RAN1#112-'
RETURN a.resolutionId, a.content

Example 2: 회사별 Summary 수 집계 (Top N)
Q: FL Summary를 가장 많이 작성한 회사 Top 5는?
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
WITH c, COUNT(s) AS summaryCount
ORDER BY summaryCount DESC
LIMIT 5
RETURN c.companyName AS company, summaryCount

Example 3: 회의 범위 조회 (RAN1#100~110)
Q: RAN1#100부터 RAN1#110까지 회의별 Resolution 수는?
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WHERE m.meetingNumber IN ['RAN1#100', 'RAN1#100-e', 'RAN1#101-e', 'RAN1#102-e', 'RAN1#103-e',
        'RAN1#104-e', 'RAN1#105-e', 'RAN1#106-e', 'RAN1#107-e', 'RAN1#108-e', 'RAN1#109-e', 'RAN1#110']
    OR m.meetingNumber STARTS WITH 'RAN1#100b' OR m.meetingNumber STARTS WITH 'RAN1#104b'
    OR m.meetingNumber STARTS WITH 'RAN1#106b' OR m.meetingNumber STARTS WITH 'RAN1#107b' OR m.meetingNumber STARTS WITH 'RAN1#110b'
WITH m, count(r) AS resolutionCount
RETURN m.meetingNumber AS meeting, resolutionCount
ORDER BY meeting

Example 4: Resolution 유형별 분포 (레이블 기반)
Q: 전체 Resolution 유형별(Agreement/Conclusion/WA) 분포는?
MATCH (r:Resolution)
RETURN
  CASE
    WHEN r:Agreement THEN 'Agreement'
    WHEN r:Conclusion THEN 'Conclusion'
    WHEN r:WorkingAssumption THEN 'WorkingAssumption'
  END AS type,
  count(*) AS count
ORDER BY count DESC

Example 5: 두 회사 비교
Q: Huawei와 Ericsson의 FL Summary 작성 횟수 비교는?
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
WHERE 'Huawei' IN c.companyName OR 'Huawei' IN c.aliases
WITH count(s) AS huaweiCount
MATCH (s2:Summary)-[:MODERATED_BY]->(c2:Company)
WHERE 'Ericsson' IN c2.companyName OR 'Ericsson' IN c2.aliases
RETURN huaweiCount AS Huawei, count(s2) AS Ericsson

Example 6: 키워드 검색 (content 포함)
Q: 'MIMO' 관련 Resolution 목록은?
MATCH (r:Resolution)
WHERE r.content CONTAINS 'MIMO'
RETURN r.resolutionId, r.content
LIMIT 50

Example 7: 회의당 평균/최대/최소 Resolution 수
Q: 회의당 평균 Resolution 수는?
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WITH m, count(r) AS resCount
RETURN avg(resCount) AS average, max(resCount) AS maximum, min(resCount) AS minimum

Example 8: Resolution이 가장 많은/적은 회의
Q: Resolution이 가장 많았던 회의는?
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WITH m, count(r) AS resCount
ORDER BY resCount DESC
LIMIT 1
RETURN m.meetingNumber AS meeting, resCount

Example 9: 특정 회사가 Moderator로 작성한 Summary
Q: Huawei가 Moderator로 작성한 FL Summary 목록은?
MATCH (s:Summary)-[:MODERATED_BY]->(c:Company)
WHERE 'Huawei' IN c.companyName OR 'Huawei' IN c.aliases
RETURN s.tdocNumber AS tdocNumber, s.summaryType AS type
LIMIT 100

Example 10: SessionNotes와 Chair 회사
Q: RAN1#112 회의의 Ad-hoc Session을 주관한 회사는?
MATCH (s:SessionNotes)-[:PRESENTED_AT]->(m:Meeting)
WHERE m.meetingNumber = 'RAN1#112' OR m.meetingNumber STARTS WITH 'RAN1#112-'
MATCH (s)-[:CHAIRED_BY]->(c:Company)
RETURN DISTINCT c.companyName AS company

Example 11: 특정 Agenda의 Resolution
Q: RAN1#112 회의 Agenda 8.1 관련 Resolution은?
MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem)
WHERE ai.agendaNumber STARTS WITH '8.1' AND ai.meetingNumber = '112'
RETURN r.resolutionId, ai.agendaNumber, r.content

Example 12: FFS/TBD 포함 Resolution
Q: FFS가 포함된 Agreement는?
MATCH (r:Agreement)
WHERE r.hasFFS = true
RETURN r.resolutionId, r.content
LIMIT 20

Example 13: CR(Change Request) 관련 Resolution 조회
Q: CR과 관련된 Resolution 목록은?
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)
RETURN r.resolutionId, r.content, cr.tdocNumber
LIMIT 50

Example 14: 특정 키워드 CR의 Resolution
Q: MIMO 관련 CR에 대한 Resolution은?
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)
WHERE cr.title CONTAINS 'MIMO' OR ANY(t IN cr.tdocNumber WHERE t CONTAINS 'MIMO')
RETURN r.resolutionId, r.content, cr.title

Example 15: LS(Liaison Statement) 관련 Resolution 조회
Q: LS와 관련된 Resolution은?
MATCH (r:Resolution)-[:REFERENCES]->(ls:LS)
RETURN r.resolutionId, r.content, ls.tdocNumber
LIMIT 50

Example 16: Spec 변경 관련 Resolution (CR 경유)
Q: 38.211 스펙 변경 관련 Resolution은?
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(s:Spec)
WHERE s.specNumber = '38.211'
RETURN r.resolutionId, r.content, cr.title, s.specNumber

Example 17: 특정 회의의 CR 관련 Agreement
Q: RAN1#112 회의에서 CR과 관련된 Agreement는?
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WHERE m.meetingNumber = 'RAN1#112' OR m.meetingNumber STARTS WITH 'RAN1#112-'
MATCH (a)-[:REFERENCES]->(cr:CR)
RETURN a.resolutionId, a.content, cr.title

Example 18: LS 응답 관련 Resolution
Q: LS 응답(reply)과 관련된 Resolution은?
MATCH (r:Resolution)-[:REFERENCES]->(ls:LS)
WHERE ls.direction = 'out' OR EXISTS((ls)-[:REPLYTO]->())
RETURN r.resolutionId, r.content, ls.tdocNumber

Example 19: 회의별 CR 관련 Resolution 통계
Q: 회의별로 CR 관련 Resolution이 몇 개인가?
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
MATCH (r)-[:REFERENCES]->(cr:CR)
WITH m.meetingNumber AS meeting, count(r) AS crResolutionCount
RETURN meeting, crResolutionCount
ORDER BY crResolutionCount DESC
LIMIT 10

Example 20: CR 카테고리별 Resolution (Fix/Addition)
Q: Fix(F) 카테고리 CR 관련 Resolution은?
MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)
WHERE cr.crCategory = 'F'
RETURN r.resolutionId, r.content, cr.title, cr.crCategory
LIMIT 50

Example 21: LS 방향별 Resolution (수신/발신)
Q: 발신(out) LS 관련 Resolution은?
MATCH (r:Resolution)-[:REFERENCES]->(ls:LS)
WHERE ls.direction = 'out'
RETURN r.resolutionId, r.content, ls.tdocNumber, ls.direction
LIMIT 50

Example 22: 회의 + 키워드 복합 조건 (CRITICAL: AND 사용!)
Q: RAN1#100 회의에서 positioning 관련 결정사항은?
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WHERE (m.meetingNumber = 'RAN1#100' OR m.meetingNumber STARTS WITH 'RAN1#100-')
AND r.content CONTAINS 'positioning'
RETURN r.resolutionId, r.content
LIMIT 50

Example 23: e-meeting + 키워드 복합 조건 (CRITICAL: 두 번째 WHERE 쓰지 말 것!)
Q: RAN1#101-e 회의에서 NTN 관련 합의는?
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WHERE (m.meetingNumber = 'RAN1#101-e' OR m.meetingNumber STARTS WITH 'RAN1#101-e-')
AND a.content CONTAINS 'NTN'
RETURN a.resolutionId, a.content
LIMIT 50

Example 24: LS endorsed 검색 (content 기반 - LS에 status 속성 없음)
Q: draft LS가 endorsed된 합의는?
MATCH (a:Agreement)
WHERE a.content CONTAINS 'LS' AND a.content CONTAINS 'endorsed'
RETURN a.resolutionId, a.content
LIMIT 50

Example 25: 회사가 제출한 기고서 관련 결정 (SUBMITTEDBY 관계 사용!)
Q: Qualcomm이 제출한 기고서 관련 결정은?
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTEDBY]->(c:Company)
WHERE 'Qualcomm' IN c.companyName OR 'Qualcomm' IN c.aliases
RETURN r.resolutionId, r.content, t.tdocNumber, t.title
LIMIT 50

Example 26: 회사별 기고서 합의 (ZTE, LG Electronics 등)
Q: ZTE가 제출한 기고서 관련 합의는?
MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTEDBY]->(c:Company)
WHERE 'ZTE' IN c.companyName OR 'ZTE' IN c.aliases OR 'ZTE Corporation' IN c.companyName
RETURN a.resolutionId, a.content, t.tdocNumber
LIMIT 50

Example 27: FFS 또는 TBD 미결 이슈 (복합 조건)
Q: RedCap 관련 미결 이슈는?
MATCH (r:Resolution)
WHERE r.content CONTAINS 'RedCap' AND (r.hasFFS = true OR r.hasTBD = true)
RETURN r.resolutionId, r.content
LIMIT 50

Example 28: 회의 + 회사 복합 검색 (SUBMITTEDBY 사용!)
Q: RAN1#120 회의에서 Huawei 기고서 관련 결정은?
MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting)
WHERE m.meetingNumber = 'RAN1#120' OR m.meetingNumber STARTS WITH 'RAN1#120-'
MATCH (r)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTEDBY]->(c:Company)
WHERE 'Huawei' IN c.companyName OR 'Huawei' IN c.aliases
RETURN r.resolutionId, r.content, t.tdocNumber
LIMIT 50

Example 29: CR 키워드 검색 (title CONTAINS 사용)
Q: PUCCH 관련 CR 합의는?
MATCH (a:Agreement)-[:REFERENCES]->(cr:CR)
WHERE cr.title CONTAINS 'PUCCH'
RETURN a.resolutionId, a.content, cr.title
LIMIT 50

Example 30: 회사 + 기술 키워드 복합 검색
Q: Samsung이 제출한 MIMO 관련 기고서 결정은?
MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTEDBY]->(c:Company)
WHERE ('Samsung' IN c.companyName OR 'Samsung' IN c.aliases)
AND t.title CONTAINS 'MIMO'
RETURN r.resolutionId, r.content, t.tdocNumber, t.title
LIMIT 50

=== CRITICAL NOTES ===
1. NEVER use array indexing like property[0] on array properties - it causes TypeError
2. Return the full array: c.companyName (not c.companyName[0])
3. For meeting range queries, use explicit list with ANY()
4. For type distribution, use CASE WHEN with labels
5. Company matching: 'CompanyName' IN c.companyName OR 'CompanyName' IN c.aliases
6. IMPORTANT: meetingNumber is a STRING, not an array! Use m.meetingNumber = 'RAN1#112' NOT 'RAN1#112' IN m.meetingNumber
7. For e-meeting matching: m.meetingNumber STARTS WITH 'RAN1#100' to match both 'RAN1#100' and 'RAN1#100-e'
8. CR and LS are subclasses of Tdoc - query them directly with :CR or :LS labels
9. To find Spec-related Resolutions, go through CR: (Resolution)-[:REFERENCES]->(CR)-[:MODIFIES]->(Spec)
10. CR category property is 'crCategory' (NOT 'cat'): values are F, A, B, D
11. LS direction property is 'direction' (NOT 'lsType'): values are 'in', 'out' (lowercase)
12. CRITICAL: NEVER use multiple WHERE clauses! Use AND to combine conditions:
    WRONG:  WHERE condition1 WHERE condition2 (Syntax Error!)
    CORRECT: WHERE condition1 AND condition2
13. CRITICAL: To find company-submitted documents, ALWAYS use [:SUBMITTEDBY] relationship!
    WRONG:  WHERE 'Qualcomm' IN t.title (company name is NOT in title!)
    CORRECT: (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE 'Qualcomm' IN c.companyName
14. CRITICAL: ALL keywords must be in ENGLISH! Database content is in English only.
    WRONG:  r.content CONTAINS '정확도' (Korean won't match!)
    CORRECT: r.content CONTAINS 'accuracy' (English)
15. For open issues (FFS/TBD), use OR condition: (r.hasFFS = true OR r.hasTBD = true)
16. Don't use cr.status = 'approved'. To find approved CRs, use Agreement-[:REFERENCES]->CR pattern.

=== END EXAMPLES ===
"""


def setup_llm():
    """Setup LLM via OpenRouter."""
    llm = OpenRouter(
        api_key=OPENROUTER_API_KEY,
        model="google/gemini-2.0-flash-001",
        temperature=0.0,
    )
    Settings.llm = llm
    return llm


def generate_cypher(llm, question: str) -> str:
    """Generate Cypher query from natural language question."""
    prompt = f"""You are a Neo4j Cypher expert. Convert the following natural language question to a Cypher query.

Schema Information:
{SCHEMA_INFO}

{CYPHER_EXAMPLES}

Important notes:
1. Some properties are stored as arrays (tdocNumber, companyName, aliases). Use 'value IN property' syntax for matching.
   Example: MATCH (t:Tdoc) WHERE 'R1-2302051' IN t.tdocNumber
2. CRITICAL: meetingNumber is a STRING, not an array!
   Correct: MATCH (m:Meeting) WHERE m.meetingNumber = 'RAN1#112'
   Wrong: MATCH (m:Meeting) WHERE 'RAN1#112' IN m.meetingNumber
3. For e-meeting suffix matching (COVID-era meetings have -e suffix):
   Use: m.meetingNumber = 'RAN1#100' OR m.meetingNumber STARTS WITH 'RAN1#100-'
4. Company names are in companyName array.
   Example: MATCH (c:Company) WHERE 'Huawei' IN c.companyName OR 'Huawei' IN c.aliases
5. For Resolution type distribution, use CASE WHEN r:Agreement THEN 'Agreement' pattern
6. CR and LS are subclasses of Tdoc - use :CR or :LS labels directly
   Example: MATCH (r:Resolution)-[:REFERENCES]->(cr:CR) for CR-related resolutions
7. For Spec-related queries, go through CR: (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(s:Spec)

Question: {question}

Return ONLY the Cypher query, no explanation. The query should return useful information to answer the question.
"""

    response = llm.complete(prompt)
    cypher = str(response).strip()

    # Clean up response (remove markdown code blocks if present)
    if cypher.startswith("```"):
        lines = cypher.split("\n")
        cypher = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return cypher.strip()


def serialize_value(value):
    """Serialize Neo4j values to JSON-compatible format."""
    from neo4j.graph import Node, Relationship, Path

    if isinstance(value, Node):
        # Convert Node to dict with labels and properties
        return {
            "labels": list(value.labels),
            "properties": dict(value)
        }
    elif isinstance(value, Relationship):
        return {
            "type": value.type,
            "properties": dict(value)
        }
    elif isinstance(value, Path):
        return {
            "nodes": [serialize_value(n) for n in value.nodes],
            "relationships": [serialize_value(r) for r in value.relationships]
        }
    elif isinstance(value, list):
        return [serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    else:
        return value


def execute_cypher(driver, cypher: str) -> dict:
    """Execute Cypher query and return results."""
    try:
        with driver.session() as session:
            result = session.run(cypher)
            records = []
            for record in result:
                serialized = {}
                for key, value in record.items():
                    serialized[key] = serialize_value(value)
                records.append(serialized)
            return {
                "success": True,
                "records": records,
                "count": len(records)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "records": []
        }


def generate_answer(llm, question: str, cypher: str, result: dict) -> str:
    """Generate natural language answer from query results."""
    if not result["success"]:
        return f"Query failed: {result['error']}"

    if not result["records"]:
        return "No results found for this query."

    # Limit records for context
    records_str = json.dumps(result["records"][:10], ensure_ascii=False, indent=2)

    prompt = f"""Based on the following Neo4j query results, provide a concise answer to the question.

Question: {question}

Cypher Query: {cypher}

Query Results ({result['count']} total records, showing first 10):
{records_str}

Provide a direct, concise answer in Korean. Include specific numbers and examples from the results.
"""

    response = llm.complete(prompt)
    return str(response).strip()


def validate_test_case(llm, driver, tc: dict) -> dict:
    """Validate a single test case using Text2Cypher approach."""
    question = tc["question"]

    # Step 1: Generate Cypher
    try:
        cypher = generate_cypher(llm, question)
    except Exception as e:
        return {
            "test_case_id": tc["id"],
            "cq_type": tc["cq_type"],
            "question": question,
            "status": "FAIL",
            "error": f"Cypher generation failed: {str(e)}",
            "cypher": None,
            "response": None
        }

    # Step 2: Execute Cypher
    result = execute_cypher(driver, cypher)

    # Step 3: Generate Answer
    if result["success"] and result["records"]:
        try:
            answer = generate_answer(llm, question, cypher, result)
            status = "PASS"
        except Exception as e:
            answer = f"Answer generation failed: {str(e)}"
            status = "PARTIAL"  # Query worked but answer failed
    elif result["success"]:
        answer = "No results found"
        status = "NO_DATA"  # Query worked but returned 0 results
    else:
        answer = result["error"]
        status = "FAIL"

    return {
        "test_case_id": tc["id"],
        "cq_type": tc["cq_type"],
        "question": question,
        "status": status,
        "cypher": cypher,
        "result_count": result.get("count", 0),
        "response": answer,
        "error": result.get("error")
    }


def main():
    print("=" * 70)
    print("CQ VALIDATION WITH LLAMAINDEX TEXT2CYPHER + NEO4J")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")

    # Setup
    print("\n[1/4] Setting up LLM (OpenRouter + Gemini)...")
    llm = setup_llm()

    print("\n[2/4] Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # Verify connection
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"  Connected! Total nodes: {count:,}")

    # Load test cases
    print("\n[3/4] Loading test dataset...")
    with open(TEST_DATASET) as f:
        test_data = json.load(f)

    test_cases = test_data["test_cases"]
    print(f"  - Total test cases: {len(test_cases)}")
    print(f"  - Testing ALL 100 test cases")

    # Execute queries
    print("\n[4/4] Executing Text2Cypher validation...")
    print("=" * 70)

    results = []
    passed = 0
    failed = 0
    partial = 0
    no_data = 0

    for i, tc in enumerate(test_cases):
        print(f"\n[{i+1}/100] {tc['id']} - {tc['cq_type']}")
        print(f"  Q: {tc['question'][:60]}...")

        result = validate_test_case(llm, driver, tc)
        results.append(result)

        if result["status"] == "PASS":
            passed += 1
            cypher = result.get('cypher') or ''
            print(f"  ✓ Cypher: {cypher[:50]}..." if cypher else "  ✓ No Cypher")
            print(f"  ✓ Results: {result.get('result_count', 0)} records")
            response = result.get("response") or ''
            if response:
                print(f"  A: {response[:80]}...")
        elif result["status"] == "PARTIAL":
            partial += 1
            error = result.get('error') or 'Unknown'
            print(f"  ~ Partial: {error[:50]}")
        elif result["status"] == "NO_DATA":
            no_data += 1
            cypher = result.get('cypher') or ''
            print(f"  ○ No Data: Query OK but 0 results")
            print(f"    Cypher: {cypher[:50]}..." if cypher else "    No Cypher")
        else:
            failed += 1
            error = result.get('error') or 'Unknown'
            print(f"  ✗ Error: {error[:50]}")

    driver.close()

    # Save results
    total = len(results)
    output = {
        "generated_at": datetime.now().isoformat(),
        "method": "LlamaIndex Text2Cypher + Neo4j",
        "llm": "google/gemini-2.0-flash-001",
        "neo4j_uri": NEO4J_URI,
        "metrics": {
            "total_tests": total,
            "passed": passed,
            "partial": partial,
            "no_data": no_data,
            "failed": failed,
            "pass_rate": round(100 * passed / total, 1) if total else 0,
            "success_rate": round(100 * (passed + partial) / total, 1) if total else 0,
            "query_success_rate": round(100 * (passed + partial + no_data) / total, 1) if total else 0
        },
        "results": results
    }

    output_file = OUTPUT_DIR / "cq_llamaindex_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total CQ Types Tested: {total}")
    print(f"  ✓ Passed: {passed} ({round(100 * passed / total, 1)}%)")
    print(f"  ~ Partial: {partial} ({round(100 * partial / total, 1)}%)")
    print(f"  ○ No Data: {no_data} ({round(100 * no_data / total, 1)}%)")
    print(f"  ✗ Failed: {failed} ({round(100 * failed / total, 1)}%)")
    print(f"  Success Rate (Pass + Partial): {round(100 * (passed + partial) / total, 1)}%")
    print(f"  Query Success Rate (excl. Failed): {round(100 * (passed + partial + no_data) / total, 1)}%")
    print(f"\n  Results saved to: {output_file}")


if __name__ == "__main__":
    main()
