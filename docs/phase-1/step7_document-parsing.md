# Phase-1 Step-7: Document Parsing (Layer-1)

## Overview

**Status**: ⏳ READY TO START (Step-6 complete, previous work cleared)
**Goal**: Parse transformed documents into structured JSON (Layer-1 format) for Phase-2 DB construction

**Note**: Previous parsing scripts and logs have been cleaned up (2025-11-10). Starting fresh with new implementation.

**Document Types** (4 separate parsers):
1. **Docs (TDocs)** - Technical Documents (⏳ Priority 1)
2. **Report** - Meeting Minutes (⏳ Priority 2)
3. **Change Requests** - CR documents (⏳ Priority 3)
4. **Specifications** - TS 38.xxx documents (⏳ Priority 4)

**Workflow**:
```
data_transformed (Step-6 output) → data_parsed (JSON Layer-1) → Ready for Phase-2
```

**Prerequisites**:
- ✅ Step-6 Sub-step 6-1: Transform complete (DOC→DOCX, PPT→PPTX)
- ✅ Step-6 Sub-step 6-2: Schema v2.0 validated
- ✅ Step-6 Sub-step 6-3: Multi-format strategy defined

---

## Phase-1 Step-7 Sub-steps

### ⏳ Sub-step 7-1: DOCX Basic Parser
- **Goal**: Parse DOCX files, extract metadata + text + references
- **Status**: Planned
- **Scope**: 50 representative TDocs (sample-based development)
- **Output**: JSON files with Schema v2.0 (metadata + text + references)

### ⏳ Sub-step 7-2: XLSX Integration
- **Goal**: Integrate XLSX data into DOCX parsing results
- **Status**: Planned
- **Scope**: 30 multi-format TDoc folders (DOCX + XLSX)
- **Output**: Unified JSON with `supplementary_data.xlsx_files[]`

### ⏳ Sub-step 7-3: Advanced Features
- **Goal**: Extract tables, equations, images from DOCX
- **Status**: Planned
- **Scope**: 40 TDocs with rich content
- **Output**: Enhanced JSON with tables/equations/figures sections

### ⏳ Sub-step 7-4: Full Scale Parsing
- **Goal**: Parse all 119,565 TDoc folders with production quality
- **Status**: Planned
- **Scope**: Complete dataset
- **Output**: Full `data/data_parsed/` dataset

---

## Parser 1: Docs (TDocs)

### Status: ⏳ PLANNED

### Document Analysis Results

Based on analysis of 15 representative TDoc samples:

**File Statistics**:
- Format distribution: 80.5% DOCX, 19.5% DOC (after Transform: 100% DOCX)
- Average size: 0.73 MB
- Average paragraphs: 389
- Average equations: 19.5 (OMML format)
- Average tables: 6.7
- Average images: 9.2

**Structure Characteristics**:
- Simple section hierarchy (1-3 levels)
- Custom styles dominant (TAH, afa, BodyText)
- TDoc number in filename + header
- Metadata: "Title:", "Source:", "Agenda item:" fields

**Parsing Difficulty**:
- ✅ Easy (95%+ success): TDoc number, plain text, images, references
- ⚠️ Medium (75-85%): tables, equations, captions
- ❌ Hard (40-70%): custom style hierarchy, merged cells

---

### Implementation Plan

Parser implementation is divided into 4 sub-steps for incremental development:

#### Sub-step 7-1: DOCX Basic Parser (Priority: CRITICAL)

**Goal**: Parse DOCX files only, extract metadata + text + references

**Scope**:
- **Input**: DOCX files from `data_transformed/meetings/RAN1/`
- **Output**: JSON files in `data_parsed/meetings/RAN1/docs/`
- **Sample size**: 50 representative TDocs (diverse years, companies, topics)

**Features**:
- TDoc number extraction (filename → header → fallback)
- Metadata extraction (title, source, meeting, agenda, location)
- Plain text extraction (paragraph-level with styles preserved)
- Reference pattern extraction (R1-XXXXXX, TS 38.xxx, Figure X, Table X)
- Section structure extraction (Heading styles)
- Proposals/Observations/Agreements extraction (numbered lists)
- JSON output with Schema v2.0

**Success Criteria**:
- TDoc number: 100%
- Metadata (MUST HAVE fields): 95%+
- Text: 100%
- References: 95%+
- JSON validity: 100%

**Timeline**: 1-2 days

---

#### Sub-step 7-2: XLSX Integration (Priority: HIGH)

**Goal**: Integrate XLSX files into DOCX parsing results

**Scope**:
- **Input**: Folders with DOCX + XLSX (1,060 folders)
- **Output**: Unified JSON with `supplementary_data.xlsx_files[]`
- **Sample size**: 30 folders with diverse XLSX types

**Features**:
- XLSX classification logic (simulation/rrc_parameter/admin/unknown)
- Tiered extraction:
  - Simulation: Full data extraction (all sheets, all rows)
  - RRC parameters: Summary extraction (sheet names, columns, row count)
  - Admin: Metadata only (filename, skip content)
- Integration into existing DOCX JSON structure

**XLSX Classification Logic** (from Step-6 Sub-step 6-3):
```python
def classify_xlsx(filename: str) -> str:
    """Classify XLSX file type by filename keywords"""
    fn_lower = filename.lower()

    # Priority 1: Simulation results
    sim_keywords = ['simulation', 'evaluation', 'performance', 'result',
                    'link-level', 'system-level', 'lls', 'sls']
    if any(kw in fn_lower for kw in sim_keywords):
        return 'simulation'

    # Priority 2: RRC parameters
    rrc_keywords = ['rrc', 'parameter', 'config', 'ie', 'information-element']
    if any(kw in fn_lower for kw in rrc_keywords):
        return 'rrc_parameter'

    # Priority 3: Meeting lists (skip)
    admin_keywords = ['tdoc_list', 'attendance', 'participant', 'agenda']
    if any(kw in fn_lower for kw in admin_keywords):
        return 'admin'

    # Default: Unknown, extract summary
    return 'unknown'
```

**Dependencies**: Sub-step 7-1 complete

**Timeline**: 1-2 days

---

#### Sub-step 7-3: Advanced DOCX Features (Priority: MEDIUM)

**Goal**: Extract complex DOCX elements (tables, equations, images)

**Scope**:
- **Input**: Same as Sub-step 7-1
- **Output**: Enhanced JSON with tables/equations/figures sections
- **Sample size**: 40 TDocs with rich content

**Features**:
- OMML equation extraction → LaTeX conversion
- Table extraction with structure preservation (merged cells, styling)
- Image extraction (save to separate files, link in JSON)
- Caption extraction (Figure X, Table X captions)
- Equation token extraction (variable names for search)

**Dependencies**: Sub-step 7-1 complete

**Timeline**: 2-3 days

---

#### Sub-step 7-4: Full Scale Parsing (Priority: FINAL)

**Goal**: Parse all 119,565 TDoc folders with production-grade quality

**Scope**:
- **Input**: All folders in `data_transformed/meetings/RAN1/`
- **Output**: Complete `data_parsed/` dataset
- **Target**: 99%+ success rate

**Features**:
- Parallel processing (multi-core)
- Error handling (3-level fallback: full → basic → metadata-only)
- Checkpoint/resume (handle interruptions)
- Progress tracking (logs, statistics)
- Quality validation (schema compliance, completeness checks)
- Performance optimization (batch processing, caching)

**Dependencies**: Sub-steps 7-1, 7-2, 7-3 complete and validated on samples

**Timeline**: 2-3 days (parsing time) + 1 day (validation)

---

## Output Schema v2.0 (Layer-1) - Validated ✅

Based on validation of 25 diverse samples (2016-2025) in Step-6 Sub-step 6-2:

```json
{
  "tdoc_id": "R1-2500995",
  "meeting": "TSGR1_120",
  "location": "Athens, Greece",
  "date": "2024-02-17~2024-02-21",
  "agenda_item": "9.11.3",
  "source_company": ["Nokia", "Nokia Shanghai Bell"],
  "title": "Discussion of NR-NTN uplink capacity enhancements",
  "document_for": "Discussion and Decision",
  "work_item": "NR_NTN_Ph3",
  "release": "Rel-19",
  "sections": [
    {
      "name": "Discussion",
      "content": "<본문 텍스트>",
      "tables": [
        {
          "caption": "Table 5.2.1-1 CSI-RS configuration parameters",
          "rows": [["Parameter","Description"],["density","0.5"]],
          "summary": "Table describing Parameter and Description."
        }
      ],
      "figures": [
        {
          "caption": "Figure 5.2.1-1 Example of CSI-RS mapping",
          "keywords": ["CSI-RS","mapping","example"],
          "image_path": "fig_5_2_1_1.png"
        }
      ],
      "equations": [
        {
          "latex": "SINR = P_signal / (P_interference + N0)",
          "tokens": ["SINR","signal","interference","noise"]
        }
      ]
    }
  ],
  "proposals": [{"id":1,"text":"For inter-slot OCC …"}],
  "observations": [{"id":1,"text":"Excessive number of resources …"}],
  "agreements": [{"meeting_ref":"RAN1 #119","text":"Agreement on ..."}],
  "references": ["R1-2209970","RP-241667","TS 38.213"],
  "supplementary_data": {
    "pptx_files": [
      {
        "filename": "R1-2500995_WF.pptx",
        "slide_count": 15,
        "type": "Way Forward"
      }
    ],
    "xlsx_files": [
      {
        "filename": "R1-2500995_simulation_results.xlsx",
        "type": "simulation",
        "sheets": [
          {
            "name": "BLER_vs_SNR",
            "rows": 50,
            "columns": ["SNR (dB)", "BLER", "Throughput (Mbps)"],
            "data": [
              {"SNR": -5, "BLER": 0.5, "Throughput": 10.2}
            ]
          }
        ]
      }
    ]
  },
  "parsing_info": {
    "status": "success",
    "parser_version": "1.0.0",
    "layer": "Layer-1",
    "parsed_at": "2025-11-04T15:09:21",
    "transform_source": "step6"
  }
}
```

### Field Classification (Validation-Based)

**MUST HAVE** (90%+ coverage):
- `tdoc_id` (100%) - R1-XXXXXX pattern
- `location` (100%) - Meeting location
- `source_company` (94.4%) - Array of companies

**SHOULD HAVE** (60-89% coverage):
- `agenda_item` (88.9%) - Agenda number
- `title` (88.9%) - Document title
- `document_for` (83.3%) - Purpose

**OPTIONAL** (30-59% coverage):
- `proposals` (55.6%) - Proposal statements
- `release` (50.0%) - Rel-XX
- `observations` (33.3%) - Observation statements
- `agreements` (33.3%) - Agreement references

**RARE** (<30% coverage, inferred if missing):
- `meeting` (16.7%) - TSGR1_XXX (usually from file path)
- `date` (16.7%) - Date range (inconsistent format)
- `work_item` (11.1%) - WI code (recent docs only)

**Notes**:
- `meeting` and `date` can be inferred from file path if not in header
- `work_item` is a recent trend (2024+), not present in legacy docs
- `proposals`/`observations`/`agreements` are content-specific, not always present

---

## Parser 2-4: Other Document Types

### Parser 2: Report (Meeting Minutes)

**Status**: ⏳ PLANNED (After Docs parser complete)

**Characteristics**:
- Very large files (avg 1.02 MB, 10,191 paragraphs)
- Standard Heading1-6 styles
- Table of Contents (TOC)
- Many hyperlinks (2,000+)
- High equation/table/image count

**Challenges**:
- Memory management (chunk-based parsing)
- TOC extraction
- Complex navigation structure

**Timeline**: 3-4 days

---

### Parser 3: Change Requests

**Status**: ⏳ PLANNED (After Report parser complete)

**Characteristics**:
- Structured format (CR template)
- Change tracking (before/after)
- Specification references
- Approval status

**Timeline**: 2-3 days

---

### Parser 4: Specifications

**Status**: ⏳ PLANNED (After CR parser complete)

**Characteristics**:
- Highly structured (TS template)
- Deep section hierarchy (5.2.1.3.2)
- Many cross-references
- Version tracking

**Timeline**: 2-3 days

---

## Validation Strategy

### Sample-Based Testing

For each parser:
1. Select representative samples (15-20 documents for Docs, fewer for others)
2. Manual verification of key fields
3. Automated validation (schema, completeness)

### Success Metrics

| Metric | Target |
|--------|--------|
| TDoc number extraction | 99%+ |
| Metadata completeness | 90%+ |
| Text extraction | 100% |
| Reference extraction | 95%+ |
| JSON validity | 100% |

### Error Handling

- 3-level fallback (full → basic → metadata-only)
- Detailed error logging
- Failed documents tracked separately

---

## Timeline

### Sub-step 7-1: DOCX Basic Parser
| Task | Duration | Status |
|------|----------|--------|
| Develop metadata + text + reference extractor | 1-2 days | ⏳ Planned |
| Test on 50 samples | 0.5 days | ⏳ Planned |

### Sub-step 7-2: XLSX Integration
| Task | Duration | Status |
|------|----------|--------|
| Implement XLSX classification logic | 1 day | ⏳ Planned |
| Test on 30 multi-format folders | 0.5 days | ⏳ Planned |

### Sub-step 7-3: Advanced Features
| Task | Duration | Status |
|------|----------|--------|
| Add table/equation/image extraction | 2-3 days | ⏳ Planned |
| Test on 40 rich-content TDocs | 0.5 days | ⏳ Planned |

### Sub-step 7-4: Full Scale Parsing
| Task | Duration | Status |
|------|----------|--------|
| Implement parallel processing + error handling | 1 day | ⏳ Planned |
| Parse all 119,565 folders | 1-2 days | ⏳ Planned |
| Validate results | 1 day | ⏳ Planned |

### Other Parsers (After TDocs)
| Parser | Duration | Status |
|--------|----------|--------|
| **Report (Minutes)** | 3-4 days | ⏳ Planned |
| **Change Requests** | 2-3 days | ⏳ Planned |
| **Specifications** | 2-3 days | ⏳ Planned |

### Total Step-7 Timeline
- **Docs (TDocs)**: 6-10 days (Sub-steps 7-1 through 7-4)
- **All Document Types**: 14-22 days
- **Start Date**: After Step-6 Transform completes

---

## Dependencies

### Python Libraries

```bash
# Core parsing libraries
pip3 install python-docx python-pptx openpyxl pandas

# Optional utilities
pip3 install lxml mammoth Pillow
```

**Library Usage**:
- `python-docx`: DOCX parsing (metadata, text, tables, images)
- `python-pptx`: PPTX metadata extraction (slide count, title)
- `openpyxl`: XLSX parsing (Excel workbooks)
- `pandas`: XLSX data manipulation (for simulation results)
- `lxml`: XML processing (for OMML equations)
- `mammoth`: Fallback DOCX→HTML converter (if needed)
- `Pillow`: Image processing (for extracted figures)

---

## References

- **Step-5**: [Data Cleanup](./step5_data-cleanup-for-parsing.md)
- **Step-6**: [Data Transformation](./step6_data-transformation-for-parsing.md) (Prerequisites)
- **Input Data**: `data/data_transformed/meetings/RAN1/` (from Step-6)
- **Output Data**: `data/data_parsed/meetings/RAN1/`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-04
**Status**: Planned (waiting for Step-6 Transform to complete)

**Version History**:
- **v1.0** (2025-11-04): Created from original step6, focused on parsing implementation only
