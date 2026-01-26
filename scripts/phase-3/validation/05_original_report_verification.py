#!/usr/bin/env python3
"""
Original Report Verification: Direct comparison with source DOCX files.

Samples random Agreements/Conclusions from parsed data and verifies
they exist in the original Final Report documents.
"""

import json
import random
import re
from pathlib import Path
from datetime import datetime
from docx import Document
import zipfile
import xml.etree.ElementTree as ET

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
PARSED_DIR = BASE_DIR / "ontology" / "output" / "parsed_reports" / "v2"
REPORTS_DIR = BASE_DIR / "data" / "data_extracted" / "meetings" / "RAN1"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"


def find_report_file(meeting_id: str) -> Path | None:
    """Find the Final Report file for a meeting."""
    # Convert meeting_id to folder name
    # RAN1#100 -> TSGR1_100, RAN1#100b -> TSGR1_100bis
    match = re.match(r'RAN1#(\d+)(\w?)', meeting_id)
    if not match:
        return None

    num = match.group(1)
    suffix = match.group(2)

    # Try different folder patterns
    folder_patterns = [
        f"TSGR1_{num}",
        f"TSGR1_{num}bis" if suffix == 'b' else None,
        f"TSGR1_{num}{suffix}" if suffix else None,
    ]

    for pattern in filter(None, folder_patterns):
        folder = REPORTS_DIR / pattern
        if folder.exists():
            # Look for Final Report
            for f in folder.glob("Report/**/*.doc*"):
                if "final" in f.name.lower() or "report" in f.name.lower():
                    return f

            # Also try root level
            for f in folder.glob("*.doc*"):
                if "final" in f.name.lower() or "report" in f.name.lower():
                    return f

    return None


def extract_text_from_docx(filepath: Path) -> str:
    """Extract all text from a DOCX file."""
    try:
        doc = Document(filepath)
        text_parts = []
        for para in doc.paragraphs:
            text_parts.append(para.text)
        return "\n".join(text_parts)
    except Exception as e:
        return ""


def extract_text_from_docm(filepath: Path) -> str:
    """Extract text from a DOCM file."""
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            if 'word/document.xml' in z.namelist():
                xml_content = z.read('word/document.xml')
                tree = ET.fromstring(xml_content)

                # Define namespace
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                text_parts = []
                for para in tree.findall('.//w:p', ns):
                    para_text = []
                    for t in para.findall('.//w:t', ns):
                        if t.text:
                            para_text.append(t.text)
                    text_parts.append(''.join(para_text))

                return "\n".join(text_parts)
    except Exception as e:
        return ""


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might differ
    text = re.sub(r'[""''"]', '"', text)
    text = re.sub(r'[–—]', '-', text)
    return text.strip().lower()


def verify_content_in_report(content: str, report_text: str) -> dict:
    """Verify if content appears in the report."""
    # Normalize both texts
    norm_content = normalize_text(content)
    norm_report = normalize_text(report_text)

    # Try exact match first (first 100 chars)
    search_text = norm_content[:100]
    exact_match = search_text in norm_report

    # Try fuzzy match with key phrases
    words = norm_content.split()[:10]
    key_phrase = ' '.join(words)
    fuzzy_match = key_phrase in norm_report

    # Try finding significant tokens
    significant_words = [w for w in words if len(w) > 5][:5]
    token_matches = sum(1 for w in significant_words if w in norm_report)

    return {
        "exact_match": exact_match,
        "fuzzy_match": fuzzy_match,
        "token_matches": token_matches,
        "total_tokens": len(significant_words),
        "verified": exact_match or fuzzy_match or (token_matches >= len(significant_words) * 0.6)
    }


def sample_and_verify(num_samples: int = 30) -> dict:
    """Sample random items and verify against original reports."""

    # Load parsed data
    all_items = []
    for f in sorted(PARSED_DIR.glob("RAN1_*_v2.json")):
        with open(f) as fp:
            data = json.load(fp)
            meeting_id = data["meeting_id"]
            for agr in data["agreements"]:
                all_items.append({
                    "meeting": meeting_id,
                    "type": "Agreement",
                    "id": agr["decision_id"],
                    "content": agr["content"],
                    "agenda": agr["agenda_item"]
                })
            for conc in data["conclusions"]:
                all_items.append({
                    "meeting": meeting_id,
                    "type": "Conclusion",
                    "id": conc["decision_id"],
                    "content": conc["content"],
                    "agenda": conc["agenda_item"]
                })

    # Sample items
    samples = random.sample(all_items, min(num_samples, len(all_items)))

    results = []
    report_cache = {}

    for item in samples:
        meeting_id = item["meeting"]

        # Find and cache report
        if meeting_id not in report_cache:
            report_path = find_report_file(meeting_id)
            if report_path:
                if report_path.suffix.lower() == '.docx':
                    report_cache[meeting_id] = extract_text_from_docx(report_path)
                elif report_path.suffix.lower() == '.docm':
                    report_cache[meeting_id] = extract_text_from_docm(report_path)
                else:
                    report_cache[meeting_id] = ""
            else:
                report_cache[meeting_id] = None

        report_text = report_cache.get(meeting_id)

        if report_text is None:
            result = {
                "item": item,
                "status": "SKIP",
                "reason": "report_not_found"
            }
        elif not report_text:
            result = {
                "item": item,
                "status": "SKIP",
                "reason": "report_empty"
            }
        else:
            verification = verify_content_in_report(item["content"], report_text)
            result = {
                "item": {
                    "id": item["id"],
                    "type": item["type"],
                    "meeting": item["meeting"],
                    "agenda": item["agenda"],
                    "content_preview": item["content"][:100]
                },
                "status": "PASS" if verification["verified"] else "FAIL",
                "verification": verification
            }

        results.append(result)

    return results


def main():
    print("=" * 70)
    print("ORIGINAL REPORT VERIFICATION")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    print("[1/2] Sampling and verifying against original reports...")
    print("  (This may take a moment as we read DOCX files)")
    print()

    results = sample_and_verify(50)

    # Analyze results
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    print("\n[2/2] Results Analysis")
    print("=" * 70)
    print(f"  Total Samples: {len(results)}")
    print(f"  ✅ PASS (verified in original): {passed}")
    print(f"  ❌ FAIL (not found): {failed}")
    print(f"  ⏭️  SKIP (report unavailable): {skipped}")

    verifiable = passed + failed
    if verifiable > 0:
        verification_rate = round(100 * passed / verifiable, 2)
        print(f"\n  Verification Rate: {verification_rate}%")
    else:
        verification_rate = 0
        print("\n  No verifiable samples")

    # Print sample results
    print("\n" + "=" * 70)
    print("SAMPLE VERIFICATION DETAILS")
    print("=" * 70)

    for r in results[:10]:
        if r["status"] == "PASS":
            print(f"\n  ✅ [{r['item']['id']}] {r['item']['type']}")
            print(f"     Meeting: {r['item']['meeting']}, Agenda: {r['item']['agenda']}")
            print(f"     Content: {r['item']['content_preview'][:60]}...")
            v = r["verification"]
            print(f"     Match: exact={v['exact_match']}, fuzzy={v['fuzzy_match']}, tokens={v['token_matches']}/{v['total_tokens']}")
        elif r["status"] == "FAIL":
            print(f"\n  ❌ [{r['item']['id']}] {r['item']['type']}")
            print(f"     Meeting: {r['item']['meeting']}, Agenda: {r['item']['agenda']}")
            print(f"     Content: {r['item']['content_preview'][:60]}...")
            v = r["verification"]
            print(f"     Match: exact={v['exact_match']}, fuzzy={v['fuzzy_match']}, tokens={v['token_matches']}/{v['total_tokens']}")

    # Save results
    output_file = OUTPUT_DIR / "original_report_verification.json"
    output = {
        "executed_at": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "verification_rate": verification_rate
        },
        "results": results
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to: {output_file}")

    # Overall assessment
    print("\n" + "=" * 70)
    print("OVERALL ASSESSMENT")
    print("=" * 70)
    if verification_rate >= 90:
        print("  ✅ HIGH CONFIDENCE: >90% of sampled content verified in original reports")
    elif verification_rate >= 70:
        print("  ⚠️  MEDIUM CONFIDENCE: 70-90% verification rate")
    else:
        print("  ❌ LOW CONFIDENCE: <70% verification rate - investigation needed")

    return output


if __name__ == "__main__":
    main()
