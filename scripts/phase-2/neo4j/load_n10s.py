#!/usr/bin/env python3
"""
Sub-step 2-1: Neo4j 적재 (n10s)
neosemantics 플러그인을 사용하여 RDF/JSON-LD 데이터를 Neo4j에 적재
"""

import time
from neo4j import GraphDatabase

# Neo4j connection settings
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password123")


def run_query(driver, query, description=""):
    """Execute a Cypher query and return results with timing."""
    start = time.time()
    with driver.session() as session:
        result = session.run(query)
        records = list(result)
        elapsed = time.time() - start
    print(f"  {description}: {elapsed:.2f}s, {len(records)} records")
    return records, elapsed


def main():
    print("=" * 60)
    print("Sub-step 2-1: Neo4j 적재 (n10s)")
    print("=" * 60)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    total_start = time.time()

    try:
        # Step 0: Clear existing data for fresh reload
        print("\n[Step 0] Clearing existing data...")
        run_query(driver, "MATCH (n) DETACH DELETE n", "All nodes deleted")
        run_query(driver, "CALL n10s.graphconfig.drop() YIELD value RETURN value", "GraphConfig dropped")

        # Step 1: Create constraint
        print("\n[Step 1] Creating constraint...")
        run_query(driver,
            "CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE",
            "Constraint created")

        # Step 2: Initialize GraphConfig
        # Note: OVERWRITE mode ensures single values for content/properties
        # This allows standard CONTAINS queries to work
        # applyNeo4jNaming: true converts relationship names to UPPER_CASE format
        print("\n[Step 2] Initializing GraphConfig...")
        run_query(driver,
            """CALL n10s.graphconfig.init({
                handleVocabUris: "IGNORE",
                handleMultival: "OVERWRITE",
                keepLangTag: false,
                keepCustomDataTypes: false,
                applyNeo4jNaming: true
            })""",
            "GraphConfig initialized")

        # Step 3: Load TBox (Ontology Schema)
        print("\n[Step 3] Loading TBox (Ontology Schema)...")
        records, _ = run_query(driver,
            """CALL n10s.onto.import.fetch("file:///import/tdoc-ontology.ttl", "Turtle")
               YIELD terminationStatus, triplesLoaded, triplesParsed
               RETURN terminationStatus, triplesLoaded, triplesParsed""",
            "TBox loaded")
        if records:
            print(f"    Status: {records[0]['terminationStatus']}, Triples: {records[0]['triplesLoaded']}")

        # Step 4: Load ABox (Instances) - Phase-2 + Phase-3
        print("\n[Step 4] Loading ABox (Instances)...")

        # Phase-2 instances (base ontology)
        phase2_files = [
            ("phase-2/meetings.jsonld", 59),
            ("phase-2/releases.jsonld", 13),
            ("phase-2/specs.jsonld", 75),
            ("phase-2/working_groups.jsonld", 118),
            ("phase-2/companies.jsonld", 222),
            ("phase-2/work_items.jsonld", 419),
            ("phase-2/contacts.jsonld", 982),
            ("phase-2/agenda_items.jsonld", 1335),
            ("phase-2/tdocs.jsonld", 122257),  # Largest file last
        ]

        # Phase-3 instances (Resolution ontology extension)
        phase3_files = [
            ("phase-3/session_notes.jsonld", 400),
            ("phase-3/summaries.jsonld", 2100),
            ("phase-3/resolutions_working_assumptions.jsonld", 946),
            ("phase-3/resolutions_conclusions.jsonld", 2683),
            ("phase-3/resolutions_agreements.jsonld", 21017),
        ]

        all_files = phase2_files + phase3_files
        total_triples = 0

        for filename, expected_count in all_files:
            print(f"\n  Loading {filename} (expected: {expected_count} instances)...")
            start = time.time()
            with driver.session() as session:
                result = session.run(
                    f"""CALL n10s.rdf.import.fetch("file:///import/output/instances/{filename}", "JSON-LD")
                        YIELD terminationStatus, triplesLoaded, triplesParsed
                        RETURN terminationStatus, triplesLoaded, triplesParsed"""
                )
                records = list(result)
            elapsed = time.time() - start

            if records:
                status = records[0]['terminationStatus']
                triples = records[0]['triplesLoaded']
                total_triples += triples
                print(f"    Status: {status}, Triples: {triples}, Time: {elapsed:.2f}s")
            else:
                print(f"    WARNING: No result returned for {filename}")

        # Step 5: Verification
        print("\n" + "=" * 60)
        print("[Step 5] Verification")
        print("=" * 60)

        # Node counts by label
        print("\n[5.1] Node counts by label:")
        with driver.session() as session:
            result = session.run(
                """MATCH (n)
                   RETURN labels(n)[0] AS label, count(n) AS count
                   ORDER BY count DESC"""
            )
            total_nodes = 0
            for record in result:
                print(f"    {record['label']}: {record['count']}")
                total_nodes += record['count']
            print(f"    TOTAL: {total_nodes}")

        # Relationship counts
        print("\n[5.2] Relationship counts by type:")
        with driver.session() as session:
            result = session.run(
                """MATCH ()-[r]->()
                   RETURN type(r) AS relType, count(r) AS count
                   ORDER BY count DESC"""
            )
            total_rels = 0
            for record in result:
                print(f"    {record['relType']}: {record['count']}")
                total_rels += record['count']
            print(f"    TOTAL: {total_rels}")

        # Summary
        total_elapsed = time.time() - total_start
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"  Total nodes: {total_nodes}")
        print(f"  Total relationships: {total_rels}")
        print(f"  Total triples loaded: {total_triples}")
        print(f"  Total time: {total_elapsed:.2f}s ({total_elapsed/60:.1f}m)")
        print("=" * 60)

        # Return stats for comparison
        return {
            "method": "n10s",
            "nodes": total_nodes,
            "relationships": total_rels,
            "triples": total_triples,
            "time_seconds": total_elapsed
        }

    finally:
        driver.close()


if __name__ == "__main__":
    stats = main()
    print(f"\nStats: {stats}")
