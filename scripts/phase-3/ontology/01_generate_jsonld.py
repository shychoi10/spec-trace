#!/usr/bin/env python3
"""
Generate JSON-LD instances from parsed Phase-3 reports.

Spec: Uses "Resolution" terminology per Section 4.1.

Outputs:
- ontology/output/instances/phase-3/resolutions_agreements.jsonld
- ontology/output/instances/phase-3/resolutions_conclusions.jsonld
- ontology/output/instances/phase-3/resolutions_working_assumptions.jsonld
- ontology/output/instances/phase-3/summaries.jsonld
- ontology/output/instances/phase-3/session_notes.jsonld
"""

import json
from pathlib import Path
from datetime import datetime


# Paths
PARSED_DIR = Path(__file__).parent.parent.parent.parent / "ontology" / "output" / "parsed_reports"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "ontology" / "output" / "instances" / "phase-3"

# JSON-LD Context (Spec: Resolution terminology per Section 4.1)
CONTEXT = {
    "@vocab": "http://3gpp.org/ontology/tdoc#",
    "tdoc": "http://3gpp.org/ontology/tdoc#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "meeting": {"@id": "tdoc:meeting", "@type": "@id"},
    "agenda": {"@id": "tdoc:agenda", "@type": "@id"},
    "references": {"@id": "tdoc:references", "@type": "@id"},
    "moderatedBy": {"@id": "tdoc:moderatedBy", "@type": "@id"},
    "chairedBy": {"@id": "tdoc:chairedBy", "@type": "@id"},
    "resolutionBelongsTo": {"@id": "tdoc:resolutionBelongsTo", "@type": "@id"},
    "madeAt": {"@id": "tdoc:madeAt", "@type": "@id"},
}


def load_all_reports() -> list[dict]:
    """Load all parsed reports from phase-3 directory."""
    reports = []
    for path in sorted(PARSED_DIR.glob("RAN1_*.json")):
        with open(path, 'r', encoding='utf-8') as f:
            reports.append(json.load(f))
    return reports


def generate_resolution_id_uri(resolution_id: str) -> str:
    """Generate URI for resolution (Spec: Section 4.1)."""
    return f"tdoc:resolution/{resolution_id}"


def generate_meeting_uri(meeting_id: str) -> str:
    """Generate URI for meeting.

    Note: Must match Phase-2 Meeting URI format (underscore, not hyphen).
    Phase-2 uses: tdoc:meeting/RAN1_100
    """
    # meeting_id like "RAN1#112" -> "meeting:RAN1_112" (underscore to match Phase-2)
    return f"tdoc:meeting/{meeting_id.replace('#', '_')}"


def generate_agenda_uri(meeting_id: str, agenda_item: str) -> str:
    """Generate URI for agenda item."""
    meeting_num = meeting_id.replace("RAN1#", "")
    return f"tdoc:agenda/{meeting_num}-{agenda_item}"


def generate_tdoc_uri(tdoc_number: str) -> str:
    """Generate URI for TDoc."""
    return f"tdoc:{tdoc_number}"


def generate_company_uri(company_name: str) -> str:
    """Generate URI for company."""
    # Normalize company name for URI
    normalized = company_name.strip().replace(" ", "_").replace("/", "_")
    return f"tdoc:company/{normalized}"


def generate_agreements_jsonld(reports: list[dict]) -> dict:
    """Generate JSON-LD for Agreement instances (Spec: Section 4.1)."""
    instances = []

    for report in reports:
        meeting_id = report["meeting_id"]
        meeting_uri = generate_meeting_uri(meeting_id)

        for agr in report.get("agreements", []):
            instance = {
                "@id": generate_resolution_id_uri(agr["decision_id"]),
                "@type": ["Resolution", "Agreement"],  # Multiple types for inheritance
                "resolutionId": agr["decision_id"],
                "content": agr["content"],
                "resolutionBelongsTo": generate_agenda_uri(meeting_id, agr["agenda_item"]),
                "madeAt": meeting_uri,
            }

            # Optional fields
            if agr.get("has_ffs"):
                instance["hasFFS"] = True
            if agr.get("has_tbd"):
                instance["hasTBD"] = True
            if agr.get("session_context"):
                instance["sessionContext"] = agr["session_context"]
            if agr.get("note"):
                instance["note"] = agr["note"]

            # References to TDocs
            if agr.get("referenced_tdocs"):
                refs = [generate_tdoc_uri(t) for t in agr["referenced_tdocs"]]
                instance["references"] = refs if len(refs) > 1 else refs[0]

            instances.append(instance)

    return {
        "@context": CONTEXT,
        "@graph": instances
    }


def generate_conclusions_jsonld(reports: list[dict]) -> dict:
    """Generate JSON-LD for Conclusion instances (Spec: Section 4.1)."""
    instances = []

    for report in reports:
        meeting_id = report["meeting_id"]
        meeting_uri = generate_meeting_uri(meeting_id)

        for con in report.get("conclusions", []):
            instance = {
                "@id": generate_resolution_id_uri(con["decision_id"]),
                "@type": ["Resolution", "Conclusion"],  # Multiple types for inheritance
                "resolutionId": con["decision_id"],
                "content": con["content"],
                "resolutionBelongsTo": generate_agenda_uri(meeting_id, con["agenda_item"]),
                "madeAt": meeting_uri,
            }

            if con.get("has_consensus") is not None:
                instance["hasConsensus"] = con["has_consensus"]
            if con.get("session_context"):
                instance["sessionContext"] = con["session_context"]
            if con.get("note"):
                instance["note"] = con["note"]

            if con.get("referenced_tdocs"):
                refs = [generate_tdoc_uri(t) for t in con["referenced_tdocs"]]
                instance["references"] = refs if len(refs) > 1 else refs[0]

            instances.append(instance)

    return {
        "@context": CONTEXT,
        "@graph": instances
    }


def generate_working_assumptions_jsonld(reports: list[dict]) -> dict:
    """Generate JSON-LD for WorkingAssumption instances (Spec: Section 4.1)."""
    instances = []

    for report in reports:
        meeting_id = report["meeting_id"]
        meeting_uri = generate_meeting_uri(meeting_id)

        for wa in report.get("working_assumptions", []):
            instance = {
                "@id": generate_resolution_id_uri(wa["decision_id"]),
                "@type": ["Resolution", "WorkingAssumption"],  # Multiple types for inheritance
                "resolutionId": wa["decision_id"],
                "content": wa["content"],
                "resolutionBelongsTo": generate_agenda_uri(meeting_id, wa["agenda_item"]),
                "madeAt": meeting_uri,
            }

            if wa.get("session_context"):
                instance["sessionContext"] = wa["session_context"]
            if wa.get("note"):
                instance["note"] = wa["note"]

            if wa.get("referenced_tdocs"):
                refs = [generate_tdoc_uri(t) for t in wa["referenced_tdocs"]]
                instance["references"] = refs if len(refs) > 1 else refs[0]

            instances.append(instance)

    return {
        "@context": CONTEXT,
        "@graph": instances
    }


def generate_summaries_jsonld(reports: list[dict]) -> dict:
    """Generate JSON-LD for Summary instances (FL and Moderator)."""
    instances = []

    for report in reports:
        meeting_id = report["meeting_id"]
        meeting_uri = generate_meeting_uri(meeting_id)

        # FL Summaries
        for fl in report.get("fl_summaries", []):
            instance = {
                "@id": generate_tdoc_uri(fl["tdoc_number"]),
                "@type": "Summary",
                "tdocNumber": fl["tdoc_number"],
                "title": fl["title"],
                "summaryType": "FL",
                "meeting": meeting_uri,
                "moderatedBy": generate_company_uri(fl["company"]),
            }

            if fl.get("agenda_item") and fl["agenda_item"] != "UNKNOWN":
                instance["agenda"] = generate_agenda_uri(meeting_id, fl["agenda_item"])
            if fl.get("round_number"):
                instance["roundNumber"] = fl["round_number"]

            instances.append(instance)

        # Moderator Summaries
        for mod in report.get("moderator_summaries", []):
            instance = {
                "@id": generate_tdoc_uri(mod["tdoc_number"]),
                "@type": "Summary",
                "tdocNumber": mod["tdoc_number"],
                "title": mod["title"],
                "summaryType": "Moderator",
                "meeting": meeting_uri,
                "moderatedBy": generate_company_uri(mod["company"]),
            }

            if mod.get("agenda_item") and mod["agenda_item"] != "UNKNOWN":
                instance["agenda"] = generate_agenda_uri(meeting_id, mod["agenda_item"])
            if mod.get("round_number"):
                instance["roundNumber"] = mod["round_number"]

            instances.append(instance)

    return {
        "@context": CONTEXT,
        "@graph": instances
    }


def generate_session_notes_jsonld(reports: list[dict]) -> dict:
    """Generate JSON-LD for SessionNotes instances."""
    instances = []

    for report in reports:
        meeting_id = report["meeting_id"]
        meeting_uri = generate_meeting_uri(meeting_id)

        for sn in report.get("session_notes", []):
            instance = {
                "@id": generate_tdoc_uri(sn["tdoc_number"]),
                "@type": "SessionNotes",
                "tdocNumber": sn["tdoc_number"],
                "title": sn["title"],
                "meeting": meeting_uri,
                "chairedBy": generate_company_uri(sn["company"]),
            }

            if sn.get("agenda_item") and sn["agenda_item"] != "UNKNOWN":
                instance["agenda"] = generate_agenda_uri(meeting_id, sn["agenda_item"])

            instances.append(instance)

    return {
        "@context": CONTEXT,
        "@graph": instances
    }


def save_jsonld(data: dict, filename: str) -> None:
    """Save JSON-LD to file."""
    output_path = OUTPUT_DIR / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data['@graph'])} instances to {output_path}")


def main():
    """Generate all JSON-LD files."""
    print("Loading parsed reports...")
    reports = load_all_reports()
    print(f"Loaded {len(reports)} reports")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate JSON-LD files (Spec: Resolution terminology per Section 4.1)
    print("\nGenerating JSON-LD instances...")

    # Agreements
    agreements = generate_agreements_jsonld(reports)
    save_jsonld(agreements, "resolutions_agreements.jsonld")

    # Conclusions
    conclusions = generate_conclusions_jsonld(reports)
    save_jsonld(conclusions, "resolutions_conclusions.jsonld")

    # Working Assumptions
    was = generate_working_assumptions_jsonld(reports)
    save_jsonld(was, "resolutions_working_assumptions.jsonld")

    # Summaries (FL + Moderator)
    summaries = generate_summaries_jsonld(reports)
    save_jsonld(summaries, "summaries.jsonld")

    # Session Notes
    session_notes = generate_session_notes_jsonld(reports)
    save_jsonld(session_notes, "session_notes.jsonld")

    # Summary
    total = (
        len(agreements["@graph"]) +
        len(conclusions["@graph"]) +
        len(was["@graph"]) +
        len(summaries["@graph"]) +
        len(session_notes["@graph"])
    )
    print(f"\n{'='*60}")
    print(f"Total instances generated: {total}")
    print(f"  Agreements: {len(agreements['@graph'])}")
    print(f"  Conclusions: {len(conclusions['@graph'])}")
    print(f"  Working Assumptions: {len(was['@graph'])}")
    print(f"  Summaries: {len(summaries['@graph'])}")
    print(f"  Session Notes: {len(session_notes['@graph'])}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
