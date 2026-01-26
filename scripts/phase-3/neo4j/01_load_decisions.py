#!/usr/bin/env python3
"""
Load Phase-3 Resolution data into Neo4j using direct Cypher.

Spec: Uses "Resolution" terminology per Section 4.1.

Creates nodes:
- Agreement, Conclusion, WorkingAssumption (with Resolution label)

Creates relationships:
- RESOLUTION_BELONGS_TO (Resolution -> AgendaItem)
- MADE_AT (Resolution -> Meeting)
- REFERENCES (Resolution -> Tdoc)
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


def create_resolution_nodes(tx, resolutions: list[dict], resolution_type: str):
    """Create Resolution nodes (Agreement, Conclusion, or WorkingAssumption)."""
    query = f"""
    UNWIND $resolutions AS r
    MERGE (res:Resolution:{resolution_type} {{resolutionId: r.resolutionId}})
    SET res.content = r.content,
        res.hasFFS = COALESCE(r.hasFFS, false),
        res.hasTBD = COALESCE(r.hasTBD, false),
        res.sessionContext = r.sessionContext,
        res.note = r.note
    """

    if resolution_type == "Conclusion":
        query = f"""
        UNWIND $resolutions AS r
        MERGE (res:Resolution:{resolution_type} {{resolutionId: r.resolutionId}})
        SET res.content = r.content,
            res.hasConsensus = r.hasConsensus,
            res.sessionContext = r.sessionContext,
            res.note = r.note
        """

    tx.run(query, resolutions=resolutions)


def create_resolution_relationships(tx, resolutions: list[dict]):
    """Create relationships for resolutions."""
    # MADE_AT relationship (Resolution -> Meeting)
    # DB format: meetingNumber = 'RAN1#100' or 'RAN1#100-e' (string, -e suffix for e-meetings)
    # JSON-LD format: madeAt = 'tdoc:meeting/RAN1_100' (underscore)
    # Fix: Use STARTS WITH to handle -e suffix mismatch
    tx.run("""
        UNWIND $resolutions AS r
        MATCH (res:Resolution {resolutionId: r.resolutionId})
        MATCH (m:Meeting) WHERE m.meetingNumber = r.meetingNum OR m.meetingNumber STARTS WITH r.meetingNum + '-'
        MERGE (res)-[:MADE_AT]->(m)
    """, resolutions=[
        {
            "resolutionId": r["resolutionId"],
            # Convert "tdoc:meeting/RAN1_100" -> "RAN1#100" (underscore to hash)
            "meetingNum": r["madeAt"].replace("tdoc:meeting/", "").replace("_", "#")
        }
        for r in resolutions if "madeAt" in r
    ])

    # RESOLUTION_BELONGS_TO relationship (Resolution -> AgendaItem)
    for r in resolutions:
        if "resolutionBelongsTo" not in r:
            continue

        agenda_ref = r["resolutionBelongsTo"]
        # Parse "tdoc:agenda/112-8.1" -> meeting=112, agenda=8.1
        parts = agenda_ref.replace("tdoc:agenda/", "").split("-", 1)
        if len(parts) != 2:
            continue

        meeting_num, agenda_item = parts

        tx.run("""
            MATCH (res:Resolution {resolutionId: $resolutionId})
            MERGE (ai:AgendaItem {agendaNumber: $agendaItem, meetingNumber: $meetingNum})
            MERGE (res)-[:RESOLUTION_BELONGS_TO]->(ai)
        """, resolutionId=r["resolutionId"], agendaItem=agenda_item, meetingNum=meeting_num)


def create_references_relationships(tx, resolutions: list[dict]):
    """Create REFERENCES relationships (Resolution -> Tdoc)."""
    # DB format: tdocNumber = ['R1-2000138'] (array)
    for r in resolutions:
        refs = r.get("references", [])
        if isinstance(refs, str):
            refs = [refs]

        for ref in refs:
            tdoc_num = ref.replace("tdoc:", "")
            tx.run("""
                MATCH (res:Resolution {resolutionId: $resolutionId})
                MATCH (t:Tdoc) WHERE $tdocNum IN t.tdocNumber
                MERGE (res)-[:REFERENCES]->(t)
            """, resolutionId=r["resolutionId"], tdocNum=tdoc_num)


def create_indexes(tx):
    """Create indexes for Resolution nodes."""
    tx.run("CREATE INDEX IF NOT EXISTS FOR (r:Resolution) ON (r.resolutionId)")
    tx.run("CREATE INDEX IF NOT EXISTS FOR (ai:AgendaItem) ON (ai.agendaNumber, ai.meetingNumber)")


def main():
    """Main function to load all resolutions into Neo4j."""
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # Create indexes
            print("Creating indexes...")
            session.execute_write(create_indexes)

            # Load Agreements
            print("\nLoading Agreements...")
            agreements = load_jsonld("resolutions_agreements.jsonld")
            print(f"  Loaded {len(agreements)} agreements from JSON-LD")

            # Batch insert agreements
            batch_size = 1000
            for i in range(0, len(agreements), batch_size):
                batch = agreements[i:i+batch_size]
                session.execute_write(create_resolution_nodes, batch, "Agreement")
                print(f"  Created nodes: {i+len(batch)}/{len(agreements)}")

            # Create relationships
            print("  Creating relationships...")
            session.execute_write(create_resolution_relationships, agreements)
            session.execute_write(create_references_relationships, agreements)

            # Load Conclusions
            print("\nLoading Conclusions...")
            conclusions = load_jsonld("resolutions_conclusions.jsonld")
            print(f"  Loaded {len(conclusions)} conclusions from JSON-LD")

            for i in range(0, len(conclusions), batch_size):
                batch = conclusions[i:i+batch_size]
                session.execute_write(create_resolution_nodes, batch, "Conclusion")
                print(f"  Created nodes: {i+len(batch)}/{len(conclusions)}")

            session.execute_write(create_resolution_relationships, conclusions)
            session.execute_write(create_references_relationships, conclusions)

            # Load Working Assumptions
            print("\nLoading Working Assumptions...")
            was = load_jsonld("resolutions_working_assumptions.jsonld")
            print(f"  Loaded {len(was)} working assumptions from JSON-LD")

            for i in range(0, len(was), batch_size):
                batch = was[i:i+batch_size]
                session.execute_write(create_resolution_nodes, batch, "WorkingAssumption")
                print(f"  Created nodes: {i+len(batch)}/{len(was)}")

            session.execute_write(create_resolution_relationships, was)
            session.execute_write(create_references_relationships, was)

            # Summary
            result = session.run("""
                MATCH (r:Resolution)
                RETURN labels(r) AS labels, count(*) AS count
            """)

            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            for record in result:
                labels = [l for l in record["labels"] if l != "Resolution"]
                print(f"  {labels[0] if labels else 'Resolution'}: {record['count']}")

            # Count relationships
            result = session.run("""
                MATCH ()-[r:MADE_AT]->() WHERE startNode(r):Resolution
                RETURN 'MADE_AT' AS type, count(r) AS count
                UNION ALL
                MATCH ()-[r:RESOLUTION_BELONGS_TO]->() RETURN 'RESOLUTION_BELONGS_TO' AS type, count(r) AS count
                UNION ALL
                MATCH ()-[r:REFERENCES]->(:Tdoc) WHERE startNode(r):Resolution
                RETURN 'REFERENCES' AS type, count(r) AS count
            """)

            print("\nRelationships:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")

    finally:
        driver.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
