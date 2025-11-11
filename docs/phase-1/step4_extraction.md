# Phase 1, Step 4: Extract Downloaded ZIP Files

> **Quick Reference**: See [`data/data_extracted/CLAUDE.md`](../../data/data_extracted/CLAUDE.md) for extraction summary

## Objective

다운로드된 ZIP 파일들을 압축 해제하여 분석 가능한 형태로 변환

## Overview

Phase-1에서 다운로드한 3가지 타입의 ZIP 파일들을 각각의 특성에 맞게 압축 해제:

```
Phase-1 Step-4 Sub-steps
├── Sub-step 4-1: Meetings Extraction        [✅ COMPLETE]
├── Sub-step 4-2: Change Requests Extraction [✅ COMPLETE]
└── Sub-step 4-3: Specifications Extraction  [✅ COMPLETE]
```

## Sub-steps

### Sub-step 4-1: Meetings Extraction

**Source**: `data/data_raw/meetings/RAN1/TSGR1_*/Docs/*.zip`

**Strategy**: 중첩 압축 해제 (nested extraction)
- 회의 문서는 ZIP 안에 ZIP이 중첩되어 있음
- 모든 최상위 ZIP 파일을 동일 이름의 폴더로 변환
- 디렉토리 구조 보존
- **중요**: TDoc 내부의 첨부 ZIP 파일(685개)은 **의도적으로 보존**
  - 이는 다른 TDoc을 참조/첨부한 파일
  - 메인 문서(DOC/DOCX)만 파싱 대상
  - Step-6에서 자동으로 제외됨

**Pattern**:
```
Input:  TSGR1_100/Docs/R1-200001.zip
Output: TSGR1_100/Docs/R1-200001/
        ├── R1-200001.docx         ← 메인 문서 (파싱 대상)
        └── R1-200002.zip          ← 첨부 파일 (보존, 파싱 제외)
```

**Results**:
- **ZIP Files Processed**: 119,760 / 119,743 (99.988%)
  - Initial extraction (2025-10-30): 119,687 ZIPs (99.90%)
  - First recovery with 7zip (2025-11-07): +44 ZIPs (50% recovery)
  - Advanced recovery (2025-11-10): +29 ZIPs (65.9% recovery)
- **Unrecoverable Failures**: 15 ZIPs (0.012%)
  - Empty archives: 11 ZIPs
  - Zero byte files: 4 ZIPs
- **Nested ZIP Files**: 685 files (첨부 파일, 의도적 보존)
- **Step-5 Cleanup**: 32 ZIPs (Report/Archive folders, intentional removal)
- **Output Size**: 42 GB
- **Processing Time**: 130 seconds (initial extraction)
- **Parallel Workers**: 8 threads

**Script**: `scripts/phase-1/meetings/RAN1/03_extract_meetings.py`

**Key Features**:
- Parallel processing with ThreadPoolExecutor
- Resume capability (skip already extracted)
- Corrupted ZIP handling (log and continue)
- Progress tracking with tqdm

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/meetings/RAN1/03_extract_meetings.py \
  --source data/data_raw/meetings/RAN1 \
  --dest data/data_extracted/meetings/RAN1 \
  --workers 8
```

---

### Sub-step 4-2: Change Requests Extraction

**Source**: `data/data_raw/change-requests/RAN1/Rel-*/TSG/*.zip`

**Strategy**: 단순 압축 해제 (flat extraction)
- 각 ZIP은 하나의 폴더로 변환
- 폴더 안에 여러 CR 문서들 (DOC/DOCX) 포함

**Pattern**:
```
Input:  Rel-19/TSG/RP-191281.zip
Output: Rel-19/TSG/RP-191281/
        ├── RP-191281.docx
        ├── R1-1234567.docx
        └── ...
```

**Results**:
- **ZIP Files Processed**: 520 / 520 (100%)
- **Corrupted ZIPs**: 0
- **Output Files**: ~3,000+ DOC/DOCX files
- **Output Size**: ~500 MB
- **Processing Time**: 1.1 seconds

**Script**: `scripts/phase-1/change-requests/RAN1/06_extract_change_requests.py`

**Key Features**:
- Parallel processing (8 workers)
- Resume capability
- Error logging

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/change-requests/RAN1/06_extract_change_requests.py \
  --source data/data_raw/change-requests/RAN1 \
  --dest data/data_extracted/change-requests/RAN1
```

---

### Sub-step 4-3: Specifications Extraction

**Source**: `data/data_raw/specs/RAN1/38.XXX/382XX-*.zip`

**Strategy**: 제자리 압축 해제 (in-place extraction)
- ZIP을 같은 디렉토리에 압축 해제
- 8개의 spec DOCX 파일 생성 (Tier 1+2+4)

**Pattern**:
```
Input:  38.211/38211-j10.zip
Output: 38.211/38211-j10.docx (same directory)
```

**Results**:
- **ZIP Files Processed**: 8 / 8 (100%)
- **Corrupted ZIPs**: 0
- **Output Files**: 8 DOCX/DOC files
- **Output Size**: 9.2 MB
- **Processing Time**: 0.2 seconds

**Script**: `scripts/phase-1/specs/RAN1/extract_specs.py`

**Key Features**:
- Simple sequential processing
- In-place extraction
- Minimal error handling needed

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/specs/RAN1/extract_specs.py
```

---

## Overall Results

**Extraction Summary**:

| Type | ZIPs | Success Rate | Recovered | Final Rate | Output Size | Time | Strategy |
|------|------|--------------|-----------|------------|-------------|------|----------|
| Meetings | 119,743 | 99.90% | +73 (2 phases) | **99.988%** | 42 GB | 130s | Nested (8 workers) |
| Change Requests | 520 | 100% | - | 100% | ~500 MB | 1.1s | Flat (8 workers) |
| Specifications | 8 | 100% | - | 100% | 9.2 MB | 0.2s | In-place (sequential) |
| **Total** | **120,271** | **99.90%** | **+73** | **99.988%** | **~42.5 GB** | **~132s** | - |

**Corrupted Files**:
- Initial failures: 88 ZIPs (empty folders after extraction)
- First recovery (2025-11-07): 44 ZIPs restored using 7zip (50% recovery rate)
- Advanced recovery (2025-11-10): 29 ZIPs restored (65.9% recovery rate)
- **Total recovered**: 73 ZIPs (82.9% of initially failed files)
- **Final unrecoverable**: 15 ZIPs (0.012% of total)
  - Empty archives: 11 ZIPs
  - Zero byte files: 4 ZIPs
- Step-5 cleanup: 32 ZIPs (Report/Archive folders, intentionally removed)
- All failures logged in `logs/phase-1/meetings/RAN1/advanced_recovery_report.json`
- Zero corruption in CRs and Specs

---

## Output Structure

```
data/data_extracted/
├── meetings/RAN1/
│   ├── TSGR1_84/
│   │   ├── Docs/
│   │   │   ├── R1-xxxx.zip      (original, kept)
│   │   │   ├── R1-xxxx/         (extracted)
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── Report/
│   │       └── ...
│   └── ...
│
├── change-requests/RAN1/
│   ├── Rel-15/TSG/
│   │   ├── RP-xxxxxx.zip        (original, kept)
│   │   ├── RP-xxxxxx/           (extracted)
│   │   │   ├── RP-xxxxxx.docx
│   │   │   └── R1-xxxxxxx.docx
│   │   └── ...
│   ├── Rel-16/TSG/...
│   ├── Rel-17/TSG/...
│   ├── Rel-18/TSG/...
│   └── Rel-19/TSG/...
│
└── specs/RAN1/
    ├── 38.201/
    │   └── 38201-j00.doc        (extracted)
    ├── 38.202/
    │   └── 38202-j00.docx
    ├── 38.211/
    │   └── 38211-j10.docx
    ├── 38.212/
    │   └── 38212-j10.docx
    ├── 38.213/
    │   └── 38213-j10.docx
    ├── 38.214/
    │   └── 38214-j10.docx
    ├── 38.215/
    │   └── 38215-j10.docx
    └── 38.291/
        └── 38291-j10.docx
```

**Note**:
- Meetings & CRs: Original ZIP files are **kept** alongside extracted folders
- Specs: Original ZIP files remain in `data_raw/specs/RAN1/` (in-place extraction)

---

## Logs

**Location**: `logs/phase-1/{meetings,change-requests,specs}/RAN1/`

**Essential Logs** (kept permanently):
- `verification.log` - Download verification results
- `extraction.log` - Extraction summary and errors

**Deleted Logs** (temporary, removed after completion):
- `aria2c_download_*.log` - Console output during download (13.2 MB)
- `download*.log` - Various download attempt logs (686 KB)
- `aria2c_input_*.txt` - Download list files (15 KB)
- `crawl*.log`, `generate*.log`, etc. - Development/debugging logs

**Cleanup Result**: `logs/` directory reduced from 15 MB → 64 KB (99.6% reduction)

---

## Performance Notes

### Meetings Extraction (Bottleneck)
- **Bottleneck**: I/O bound (reading/writing ZIPs)
- **Optimization**: 8 parallel workers
- **Throughput**: ~920 ZIPs/second
- **Memory**: Low (each worker extracts one ZIP at a time)

### Corrupted ZIP Handling
- **Strategy**: Skip and log, don't stop
- **Rate**: 79/119,766 = 0.07% (very low)
- **Impact**: Minimal (most are small files)

### Resume Capability
- All scripts support `--resume` flag
- Skip already extracted folders (check if folder exists and non-empty)
- Useful for interrupted extractions

---

## Recovery Process

### Sub-step 4-4: Failed ZIP Recovery (2025-11-07)

After initial extraction, verification revealed extraction failures requiring recovery.

#### Phase 1: Verification

**Script**: `scripts/phase-1/meetings/RAN1/05_verify_extraction.py`

Compared `data_raw` ZIPs against `data_extracted` folders:
- **Total ZIPs**: 119,743
- **Empty folders**: 88 (folders created but no files extracted)
- **Missing folders**: 32 (Report/Archive, removed in Step-5 cleanup)
- **Intentional cleanup**: 99 folders (Step-5 Archive removal)
- **True failures**: 120 ZIPs (88 empty + 32 missing)

**Log**: `logs/phase-1/meetings/RAN1/extraction_verification.json`

#### Phase 2: 7zip Recovery

**Script**: `scripts/phase-1/meetings/RAN1/06_recover_empty_zips.py`

Attempted recovery of 88 empty ZIP folders using 7zip:
- **Recovery attempts**: 88 ZIPs
- **Success**: 44 ZIPs (50% recovery rate)
- **Failed**: 44 ZIPs (unrecoverable)
- **Recovered files**: All in `Docs/` folders (TDoc documents)

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/meetings/RAN1/06_recover_empty_zips.py
```

**Log**: `logs/phase-1/meetings/RAN1/empty_zip_recovery_report.json`

#### Phase 3: Advanced Multi-tool Recovery (2025-11-10)

**Script**: `scripts/phase-1/meetings/RAN1/07_advanced_recovery.py`

Attempted recovery of remaining 44 failed ZIPs using advanced techniques:
- **Tool**: 7z (tolerant mode - return code 2 허용)
- **Recovery attempts**: 44 ZIPs
- **Success**: 29 ZIPs (65.9% recovery rate)
- **Failed**: 15 ZIPs (final unrecoverable)
- **Recovered files**: 35 files (including R1, R2, R4 TDocs)

**Recovery Breakdown**:
- Unexpected end of archive: 17/18 recovered (7z partial extraction)
- Unsupported compression (RAR): 9/9 recovered (7z handles RAR)
- Other: 3/3 recovered

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/meetings/RAN1/07_advanced_recovery.py
```

**Log**: `logs/phase-1/meetings/RAN1/advanced_recovery_report.json`

#### Phase 4: Final Results

**Final Success Rate**: **99.988%** (119,760 / 119,743)

**Total Recovery Summary**:
- Initial failures: 88 ZIPs
- Phase 2 recovered: 44 ZIPs (50%)
- Phase 3 recovered: 29 ZIPs (65.9%)
- **Total recovered**: 73 ZIPs (82.9%)

**Final Unrecoverable Files** (15 ZIPs, 0.012%):
- **Empty archives**: 11 files (ZIP structure valid, no content)
- **Zero byte files**: 4 files (download failures)

**Impact**: Negligible (0.012% of total documents)

---

## Troubleshooting

### Q: "Bad ZIP file" errors
**A**: Expected for some files. Logged but extraction continues. Check extraction.log for details.

### Q: Out of disk space
**A**: Need ~42 GB free space for meetings extraction. Check with `df -h` first.

### Q: Extraction taking too long
**A**: Increase workers with `--workers` flag (meetings only). Default is 8, try 16 if CPU allows.

### Q: Want to re-extract certain files
**A**: Delete the extracted folder and re-run with `--resume` flag. Only missing folders will be extracted.

---

## Next Steps

After Step-4 completion:

```
Phase-1 Progress: 🚧 86% (6/7 Steps Complete)
├── Step-1: Meetings Download            [✅ 100%]
├── Step-2: Change Requests Download     [✅ 100%]
├── Step-3: Specifications Download      [✅ 100%]
├── Step-4: Extraction                   [✅ 99.94%]
├── Step-5: Data Cleanup                 [✅ 100%]
├── Step-6: Data Transformation          [✅ 100%]
└── Step-7: Document Parsing (Layer-1)   [⏳ Planned]
```

**Proceed to**:
- **Step-5**: Data Cleanup for Parsing (already complete)
- **Step-6**: Data Transformation for Parsing (already complete)
- **Step-7**: Document Parsing (Layer-1) - ready to start

---

## References

- **Project Overview**: [docs/phase-1/README.md](README.md)
- **Progress Tracking**: [progress.md](../../progress.md)
- **Data Summary**: [data/data_extracted/CLAUDE.md](../../data/data_extracted/CLAUDE.md)
