# Phase 1, Step 4: Extract Downloaded ZIP Files

> **Quick Reference**: See [`data/data_extracted/CLAUDE.md`](../../data/data_extracted/CLAUDE.md) for extraction summary

## Objective

다운로드된 ZIP 파일들을 압축 해제하여 분석 가능한 형태로 변환

## Overview

Phase-1에서 다운로드한 3가지 타입의 ZIP 파일들을 각각의 특성에 맞게 압축 해제:

```
Step-4 Extraction Workflow
├── 4a. Meetings Extraction        [✅ COMPLETE]
├── 4b. Change Requests Extraction [✅ COMPLETE]
└── 4c. Specifications Extraction  [✅ COMPLETE]
```

## Sub-steps

### 4a. Meetings Extraction

**Source**: `data/data_raw/meetings/RAN1/TSGR1_*/Docs/*.zip`

**Strategy**: 중첩 압축 해제 (nested extraction)
- 회의 문서는 ZIP 안에 ZIP이 중첩되어 있음
- 모든 ZIP 파일을 동일 이름의 폴더로 변환
- 디렉토리 구조 보존

**Pattern**:
```
Input:  TSGR1_100/Docs/R1-200001.zip
Output: TSGR1_100/Docs/R1-200001/
        └── (extracted contents)
```

**Results**:
- **ZIP Files Processed**: 119,687 / 119,766 (99.93%)
- **Corrupted ZIPs**: 79 (0.07%)
- **Output Size**: 42 GB
- **Processing Time**: 130 seconds
- **Parallel Workers**: 8 threads

**Script**: `scripts/phase-1/meetings/RAN1/extract_meetings.py`

**Key Features**:
- Parallel processing with ThreadPoolExecutor
- Resume capability (skip already extracted)
- Corrupted ZIP handling (log and continue)
- Progress tracking with tqdm

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/meetings/RAN1/extract_meetings.py \
  --source data/data_raw/meetings/RAN1 \
  --dest data/data_extracted/meetings/RAN1 \
  --workers 8
```

---

### 4b. Change Requests Extraction

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
- **ZIP Files Processed**: 105 / 105 (100%)
- **Corrupted ZIPs**: 0
- **Output Files**: 706 DOC/DOCX files
- **Output Size**: 122 MB
- **Processing Time**: 0.4 seconds

**Script**: `scripts/phase-1/change-requests/RAN1/extract_change_requests.py`

**Key Features**:
- Simple sequential processing (only 105 files)
- Resume capability
- Error logging

**Usage**:
```bash
cd /home/sihyeon/workspace/spec-trace
python3 scripts/phase-1/change-requests/RAN1/extract_change_requests.py \
  --source data/data_raw/change-requests/RAN1 \
  --dest data/data_extracted/change-requests/RAN1
```

---

### 4c. Specifications Extraction

**Source**: `data/data_raw/specs/RAN1/38.21[1-5]-j10.zip`

**Strategy**: 제자리 압축 해제 (in-place extraction)
- ZIP을 같은 디렉토리에 압축 해제
- 5개의 spec DOCX 파일만 생성됨

**Pattern**:
```
Input:  38.211-j10.zip
Output: 38.211-j10.docx (same directory)
```

**Results**:
- **ZIP Files Processed**: 5 / 5 (100%)
- **Corrupted ZIPs**: 0
- **Output Files**: 5 DOCX files
- **Output Size**: 9.9 MB
- **Processing Time**: 0.1 seconds

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

| Type | ZIPs | Success Rate | Output Size | Time | Strategy |
|------|------|--------------|-------------|------|----------|
| Meetings | 119,687 | 99.93% | 42 GB | 130s | Nested (8 workers) |
| Change Requests | 105 | 100% | 122 MB | 0.4s | Flat (sequential) |
| Specifications | 5 | 100% | 9.9 MB | 0.1s | In-place (sequential) |
| **Total** | **119,797** | **99.93%** | **~42 GB** | **~131s** | - |

**Corrupted Files**:
- Only 79 corrupted ZIPs found in meetings (0.07%)
- All corrupted files logged in `logs/phase-1/meetings/RAN1/extraction.log`
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
    ├── 38.211-j10.zip           (original, kept)
    ├── 38.211-j10.docx          (extracted)
    ├── 38.212-j10.zip
    ├── 38.212-j10.docx
    ├── 38.213-j10.zip
    ├── 38.213-j10.docx
    ├── 38.214-j10.zip
    ├── 38.214-j10.docx
    ├── 38.215-j10.zip
    └── 38.215-j10.docx
```

**Note**: Original ZIP files are **kept** for reference and potential re-extraction

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

After Step-4 completion, Phase-1 (Raw Data Download & Extraction) is complete:

```
Phase-1 Status: ✅ COMPLETE
├── Step-1: Meetings Download        [✅ 100%]
├── Step-2: Change Requests Download [✅ 100%]
├── Step-3: Specifications Download  [✅ 100%]
└── Step-4: Extraction               [✅ 99.93%]
```

**Proceed to Phase-2**: Data parsing and analysis
- Parse DOCX/DOC files
- Extract text and tables
- Build searchable database
- Cross-reference CRs with meeting documents

---

## References

- **Project Overview**: [docs/phase-1/README.md](README.md)
- **Progress Tracking**: [progress.md](../../progress.md)
- **Data Summary**: [data/data_extracted/CLAUDE.md](../../data/data_extracted/CLAUDE.md)
