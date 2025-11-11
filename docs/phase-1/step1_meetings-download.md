# Phase 1, Step 1: Download RAN1 Meetings from 3GPP FTP

> **Quick Reference**: See [`data/data_raw/meetings/RAN1/CLAUDE.md`](../../data/data_raw/meetings/RAN1/CLAUDE.md) for meeting list (TSGR1_84 to TSGR1_122b)

## Objective

3GPP FTP 서버에서 RAN1 회의 자료 원본 파일들을 다운로드

## Source

**FTP URL**: `https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/`

**Structure**:
```
TSGR1_XXX/
├── Docs/           # Meeting documents (download)
├── Report/         # Meeting reports (download)
└── (others)        # Agenda, Invitation, LS, etc (skip)
```

## Target

**Meeting Range**: TSGR1_84 ~ TSGR1_122 (숫자 기준)
- 접미사 상관없이 모두 다운로드: `b`, `-e`, `_e`, `b-e`, `b_e` 등
- **Total**: 62 meetings

**Download Folders**: `Docs/`, `Report/` only
- 미러링: 폴더 구조 그대로 복사 (서브폴더 포함)
- 빈 폴더도 생성 (원본이 비어있는지 구분하기 위함)

## Download Status

**Status**: ✅ COMPLETE (2025-10-30)

- **Total Meetings**: 62/62 (100%)
- **Total Files**: 119,843 files
- **Method**: aria2c batch download
- **Verification**: URL-based comparison

## Output

```
data_raw/meetings/RAN1/
├── TSGR1_84/
│   ├── Docs/
│   └── Report/
├── TSGR1_84b/
│   ├── Docs/
│   └── Report/
...
└── TSGR1_122b/
    ├── Docs/
    └── Report/
```

## How to Download

### Prerequisites

Install aria2c:
```bash
sudo apt install -y aria2
```

### Step 1: Generate Download List

Scan FTP server and create list of missing files:

```bash
python3 scripts/phase-1/meetings/RAN1/01_generate_download_list.py
```

**What it does**:
- Reads target meeting list from `data/data_raw/meetings/RAN1/CLAUDE.md`
- Scans all 62 meetings on FTP recursively
- Compares with local files (URL-based, not file count)
- Generates `logs/phase-1/meetings/RAN1/aria2c_input.txt`

**Output**:
- aria2c input file: `logs/phase-1/meetings/RAN1/aria2c_input.txt`
- Time: ~30-40 minutes

### Step 2: Download with aria2c

Execute batch download:

```bash
python3 scripts/phase-1/meetings/RAN1/02_download_with_aria2c.py
```

**What it does**:
- Checks if aria2c is installed
- Validates aria2c_input.txt exists
- Runs aria2c with optimized settings
- Logs to `logs/phase-1/meetings/RAN1/aria2c_download.log`

**aria2c Settings** (optimized for speed + stability):
```
--max-connection-per-server=16    # 16 connections per server
--split=5                          # Split each file into 5 parts
--max-concurrent-downloads=20     # Download 20 files simultaneously
--continue=true                    # Resume on interruption
--allow-overwrite=false            # Never overwrite existing files
```

**Time**: Varies based on missing files
- Initial download (55,569 files): ~2 hours
- Incremental updates: minutes to hours

### Step 3: Verify Completion

Verify all files downloaded correctly:

```bash
python3 scripts/phase-1/meetings/RAN1/04_verify_status.py
```

**What it does**:
- Checks each meeting on FTP server
- Compares FTP file counts vs local
- Categorizes: COMPLETE / PARTIAL / MISSING
- Saves report to `logs/phase-1/meetings/RAN1/verification_complete.log`

**Time**: ~30-40 minutes

## Technical Approach

### Why aria2c?

**Previously tried**: Python urllib with ThreadPoolExecutor (5 workers)
- **Problem**: Too slow (~6-8 hours estimated)
- **Issue**: Single connection per file, limited parallelism

**Solution**: aria2c batch download
- **Multi-connection**: 16 connections per server = much faster
- **File splitting**: Each file split into 5 parts for parallel download
- **Batch processing**: 20 files downloaded concurrently
- **Auto-resume**: Interruptions automatically resume
- **Result**: 55,569 files in ~2 hours

### URL-Based Comparison

**Key Innovation**: Compare by URL, not file count

**Why**:
- File count heuristics (>=1000 files = complete) are unreliable
- Example: TSGR1_105-e showed 1,943 files locally, seemed "complete"
- Reality: FTP had 2,080 files → 137 missing (7%)

**Method**:
1. Extract all file URLs from FTP recursively
2. Convert URLs to relative paths
3. Check if each relative path exists locally
4. Missing paths = files to download

**Accuracy**: 100% - no false positives or negatives

## Performance Stats

### Final Results

| Metric | Value |
|--------|-------|
| Total Meetings | 62 |
| Total Files | 119,843 |
| Initial Local Files | 64,284 (54%) |
| Files Downloaded | 55,559 |
| Download Time | ~2 hours |
| Verification | 62/62 COMPLETE |

### Per-Meeting Examples

| Meeting | Docs | Report | Total | Status |
|---------|------|--------|-------|--------|
| TSGR1_90 | 3,239 | 3 | 3,242 | ✅ Largest |
| TSGR1_120b | 1,490 | 3 | 1,493 | ✅ Complete |
| TSGR1_100b | 0 | 0 | 0 | ✅ Empty (intentional) |

### Empty Meetings

Three meetings are intentionally empty on FTP:
- TSGR1_100b
- TSGR1_101
- TSGR1_102

## Scripts

All scripts located in `scripts/phase-1/meetings/RAN1/`:

1. **01_generate_download_list.py** - Create aria2c input file
   - Scans FTP for all files
   - Compares with local files
   - Generates download list

2. **02_download_with_aria2c.py** - Execute aria2c download
   - Validates prerequisites
   - Runs aria2c with optimal settings
   - Handles errors gracefully

3. **04_verify_status.py** - Verify completion
   - Checks FTP vs local for each meeting
   - Generates detailed report
   - Identifies any issues

## Lessons Learned

### What Worked

1. **aria2c >> urllib**: Much faster, more reliable
2. **URL comparison >> file counting**: 100% accurate
3. **Single unified script**: 01_generate_download_list.py does everything
4. **Zero-byte detection**: Catches partial/failed downloads

### What Didn't Work

1. **ThreadPoolExecutor (5 workers)**: Too slow for massive downloads
2. **File count heuristics**: Unreliable (false positives)
3. **Multiple small scripts**: Confusing, hard to maintain

### Best Practices

1. Always verify with FTP comparison, not assumptions
2. Use aria2c for large-scale downloads (multi-connection advantage)
3. URL-based comparison ensures accuracy
4. Keep scripts simple and well-documented
5. Save verification logs for future reference

## Troubleshooting

### Issue: aria2c not found
**Solution**: Install aria2c
```bash
sudo apt install -y aria2
```

### Issue: aria2c_input.txt not found
**Solution**: Run 01_generate_download_list.py first
```bash
python3 scripts/phase-1/meetings/RAN1/01_generate_download_list.py
```

### Issue: Download interrupted
**Solution**: Just re-run 02_download_with_aria2c.py
- aria2c automatically resumes from where it left off
- `--continue=true` flag handles this

### Issue: Verification shows PARTIAL
**Solution**: Re-generate download list and download again
```bash
python3 scripts/phase-1/meetings/RAN1/01_generate_download_list.py
python3 scripts/phase-1/meetings/RAN1/02_download_with_aria2c.py
```

## Logs

All logs stored in `logs/phase-1/meetings/RAN1/`:

- `aria2c_input.txt` (9MB) - Complete download list (URL + destination)
- `verification_complete.log` (9KB) - Final verification report
- `aria2c_download.log` (temporary) - aria2c detailed log (created during download)

## References

- Download spec: `data/data_raw/meetings/RAN1/CLAUDE.md`
- FTP source: https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/
- Local storage: `data_raw/meetings/RAN1/`
