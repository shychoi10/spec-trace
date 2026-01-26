#!/usr/bin/env python3
"""
Load Phase-3 Role data (Summary, SessionNotes) into Neo4j using direct Cypher.

Creates/Updates nodes:
- Summary (extending Tdoc)
- SessionNotes (extending Tdoc)

Creates relationships:
- MODERATED_BY (Summary -> Company)
- CHAIRED_BY (SessionNotes -> Company)
"""

import json
from pathlib import Path
from neo4j import GraphDatabase
import os


# Paths
INSTANCES_DIR = Path(__file__).parent.parent.parent.parent / "ontology" / "output" / "instances" / "phase-3"

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


def load_jsonld(filename: str) -> list[dict]:
    """Load instances from JSON-LD file."""
    path = INSTANCES_DIR / filename
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("@graph", [])


def parse_meeting_uri(uri: str) -> str:
    """Parse meeting URI to get meeting number."""
    # "tdoc:meeting/RAN1-112" -> "112"
    return uri.replace("tdoc:meeting/RAN1-", "")


def parse_company_uri(uri: str) -> str:
    """Parse company URI to get company name."""
    # "tdoc:company/Huawei" -> "Huawei"
    return uri.replace("tdoc:company/", "").replace("_", " ")


def create_summary_nodes(tx, summaries: list[dict]):
    """Create or update Summary nodes (which are also Tdocs)."""
    # DB format: tdocNumber = ['R1-2000138'] (array)
    # Match existing Tdoc nodes and add Summary label
    for s in summaries:
        tx.run("""
            MATCH (t:Tdoc) WHERE $tdocNumber IN t.tdocNumber
            SET t:Summary,
                t.summaryType = $summaryType,
                t.roundNumber = $roundNumber
        """,
            tdocNumber=s["tdocNumber"],
            summaryType=s.get("summaryType"),
            roundNumber=s.get("roundNumber")
        )

    # For summaries without existing Tdoc node, create new
    tx.run("""
        UNWIND $summaries AS s
        MERGE (sum:Tdoc:Summary {tdocNumber: [s.tdocNumber]})
        ON CREATE SET sum.title = s.title,
            sum.summaryType = s.summaryType,
            sum.roundNumber = s.roundNumber
    """, summaries=[
        {
            "tdocNumber": s["tdocNumber"],
            "title": s["title"],
            "summaryType": s.get("summaryType"),
            "roundNumber": s.get("roundNumber"),
        }
        for s in summaries
    ])


def create_session_notes_nodes(tx, session_notes: list[dict]):
    """Create or update SessionNotes nodes (which are also Tdocs)."""
    # DB format: tdocNumber = ['R1-2000138'] (array)
    # Match existing Tdoc nodes and add SessionNotes label
    for n in session_notes:
        tx.run("""
            MATCH (t:Tdoc) WHERE $tdocNumber IN t.tdocNumber
            SET t:SessionNotes
        """, tdocNumber=n["tdocNumber"])

    # For session notes without existing Tdoc node, create new
    tx.run("""
        UNWIND $notes AS n
        MERGE (sn:Tdoc:SessionNotes {tdocNumber: [n.tdocNumber]})
        ON CREATE SET sn.title = n.title
    """, notes=[
        {
            "tdocNumber": n["tdocNumber"],
            "title": n["title"],
        }
        for n in session_notes
    ])


def create_summary_relationships(tx, summaries: list[dict]):
    """Create relationships for Summary nodes."""
    for s in summaries:
        # MODERATED_BY relationship
        # DB format: companyName = ['Huawei'] (array), tdocNumber = ['R1-xxx'] (array)
        if "moderatedBy" in s:
            company_name = parse_company_uri(s["moderatedBy"])
            tx.run("""
                MATCH (sum:Summary) WHERE $tdocNumber IN sum.tdocNumber
                MATCH (c:Company) WHERE $companyName IN c.companyName OR $companyName IN c.aliases
                MERGE (sum)-[:MODERATED_BY]->(c)
            """, tdocNumber=s["tdocNumber"], companyName=company_name)

        # Link to meeting
        # DB format: meetingNumber = ['RAN1#100'] or ['RAN1#100-e'] (array, -e suffix for e-meetings)
        # JSON-LD format: meeting = 'tdoc:meeting/RAN1-100'
        # Fix: Use STARTS WITH to handle -e suffix mismatch
        if "meeting" in s:
            # Convert "tdoc:meeting/RAN1-100" -> "RAN1#100"
            meeting_num = s["meeting"].replace("tdoc:meeting/", "").replace("-", "#")
            tx.run("""
                MATCH (sum:Summary) WHERE $tdocNumber IN sum.tdocNumber
                MATCH (m:Meeting) WHERE ANY(num IN m.meetingNumber WHERE num = $meetingNum OR num STARTS WITH $meetingNum + '-')
                MERGE (sum)-[:PRESENTED_AT]->(m)
            """, tdocNumber=s["tdocNumber"], meetingNum=meeting_num)


def create_session_notes_relationships(tx, session_notes: list[dict]):
    """Create relationships for SessionNotes nodes."""
    for n in session_notes:
        # CHAIRED_BY relationship
        # DB format: companyName = ['CMCC'] (array), tdocNumber = ['R1-xxx'] (array)
        if "chairedBy" in n:
            company_name = parse_company_uri(n["chairedBy"])
            tx.run("""
                MATCH (sn:SessionNotes) WHERE $tdocNumber IN sn.tdocNumber
                MATCH (c:Company) WHERE $companyName IN c.companyName OR $companyName IN c.aliases
                MERGE (sn)-[:CHAIRED_BY]->(c)
            """, tdocNumber=n["tdocNumber"], companyName=company_name)

        # Link to meeting
        # DB format: meetingNumber = ['RAN1#100'] or ['RAN1#100-e'] (array, -e suffix for e-meetings)
        # JSON-LD format: meeting = 'tdoc:meeting/RAN1-100'
        # Fix: Use STARTS WITH to handle -e suffix mismatch
        if "meeting" in n:
            # Convert "tdoc:meeting/RAN1-100" -> "RAN1#100"
            meeting_num = n["meeting"].replace("tdoc:meeting/", "").replace("-", "#")
            tx.run("""
                MATCH (sn:SessionNotes) WHERE $tdocNumber IN sn.tdocNumber
                MATCH (m:Meeting) WHERE ANY(num IN m.meetingNumber WHERE num = $meetingNum OR num STARTS WITH $meetingNum + '-')
                MERGE (sn)-[:PRESENTED_AT]->(m)
            """, tdocNumber=n["tdocNumber"], meetingNum=meeting_num)


def main():
    """Main function to load all role data into Neo4j."""
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # Load Summaries
            print("\nLoading Summaries...")
            summaries = load_jsonld("summaries.jsonld")
            print(f"  Loaded {len(summaries)} summaries from JSON-LD")

            session.execute_write(create_summary_nodes, summaries)
            print("  Created/updated Summary nodes")

            session.execute_write(create_summary_relationships, summaries)
            print("  Created relationships")

            # Load Session Notes
            print("\nLoading Session Notes...")
            session_notes = load_jsonld("session_notes.jsonld")
            print(f"  Loaded {len(session_notes)} session notes from JSON-LD")

            session.execute_write(create_session_notes_nodes, session_notes)
            print("  Created/updated SessionNotes nodes")

            session.execute_write(create_session_notes_relationships, session_notes)
            print("  Created relationships")

            # Summary
            result = session.run("""
                MATCH (s:Summary) RETURN 'Summary' AS type, count(s) AS count
                UNION ALL
                MATCH (sn:SessionNotes) RETURN 'SessionNotes' AS type, count(sn) AS count
            """)

            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            for record in result:
                print(f"  {record['type']}: {record['count']}")

            # Count relationships
            result = session.run("""
                MATCH ()-[r:MODERATED_BY]->() RETURN 'MODERATED_BY' AS type, count(r) AS count
                UNION ALL
                MATCH ()-[r:CHAIRED_BY]->() RETURN 'CHAIRED_BY' AS type, count(r) AS count
            """)

            print("\nRelationships:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")

    finally:
        driver.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
