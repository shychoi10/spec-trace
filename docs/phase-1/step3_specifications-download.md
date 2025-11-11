# Phase 1, Step 3: Download RAN1 Specifications

> **Quick Reference**: See [`data_raw/specs/RAN1/CLAUDE.md`](../../data_raw/specs/RAN1/CLAUDE.md) for spec list and download status

## Objective

3GPP FTP 서버에서 RAN1 NR 물리계층 스펙(38.201, 38.202, 38.211-215, 38.291)의 **최신 버전** 다운로드

**Scope**: 8개 스펙 (Tier 1-4 분류 적용)

## Source

**FTP URL**: `https://www.3gpp.org/ftp/specs/archive/38_series/`

**Structure**:
```
38_series/
├── 38.201/  (Tier 2)
├── 38.202/  (Tier 2)
├── 38.211/  (Tier 1) ← CORE
│   ├── 38211-f00.zip  (Rel-15 initial)
│   ├── 38211-g00.zip  (Rel-16 initial)
│   ├── ...
│   └── 38211-j10.zip  (Rel-19 latest) ← DOWNLOAD
├── 38.212/  (Tier 1) ← CORE
├── 38.213/  (Tier 1) ← CORE
├── 38.214/  (Tier 1) ← CORE
├── 38.215/  (Tier 1) ← CORE
└── 38.291/  (Tier 4)
```

## Target Specifications (Tier Classification)

### Tier 1: Core Standards (Priority: HIGHEST)
**설명**: 모든 기능의 기반이 되는 핵심 물리계층 표준

| Spec   | Title | Version | Size |
|--------|-------|---------|------|
| 38.211 | Physical channels and modulation | j10 (v19.1.0) | 1.2 MB |
| 38.212 | Multiplexing and channel coding | j10 (v19.1.0) | 2.1 MB |
| 38.213 | Physical layer procedures for control | j10 (v19.1.0) | 1.3 MB |
| 38.214 | Physical layer procedures for data | j10 (v19.1.0) | 3.0 MB |
| 38.215 | Physical layer measurements | j10 (v19.1.0) | 171 KB |

**Subtotal**: 5 specs, 7.9 MB

### Tier 2: Functional Standards (Priority: HIGH)
**설명**: 프로토콜 스택 및 인터페이스 정의

| Spec   | Title | Version | Size |
|--------|-------|---------|------|
| 38.201 | NR Physical layer - General description | j00 (v19.0.0) | 112 KB |
| 38.202 | NR Services provided by the physical layer | j00 (v19.0.0) | 1.0 MB |

**Subtotal**: 2 specs, 1.1 MB

### Tier 4: Special/Optional Features (Priority: LOW)
**설명**: 특수 사용 사례 또는 선택적 기능

| Spec   | Title | Version | Size |
|--------|-------|---------|------|
| 38.291 | NR Ambient IoT Physical layer | j10 (v19.1.0) | 178 KB |

**Subtotal**: 1 spec, 178 KB

**Total**: 8 specs, 9.2 MB

## Download Status

**Status**: ✅ COMPLETE (2025-11-05)

- **Total Specs**: 8/8 (100%)
- **Total Size**: 9.2 MB
- **Method**: Python requests (HTTP download)
- **Version Detection**: Auto-detected (alphabetic sort)
- **Download Time**: ~2 minutes (8 specs)
- **Latest Update**: Added Tier 2/4 specs (38.201, 38.202, 38.291)

## Output

```
data_raw/specs/RAN1/
├── CLAUDE.md
├── 38.201/  (Tier 2)
│   └── 38201-j00.zip  (112 KB)
├── 38.202/  (Tier 2)
│   └── 38202-j00.zip  (1.0 MB)
├── 38.211/  (Tier 1)
│   └── 38211-j10.zip  (1.2 MB)
├── 38.212/  (Tier 1)
│   └── 38212-j10.zip  (2.1 MB)
├── 38.213/  (Tier 1)
│   └── 38213-j10.zip  (1.3 MB)
├── 38.214/  (Tier 1)
│   └── 38214-j10.zip  (3.0 MB)
├── 38.215/  (Tier 1)
│   └── 38215-j10.zip  (171 KB)
├── 38.291/  (Tier 4)
│   └── 38291-j10.zip  (178 KB)
└── metadata/
    └── download_status.csv
```

## How to Download

### Prerequisites

**Required packages**:
```bash
pip3 install requests beautifulsoup4
```

**Note**: No aria2c needed! Python requests is sufficient for 8 small files.

---

### Single-Step Execution

Run the download script:

```bash
python3 scripts/phase-1/specs/RAN1/download_latest_specs.py
```

**What it does**:
1. For each spec (38.201, 38.202, 38.211-215, 38.291):
   - Fetch FTP directory listing
   - Extract all version codes
   - Sort alphabetically → latest version
2. Check if file already exists locally
3. Download missing files (requests library)
4. Verify downloads (file size > 0, ZIP integrity)
5. Save metadata to `download_status.csv`
6. Log results to `logs/phase-1/specs/RAN1/download.log`

**Output**:
- Downloaded files: `data_raw/specs/RAN1/38.XXX/38XXX-j10.zip`
- Metadata: `data_raw/specs/RAN1/metadata/download_status.csv`
- Log: `logs/phase-1/specs/RAN1/download.log`
- Time: ~1-2 minutes (depends on network speed)

---

## Technical Details

### 3GPP Version Encoding Scheme

**Format**: `XXXXX-VVV.zip` where VVV is a 3-character version code

**Version Code Structure**:
- **Position 1 (Major)**: Release indicator (letter)
- **Position 2 (Minor)**: Feature version (0-9, a-f in hex)
- **Position 3 (Patch)**: Editorial revision (0-9)

**Release Mapping**:
| Letter | Release | Example Versions |
|--------|---------|------------------|
| f | Rel-15 | f00 (v15.0.0), f10 (v15.1.0), fa0 (v15.10.0) |
| g | Rel-16 | g00 (v16.0.0), g10 (v16.1.0) |
| h | Rel-17 | h00 (v17.0.0), h90 (v17.9.0) |
| i | Rel-18 | i00 (v18.0.0), i70 (v18.7.0) |
| j | Rel-19 | j00 (v19.0.0), **j10 (v19.1.0)** ← Current |

**How It Works**:
- Version codes are **alphabetically sortable** by design
- Letter `j` > `i` > `h` > `g` > `f` (later releases first)
- Within same release: `j10` > `j00` (later minor version)
- **Latest version = Last item after alphabetic sort**

**Example**:
```python
versions = ['f00', 'g00', 'h00', 'i00', 'j00', 'j10']
latest = sorted(versions)[-1]  # 'j10'
```

### File Format

**Filename Pattern**: `38XXX-VVV.zip`
- Example: `38211-j10.zip`

**File Contents**: Each ZIP contains a single DOCX file
- `38211-j10.zip` → `38211-j10.docx` (unzipped)
- Format: Microsoft Word (.docx)
- Language: English
- File size: 170 KB ~ 3 MB per spec

**Total Versions Available** (as of 2025-11-05):
| Spec   | Tier | Total Versions | First | Latest |
|--------|------|----------------|-------|--------|
| 38.201 | 2    | 45 versions    | 000   | j00    |
| 38.202 | 2    | 102 versions   | 000   | j00    |
| 38.211 | 1    | 189 versions   | 000   | j10    |
| 38.212 | 1    | 198 versions   | 000   | j10    |
| 38.213 | 1    | 219 versions   | 000   | j10    |
| 38.214 | 1    | 231 versions   | 000   | j10    |
| 38.215 | 1    | 132 versions   | 000   | j10    |
| 38.291 | 4    | 15 versions    | 000   | j10    |

**Note**: We download ONLY the latest version per spec, not all 1,131 versions!

### Latest Version Auto-Detection

**Challenge**: How to programmatically find the latest version without hardcoding "j10"?

**Solution**: Fetch FTP directory HTML and parse version codes

```python
def get_latest_version(spec_num):
    url = f"https://www.3gpp.org/ftp/specs/archive/38_series/{spec_num}/"
    response = requests.get(url)

    # Extract version codes: 38211-XXX.zip
    pattern = f"38{spec_num.replace('.', '')}-([a-z0-9]{{3}})\\.zip"
    versions = re.findall(pattern, response.text)

    # Sort alphabetically and return last
    return sorted(versions)[-1]
```

**Advantage**: Works for future versions (j20, k00, etc.) without code changes!

### Why Python requests Instead of aria2c?

**Comparison**:
| Aspect | aria2c | Python requests |
|--------|--------|-----------------|
| **Speed** | Faster (multi-connection) | Slightly slower (single connection) |
| **Complexity** | Requires separate tool | Built-in Python |
| **Use Case** | Large-scale (100K+ files) | Small-scale (8 files) |
| **Setup** | `sudo apt install aria2` | `pip install requests` (already installed) |

**Decision**: Use Python requests for Step-3
- Only 8 files (~9.2 MB total)
- Download time: ~2 minutes (acceptable)
- Simpler code, fewer dependencies
- Consistent with portal crawling in Step-2

**When to use aria2c**: Step-1 (119K files), Step-2 (2.4K files)

### Download Verification

**Three-level verification**:

1. **HTTP Status Check**: `response.raise_for_status()`
2. **File Size Check**: Ensure `file_size > 0`
3. **ZIP Integrity Check**: `zipfile.ZipFile(path).testzip()`

**Example**:
```python
# Download
response = requests.get(url, stream=True)
response.raise_for_status()  # ← Check 1

# Save
with open(output_path, 'wb') as f:
    f.write(response.content)

# Verify size
if os.path.getsize(output_path) == 0:  # ← Check 2
    raise ValueError("Downloaded file is empty")

# Verify ZIP
with zipfile.ZipFile(output_path, 'r') as zf:
    if zf.testzip() is not None:  # ← Check 3
        raise ValueError("ZIP integrity check failed")
```

---

## Performance Statistics

**Overall**:
- **Total specs**: 8
- **Total size**: 9.2 MB
- **Download time**: ~2 minutes
- **Network**: ~4.6 MB/min average
- **Success rate**: 100% (8/8 specs)

**Per-Spec Breakdown** (latest run):
| Spec   | Tier | Size (KB) | Download Time | Versions Scanned |
|--------|------|-----------|---------------|------------------|
| 38.201 | 2    | 112       | ~11 sec       | 45               |
| 38.202 | 2    | 1,005     | ~34 sec       | 102              |
| 38.211 | 1    | 1,225     | (skipped)     | 189              |
| 38.212 | 1    | 2,082     | (skipped)     | 198              |
| 38.213 | 1    | 1,315     | (skipped)     | 219              |
| 38.214 | 1    | 3,059     | (skipped)     | 231              |
| 38.215 | 1    | 170       | (skipped)     | 132              |
| 38.291 | 4    | 178       | ~6 sec        | 15               |

**Time Breakdown** (incremental - 3 new specs):
- FTP listing + version detection: ~18 sec total (6 sec per new spec)
- HTTP download: ~51 sec total (17 sec per new spec)
- Verification: ~1 sec total
- **Total**: ~70 seconds (~1.2 minutes for 3 specs)

### Comparison with Previous Steps

| Metric | Step-1 (Meetings) | Step-2 (CRs) | Step-3 (Specs) |
|--------|-------------------|--------------|----------------|
| **Files** | 119,843 | 520 | **8** |
| **Size** | ~50+ GB | ~122 MB | **9.2 MB** |
| **Time** | ~2 hours | ~5 minutes | **~2 min** |
| **Method** | aria2c (必須) | aria2c (推薦) | **requests (충분)** |
| **Scripts** | 3 files | 5 files | **1 file** |
| **Complexity** | High | Medium | **Low** |

**Key Insight**: Step-3 is **60x faster** than Step-1 and **2.5x faster** than Step-2!

---

## Lessons Learned

### ✅ What Worked Well

1. **Auto-Detection Strategy**
   - No hardcoding of "j10"
   - Works for future versions automatically
   - Simple alphabetic sort is sufficient

2. **Single Script Approach**
   - No need for multi-step pipeline like Step-2
   - One command, one minute, done
   - Easy to understand and maintain

3. **Python requests Over aria2c**
   - Appropriate tool for small-scale downloads
   - Simpler dependencies
   - Adequate performance (9.2 MB in ~2 min)

4. **Spec-Level Directory Organization**
   - `38.211/`, `38.212/`, etc.
   - Easy to find specific spec
   - Supports future multi-version downloads

### 💡 Best Practices

1. **Version Synchronization**
   - Tier 1 (5 specs) and Tier 4 (1 spec) have same latest version (j10)
   - Tier 2 (2 specs) have latest version (j00)
   - This simplifies analysis (consistent release)
   - Script handles per-spec detection anyway

2. **Metadata Tracking**
   - `download_status.csv` records version + date + size
   - Enables future update detection
   - Easy to audit

3. **Verification is Essential**
   - Even 8 small files can fail
   - ZIP integrity check catches corruption
   - Better to fail early than proceed with bad data

### ⚠️ Considerations

1. **Future Version Updates**
   - Specs update every 3-6 months
   - Script auto-detects, but need to run manually
   - Consider cron job for periodic checks

2. **Historical Versions**
   - Currently download only latest (j10)
   - For version evolution analysis, may need:
     - f00 (Rel-15 initial)
     - g00 (Rel-16 initial)
     - ... etc
   - Easy to modify script for multi-version download

3. **File Storage Strategy**
   - ZIP format (original from FTP)
   - Could extract .docx automatically
   - Current choice: Keep ZIP only (save space, can extract later)

---

## Troubleshooting

### Issue: Download fails with 403 Forbidden

**Symptoms**: HTTP 403 error from FTP server

**Diagnosis**:
```bash
curl -I https://www.3gpp.org/ftp/specs/archive/38_series/38.211/38211-j10.zip
```

**Solutions**:
1. Check URL format (ensure correct spec number)
2. FTP server may be temporarily blocking requests
3. Add delay between requests (`time.sleep(2)`)
4. Use different User-Agent header

---

### Issue: ZIP integrity check fails

**Symptoms**: "ZIP integrity check failed" error

**Diagnosis**:
```bash
unzip -t data_raw/specs/RAN1/38.211/38211-j10.zip
```

**Solutions**:
1. Delete corrupted file: `rm data_raw/specs/RAN1/38.211/38211-j10.zip`
2. Re-run download script
3. If persistent, FTP server may have corrupt file (rare)

---

### Issue: "Version not found" error

**Symptoms**: Script fails to detect latest version

**Diagnosis**:
```bash
# Manually check FTP
curl https://www.3gpp.org/ftp/specs/archive/38_series/38.211/ | grep "38211-"
```

**Solutions**:
1. FTP server may be down
2. HTML format may have changed
3. Check regex pattern in `get_latest_version()`

---

### Issue: Download is too slow

**Symptoms**: Taking > 5 minutes for 9.2 MB

**Diagnosis**:
```bash
# Test network speed
curl -o /dev/null https://www.3gpp.org/ftp/specs/archive/38_series/38.211/38211-j10.zip
```

**Solutions**:
1. Check network connectivity
2. Use aria2c for faster download (modify script)
3. FTP server may be rate-limiting

---

## Advanced Usage

### Download Specific Version

Modify script to download a specific version instead of latest:

```python
# In download_latest_specs.py, replace:
version = get_latest_version(spec_num)

# With:
version = "i70"  # Rel-18 specific version
```

---

### Download Multiple Versions

To download one version per release:

```python
TARGET_VERSIONS = {
    "38.211": ["f00", "g00", "h00", "i00", "j00", "j10"],
    "38.212": ["f00", "g00", "h00", "i00", "j00", "j10"],
    # ... etc
}

for spec_num, versions in TARGET_VERSIONS.items():
    for version in versions:
        download_spec(spec_num, version)
```

---

### Extract DOCX Files

To automatically extract .docx from .zip:

```python
import zipfile

zip_path = "data_raw/specs/RAN1/38.211/38211-j10.zip"
extract_dir = "data_raw/specs/RAN1/38.211/"

with zipfile.ZipFile(zip_path, 'r') as zf:
    zf.extractall(extract_dir)

# Result: data_raw/specs/RAN1/38.211/38211-j10.docx
```

---

### Check for Updates

Create a script to check if new versions are available:

```python
#!/usr/bin/env python3
"""Check for spec updates"""

# Read current versions from metadata
current_versions = {}
with open("data_raw/specs/RAN1/metadata/download_status.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        current_versions[row['Spec']] = row['Version']

# Check latest versions on FTP
for spec_num in ["38.211", "38.212", "38.213", "38.214", "38.215"]:
    latest = get_latest_version(spec_num)
    current = current_versions.get(spec_num, "N/A")

    if latest != current:
        print(f"⚠ {spec_num}: {current} → {latest} (update available)")
    else:
        print(f"✓ {spec_num}: {current} (up to date)")
```

---

## Next Steps

After completing Step 3 (Specifications), proceed to Step 4 (Extraction)!

**Step-3 Summary**:
- Tier 1: 5 core specs (38.211-215, j10 v19.1.0) ✅
- Tier 2: 2 functional specs (38.201-202, j00 v19.0.0) ✅
- Tier 4: 1 special spec (38.291, j10 v19.1.0) ✅
- **Total**: 8 specifications, 9.2 MB

**Note on Additional Tiers**:
- This project currently focuses on **Tier 1** (38.211-215) for Change Requests
- Tier 2/4 specs downloaded for potential future use
- CR count for 38.201/202/291 unknown (not yet crawled from Portal)
- Decision on downloading additional CRs deferred until Step-7

**Next**: Step 4 - ZIP Extraction
- Extract all downloaded files
- Prepare for Step-5 (Data Cleanup)

---

## Related Documentation

- **Quick Reference**: [`data_raw/specs/RAN1/CLAUDE.md`](../../data_raw/specs/RAN1/CLAUDE.md)
- **Phase-1 Overview**: [`docs/phase-1/README.md`](README.md)
- **Step 1 (Meetings)**: [`docs/phase-1/step1_meetings-download.md`](step1_meetings-download.md)
- **Step 2 (CRs)**: [`docs/phase-1/step2_change-requests-download.md`](step2_change-requests-download.md)
- **Scripts**: `scripts/phase-1/specs/RAN1/`
- **Logs**: `logs/phase-1/specs/RAN1/`
