"""
Step-3 Sub-step 3-3: Text-to-Cypher 구현
자연어 질문을 Cypher 쿼리로 변환하여 Neo4j에서 실행
"""

import config  # SSL 패치 적용
from graph_store import get_llm, get_neo4j_driver


# Cypher 생성 프롬프트 템플릿
CYPHER_GENERATION_PROMPT = """You are a Neo4j Cypher expert. Convert the user's natural language question into a Cypher query.

## Neo4j Schema

### Node Labels and Properties:
- Tdoc: tdocNumber (unique ID like "R1-2401234"), title, type (e.g., "discussion", "CR", "draftCR", "LS in", "LS out"), status (e.g., "approved", "agreed", "noted", "revised", "withdrawn", "not treated", "postponed"), for (e.g., "Decision", "Approval", "Information")
- CR (Change Request): tdocNumber, title, type="CR" or "draftCR"
- LS (Liaison Statement): tdocNumber, title, type (values: "LS in", "LS out"), direction (values: "in", "out")
- Meeting: meetingNumber (e.g., "RAN1#120"), meetingId
- Company: companyName, aliases (array)
- Contact: contactName
- WorkItem: workItemCode (e.g., "TEI16", "NB_IOTenh3-Core", "NR_unlic-Core")
- AgendaItem: agendaNumber (e.g., "7.1.2", "8.1"), agendaDescription
- Release: releaseName (e.g., "Rel-18", "Rel-19")
- Spec: specNumber (e.g., "38.211", "38.213", "38.214")
- WorkingGroup: wgName (e.g., "RAN1", "RAN2", "SA2")

### Relationships:
- (Tdoc)-[:PRESENTED_AT]->(Meeting)
- (Tdoc)-[:SUBMITTED_BY]->(Company)
- (Tdoc)-[:HAS_CONTACT]->(Contact)
- (Tdoc)-[:BELONGS_TO]->(AgendaItem)
- (Tdoc)-[:RELATED_TO]->(WorkItem)
- (Tdoc)-[:TARGET_RELEASE]->(Release)
- (Tdoc)-[:IS_REVISION_OF]->(Tdoc)  # Points to previous version
- (Tdoc)-[:REVISED_TO]->(Tdoc)      # Points to next version
- (CR)-[:MODIFIES]->(Spec)
- (LS)-[:SENT_TO]->(WorkingGroup)
- (LS)-[:CC_TO]->(WorkingGroup)
- (LS)-[:ORIGINATED_FROM]->(WorkingGroup)
- (LS)-[:REPLY_TO]->(Tdoc)
- (Contact)-[:WORKS_FOR]->(Company)

### Important Notes:
- Tdoc numbers follow pattern: R1-YYMNNNN (e.g., R1-2401234 = meeting 124, document 01234)
- CR and LS are subtypes of Tdoc (they have tdocNumber property too)
- Use OPTIONAL MATCH for relationships that might not exist
- Return meaningful results, not just counts unless asked

## Question
{question}

## Instructions
1. Generate ONLY the Cypher query, no explanations
2. Use proper Neo4j 5.x syntax
3. Handle potential null values with COALESCE when needed
4. Limit results to 25 unless user specifies otherwise
5. Order results meaningfully when possible
6. IMPORTANT: Never return raw nodes (e.g., RETURN t), always return specific properties (e.g., RETURN t.tdocNumber, t.title)
7. CRITICAL: Relationship directions are FIXED. Never reverse them!
   - "Company가 제출한 Tdoc" → (Tdoc)-[:SUBMITTED_BY]->(Company) (Tdoc이 주어)
   - "Tdoc이 제출된 Meeting" → (Tdoc)-[:PRESENTED_AT]->(Meeting) (Tdoc이 주어)
   - Always start from Tdoc and follow arrows to the right (->)

## Cypher Query:
"""


def generate_cypher(question: str) -> str:
    """자연어 질문을 Cypher 쿼리로 변환"""
    llm = get_llm()
    prompt = CYPHER_GENERATION_PROMPT.format(question=question)
    response = llm.complete(prompt)

    # 응답에서 Cypher 쿼리만 추출 (```cypher ... ``` 블록 처리)
    cypher = response.text.strip()
    if cypher.startswith("```"):
        lines = cypher.split("\n")
        cypher = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return cypher.strip()


def execute_cypher(cypher: str) -> list:
    """Cypher 쿼리 실행 및 결과 반환"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(cypher)
            return [dict(record) for record in result]
    finally:
        driver.close()


def query(question: str, verbose: bool = True) -> dict:
    """자연어 질문 → Cypher 생성 → 실행 → 결과 반환"""
    if verbose:
        print(f"\n📝 질문: {question}")
        print("-" * 60)

    # 1. Cypher 생성
    cypher = generate_cypher(question)
    if verbose:
        print(f"🔧 생성된 Cypher:\n{cypher}")
        print("-" * 60)

    # 2. 쿼리 실행
    try:
        results = execute_cypher(cypher)
        if verbose:
            print(f"✅ 결과: {len(results)}건")
            for i, row in enumerate(results[:5]):  # 처음 5개만 출력
                print(f"   {i+1}. {row}")
            if len(results) > 5:
                print(f"   ... ({len(results) - 5}건 더 있음)")

        return {
            "question": question,
            "cypher": cypher,
            "results": results,
            "count": len(results),
            "success": True,
        }
    except Exception as e:
        if verbose:
            print(f"❌ 쿼리 실행 오류: {e}")
        return {
            "question": question,
            "cypher": cypher,
            "error": str(e),
            "success": False,
        }


def interactive_mode():
    """대화형 질의 모드"""
    print("=" * 60)
    print("3GPP TDoc Knowledge Graph - Natural Language Query")
    print("=" * 60)
    print("질문을 입력하세요. 종료하려면 'exit' 또는 'quit' 입력")
    print()

    while True:
        try:
            question = input("질문> ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit", "q"):
                print("종료합니다.")
                break

            query(question, verbose=True)
            print()
        except KeyboardInterrupt:
            print("\n종료합니다.")
            break


if __name__ == "__main__":
    # 테스트 질문들
    test_questions = [
        "Samsung이 제출한 TDoc 수는?",
        "Meeting RAN1#120에서 가장 많이 문서를 제출한 회사 top 5",
        "Rel-18을 타겟으로 하는 CR 개수",
    ]

    print("=" * 60)
    print("Text-to-Cypher 테스트")
    print("=" * 60)

    for q in test_questions:
        result = query(q, verbose=True)
        print("\n")
