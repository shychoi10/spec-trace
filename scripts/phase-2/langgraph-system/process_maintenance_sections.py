#!/usr/bin/env python3
"""
Process each Maintenance Section individually

3개의 Maintenance Section을 개별 파일로 생성:
- Pre-Rel-18 E-UTRA Maintenance
- Pre-Rel-18 NR Maintenance
- Maintenance on Release 18
"""

import sys
from pathlib import Path

# Add src to path - must be before imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from src.utils.document_parser import AllSectionsParser
from src.utils.llm_manager import LLMManager
from src.workflows.maintenance_workflow import MaintenanceWorkflow
from src.models.section_types import SectionMetadata, SectionClassification, SectionType, Release, Technology


def main():
    # Paths
    docx_path = Path("/home/sihyeon/workspace/spec-trace/data/data_transformed/meetings/RAN1/TSGR1_120/Report/Final_Minutes_report_RAN1%23120_v100/Final_Minutes_report_RAN1#120_v100.docx")
    output_dir = Path("/home/sihyeon/workspace/spec-trace/output/phase-2/langgraph-system/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    meeting_id = "RAN1_120"
    meeting_number = "120"

    print("=" * 60)
    print("Processing Maintenance Sections Individually")
    print("=" * 60)

    # Initialize
    llm = LLMManager()
    parser = AllSectionsParser(str(docx_path), llm)
    workflow = MaintenanceWorkflow({})

    # Extract all sections
    print("\n[Step 1] Extracting all Heading 1 sections...")
    sections = parser.extract_all_heading1_sections()

    # Filter maintenance sections
    maintenance_sections = [s for s in sections if "maintenance" in s.title.lower()]
    print(f"Found {len(maintenance_sections)} Maintenance sections:")
    for s in maintenance_sections:
        print(f"  - {s.title} ({len(s.content)} chars)")

    # Define section configs (LLM이 분류한 결과 기반)
    section_configs = {
        "Pre-Rel-18 E-UTRA Maintenance": {
            "release": Release.PRE_REL_18,
            "technology": Technology.E_UTRA,
            "suffix": "pre_rel_18_e_utra"
        },
        "Pre-Rel-18 NR Maintenance": {
            "release": Release.PRE_REL_18,
            "technology": Technology.NR,
            "suffix": "pre_rel_18_nr"
        },
        "Maintenance on Release 18": {
            "release": Release.REL_18,
            "technology": None,
            "suffix": "rel_18"
        }
    }

    # Process each section
    print("\n[Step 2] Processing each section...")
    results = []

    for section in maintenance_sections:
        title = section.title
        config = section_configs.get(title)

        if not config:
            print(f"  ⚠️ Unknown section: {title}")
            continue

        print(f"\n  Processing: {title}")
        print(f"    Content length: {len(section.content)} chars")

        # Create metadata
        classification = SectionClassification(
            section_type=SectionType.MAINTENANCE,
            release=config["release"],
            technology=config["technology"],
            confidence=1.0
        )

        metadata = SectionMetadata(
            title=title,
            classification=classification,
            content_preview=section.content[:500]
        )

        # Output file
        output_file = output_dir / f"{meeting_id}_maintenance_{config['suffix']}.md"

        # Run workflow
        try:
            result = workflow.run_and_save(
                section_text=section.content,
                output_path=str(output_file),
                section_metadata=metadata,
                meeting_number=meeting_number
            )

            items_count = len(result.get("items", []))
            print(f"    ✅ Saved: {output_file.name} ({items_count} items)")
            results.append({
                "title": title,
                "file": output_file.name,
                "items": items_count,
                "size": output_file.stat().st_size
            })

        except Exception as e:
            print(f"    ❌ Error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"  {r['file']}: {r['items']} items, {r['size']:,} bytes")

    total_items = sum(r['items'] for r in results)
    print(f"\n  Total: {total_items} items across {len(results)} files")


if __name__ == "__main__":
    main()
