#!/usr/bin/env python3
"""
Sub-step 2-2: Neo4j 적재 (직접 Cypher)
APOC apoc.load.json()으로 JSON-LD를 파싱하고 직접 Cypher로 노드/관계 생성
"""

import time
from neo4j import GraphDatabase

# Neo4j connection settings (different port for cypher instance)
URI = "bolt://localhost:7688"
AUTH = ("neo4j", "password123")


def run_query(driver, query, description="", show_result=False):
    """Execute a Cypher query and return results with timing."""
    start = time.time()
    with driver.session() as session:
        result = session.run(query)
        records = list(result)
        elapsed = time.time() - start

    if show_result and records:
        print(f"    Result: {records[0].data()}")
    print(f"  {description}: {elapsed:.2f}s")
    return records, elapsed


def main():
    print("=" * 60)
    print("Sub-step 2-2: Neo4j 적재 (직접 Cypher)")
    print("=" * 60)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    total_start = time.time()

    try:
        # Step 1: Create indexes
        print("\n[Step 1] Creating indexes...")
        indexes = [
            ("CREATE INDEX idx_meeting_id IF NOT EXISTS FOR (m:Meeting) ON (m.id)", "Meeting index"),
            ("CREATE INDEX idx_release_id IF NOT EXISTS FOR (r:Release) ON (r.id)", "Release index"),
            ("CREATE INDEX idx_company_id IF NOT EXISTS FOR (c:Company) ON (c.id)", "Company index"),
            ("CREATE INDEX idx_contact_id IF NOT EXISTS FOR (c:Contact) ON (c.id)", "Contact index"),
            ("CREATE INDEX idx_workitem_id IF NOT EXISTS FOR (w:WorkItem) ON (w.id)", "WorkItem index"),
            ("CREATE INDEX idx_agenda_id IF NOT EXISTS FOR (a:AgendaItem) ON (a.id)", "AgendaItem index"),
            ("CREATE INDEX idx_spec_id IF NOT EXISTS FOR (s:Spec) ON (s.id)", "Spec index"),
            ("CREATE INDEX idx_wg_id IF NOT EXISTS FOR (w:WorkingGroup) ON (w.id)", "WorkingGroup index"),
            ("CREATE INDEX idx_tdoc_id IF NOT EXISTS FOR (t:Tdoc) ON (t.id)", "Tdoc index"),
            ("CREATE INDEX idx_tdoc_number IF NOT EXISTS FOR (t:Tdoc) ON (t.tdocNumber)", "Tdoc number index"),
        ]
        for query, desc in indexes:
            run_query(driver, query, desc)

        # Step 2: Load Reference Classes
        print("\n[Step 2] Loading Reference Classes...")

        # 2.1 Meetings
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/meetings.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (m:Meeting {id: item['@id']})
            SET m.meetingNumber = item['tdoc:meetingNumber'],
                m.workingGroup = item['tdoc:workingGroup']
            RETURN count(m) AS count
        """, "Meetings loaded", True)

        # 2.2 Releases
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/releases.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (r:Release {id: item['@id']})
            SET r.releaseName = item['tdoc:releaseName']
            RETURN count(r) AS count
        """, "Releases loaded", True)

        # 2.3 Specs
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/specs.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (s:Spec {id: item['@id']})
            SET s.specNumber = item['tdoc:specNumber'],
                s.specVersion = item['tdoc:specVersion']
            RETURN count(s) AS count
        """, "Specs loaded", True)

        # 2.4 Working Groups
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/working_groups.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (w:WorkingGroup {id: item['@id']})
            SET w.wgName = item['tdoc:wgName']
            RETURN count(w) AS count
        """, "Working Groups loaded", True)

        # 2.5 Companies
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/companies.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (c:Company {id: item['@id']})
            SET c.companyName = item['tdoc:companyName'],
                c.aliases = item['tdoc:aliases']
            RETURN count(c) AS count
        """, "Companies loaded", True)

        # 2.6 Work Items
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/work_items.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (w:WorkItem {id: item['@id']})
            SET w.workItemCode = item['tdoc:workItemCode']
            RETURN count(w) AS count
        """, "Work Items loaded", True)

        # 2.7 Contacts
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/contacts.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (c:Contact {id: item['@id']})
            SET c.contactName = item['tdoc:contactName'],
                c.contactId = item['tdoc:contactId']
            RETURN count(c) AS count
        """, "Contacts loaded", True)

        # 2.8 Agenda Items
        run_query(driver, """
            CALL apoc.load.json("file:///import/output/instances/agenda_items.jsonld") YIELD value
            UNWIND value['@graph'] AS item
            MERGE (a:AgendaItem {id: item['@id']})
            SET a.agendaNumber = item['tdoc:agendaNumber'],
                a.agendaDescription = item['tdoc:agendaDescription']
            RETURN count(a) AS count
        """, "Agenda Items loaded", True)

        # Step 3: Load Tdocs using periodic.iterate for batch processing
        print("\n[Step 3] Loading Tdocs (batch processing)...")

        # 3.1 Create Tdoc nodes
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "CALL apoc.load.json('file:///import/output/instances/tdocs.jsonld') YIELD value
                 UNWIND value['@graph'] AS item RETURN item",
                "WITH item
                 MERGE (t:Tdoc {id: item['@id']})
                 SET t.tdocNumber = item['tdoc:tdocNumber'],
                     t.title = item['tdoc:title'],
                     t.type = item['tdoc:type'],
                     t.status = item['tdoc:status'],
                     t.`for` = item['tdoc:for'],
                     t.abstract = item['tdoc:abstract'],
                     t.reservationDate = item['tdoc:reservationDate'],
                     t.uploadedDate = item['tdoc:uploadedDate'],
                     t.secretaryRemarks = item['tdoc:secretaryRemarks'],
                     t.crNumber = item['tdoc:crNumber'],
                     t.crCategory = item['tdoc:crCategory'],
                     t.clausesAffected = item['tdoc:clausesAffected'],
                     t.tsgCRPack = item['tdoc:tsgCRPack'],
                     t.affectsUICC = item['tdoc:affectsUICC'],
                     t.affectsME = item['tdoc:affectsME'],
                     t.affectsRAN = item['tdoc:affectsRAN'],
                     t.affectsCN = item['tdoc:affectsCN'],
                     t.direction = item['tdoc:direction'],
                     t._submittedBy = item['tdoc:submittedBy'],
                     t._hasContact = item['tdoc:hasContact'],
                     t._belongsTo = item['tdoc:belongsTo'],
                     t._presentedAt = item['tdoc:presentedAt'],
                     t._targetRelease = item['tdoc:targetRelease'],
                     t._relatedTo = item['tdoc:relatedTo'],
                     t._modifies = item['tdoc:modifies'],
                     t._isRevisionOf = item['tdoc:isRevisionOf'],
                     t._revisedTo = item['tdoc:revisedTo'],
                     t._replyTo = item['tdoc:replyTo'],
                     t._replyIn = item['tdoc:replyIn'],
                     t._sentTo = item['tdoc:sentTo'],
                     t._ccTo = item['tdoc:ccTo'],
                     t._originalLS = item['tdoc:originalLS'],
                    t._originatedFrom = item['tdoc:originatedFrom']
                 WITH item, t
                 CALL apoc.do.case([
                     item['@type'] = 'tdoc:CR', 'SET t:CR',
                     item['@type'] = 'tdoc:LS', 'SET t:LS'
                 ], '', {t: t})
                 YIELD value RETURN count(*)",
                {batchSize: 5000, parallel: false}
            ) YIELD batches, total, errorMessages
            RETURN batches, total, errorMessages
        """, "Tdoc nodes created", True)

        # Step 4: Create relationships
        print("\n[Step 4] Creating relationships...")

        # 4.1 presentedAt
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._presentedAt IS NOT NULL RETURN t",
                "WITH t
                 MATCH (m:Meeting {id: t._presentedAt})
                 MERGE (t)-[:PRESENTED_AT]->(m)",
                {batchSize: 5000}
            ) YIELD batches, total RETURN batches, total
        """, "presentedAt relationships", True)

        # 4.2 belongsTo
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._belongsTo IS NOT NULL RETURN t",
                "WITH t
                 MATCH (a:AgendaItem {id: t._belongsTo})
                 MERGE (t)-[:BELONGS_TO]->(a)",
                {batchSize: 5000}
            ) YIELD batches, total RETURN batches, total
        """, "belongsTo relationships", True)

        # 4.3 hasContact
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._hasContact IS NOT NULL RETURN t",
                "WITH t
                 MATCH (c:Contact {id: t._hasContact})
                 MERGE (t)-[:HAS_CONTACT]->(c)",
                {batchSize: 5000}
            ) YIELD batches, total RETURN batches, total
        """, "hasContact relationships", True)

        # 4.4 targetRelease
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._targetRelease IS NOT NULL RETURN t",
                "WITH t
                 MATCH (r:Release {id: t._targetRelease})
                 MERGE (t)-[:TARGET_RELEASE]->(r)",
                {batchSize: 5000}
            ) YIELD batches, total RETURN batches, total
        """, "targetRelease relationships", True)

        # 4.5 submittedBy (array)
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._submittedBy IS NOT NULL RETURN t",
                "WITH t
                 UNWIND t._submittedBy AS companyRef
                 MATCH (c:Company {id: companyRef})
                 MERGE (t)-[:SUBMITTED_BY]->(c)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "submittedBy relationships", True)

        # 4.6 relatedTo (array)
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._relatedTo IS NOT NULL RETURN t",
                "WITH t
                 UNWIND t._relatedTo AS wiRef
                 MATCH (w:WorkItem {id: wiRef})
                 MERGE (t)-[:RELATED_TO]->(w)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "relatedTo relationships", True)

        # 4.7 modifies (CR -> Spec)
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._modifies IS NOT NULL RETURN t",
                "WITH t
                 MATCH (s:Spec {id: t._modifies})
                 MERGE (t)-[:MODIFIES]->(s)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "modifies relationships", True)

        # 4.8 isRevisionOf
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._isRevisionOf IS NOT NULL RETURN t",
                "WITH t
                 MATCH (t2:Tdoc {id: t._isRevisionOf})
                 MERGE (t)-[:IS_REVISION_OF]->(t2)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "isRevisionOf relationships", True)

        # 4.9 sentTo (LS -> WorkingGroup, array)
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._sentTo IS NOT NULL RETURN t",
                "WITH t
                 UNWIND t._sentTo AS wgRef
                 MATCH (w:WorkingGroup {id: wgRef})
                 MERGE (t)-[:SENT_TO]->(w)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "sentTo relationships", True)

        # 4.10 ccTo (LS -> WorkingGroup, array)
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._ccTo IS NOT NULL RETURN t",
                "WITH t
                 UNWIND t._ccTo AS wgRef
                 MATCH (w:WorkingGroup {id: wgRef})
                 MERGE (t)-[:CC_TO]->(w)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "ccTo relationships", True)

        # 4.11 replyTo (Tdoc -> Tdoc) - Issue #3 해결
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._replyTo IS NOT NULL RETURN t",
                "WITH t
                 MATCH (t2:Tdoc {id: t._replyTo})
                 MERGE (t)-[:REPLY_TO]->(t2)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "replyTo relationships", True)

        # 4.12 originalLS (Tdoc -> Tdoc) - Issue #2 해결
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._originalLS IS NOT NULL RETURN t",
                "WITH t
                 MATCH (ls:Tdoc {id: t._originalLS})
                 MERGE (t)-[:ORIGINAL_LS]->(ls)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "originalLS relationships", True)

        # 4.13 revisedTo (Tdoc -> Tdoc) - Issue #4 해결
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._revisedTo IS NOT NULL RETURN t",
                "WITH t
                 MATCH (t2:Tdoc {id: t._revisedTo})
                 MERGE (t)-[:REVISED_TO]->(t2)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "revisedTo relationships", True)

        # 4.14 originatedFrom (Tdoc -> WorkingGroup) - Issue #1, #5 해결
        run_query(driver, """
            CALL apoc.periodic.iterate(
                "MATCH (t:Tdoc) WHERE t._originatedFrom IS NOT NULL RETURN t",
                "WITH t
                 UNWIND t._originatedFrom AS wgRef
                 MATCH (w:WorkingGroup {id: wgRef})
                 MERGE (t)-[:ORIGINATED_FROM]->(w)",
                {batchSize: 2000}
            ) YIELD batches, total RETURN batches, total
        """, "originatedFrom relationships", True)

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
        print(f"  Total time: {total_elapsed:.2f}s ({total_elapsed/60:.1f}m)")
        print("=" * 60)

        return {
            "method": "cypher",
            "nodes": total_nodes,
            "relationships": total_rels,
            "time_seconds": total_elapsed
        }

    finally:
        driver.close()


if __name__ == "__main__":
    stats = main()
    print(f"\nStats: {stats}")
