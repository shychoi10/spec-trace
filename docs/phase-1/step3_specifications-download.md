# Phase 1, Step 3: Download RAN1 Specifications

> **Quick Reference**: See [`data_raw/specs/RAN1/CLAUDE.md`](../../data_raw/specs/RAN1/CLAUDE.md) for spec list and download status

## Objective

3GPP FTP 서버에서 RAN1 NR 물리계층 스펙(38.211-215)의 **최신 버전** 다운로드

## Source

**FTP URL**: `https://www.3gpp.org/ftp/specs/archive/38_series/`

**Structure**:
```
38_series/
├── 38.211/
│   ├── 38211-f00.zip  (Rel-15 initial)
│   ├── 38211-g00.zip  (Rel-16 initial)
│   ├── ...
│   └── 38211-j10.zip  (Rel-19 latest) ← DOWNLOAD
├── 38.212/
├── 38.213/
├── 38.214/
└── 38.215/
```

## Target Specifications

| Spec   | Title | Latest Version |
|--------|-------|----------------|
| 38.211 | Physical channels and modulation | j10 (v19.1.0) |
| 38.212 | Multiplexing and channel coding | j10 (v19.1.0) |
| 38.213 | Physical layer procedures for control | j10 (v19.1.0) |
| 38.214 | Physical layer procedures for data | j10 (v19.1.0) |
| 38.215 | Physical layer measurements | j10 (v19.1.0) |

**Total**: 5 files (~7.7 MB)

## Download Status

**Status**: ✅ COMPLETE (2025-10-30)

- **Total Specs**: 5/5 (100%)
- **Total Size**: 7.7 MB
- **Method**: Python requests (HTTP download)
- **Version Detection**: Auto-detected (alphabetic sort)
- **Download Time**: ~1.5 minutes

## Output

```
data_raw/specs/RAN1/
├── CLAUDE.md
├── 38.211/
│   └── 38211-j10.zip  (1.2 MB)
├── 38.212/
│   └── 38212-j10.zip  (2.1 MB)
├── 38.213/
│   └── 38213-j10.zip  (1.3 MB)
├── 38.214/
│   └── 38214-j10.zip  (3.0 MB)
├── 38.215/
│   └── 38215-j10.zip  (171 KB)
└── metadata/
    └── download_status.csv
```

## How to Download

### Prerequisites

**Required packages**:
```bash
pip3 install requests beautifulsoup4
```

**Note**: No aria2c needed! Python requests is sufficient for 5 small files.

---

### Single-Step Execution

Run the download script:

```bash
python3 scripts/specs/RAN1/download_latest_specs.py
```

**What it does**:
1. For each spec (38.211-215):
   - Fetch FTP directory listing
   - Extract all version codes
   - Sort alphabetically → latest version
2. Check if file already exists locally
3. Download missing files (requests library)
4. Verify downloads (file size > 0, ZIP integrity)
5. Save metadata to `download_status.csv`
6. Log results to `logs/specs/RAN1/download.log`

**Output**:
- Downloaded files: `data_raw/specs/RAN1/38.XXX/38XXX-j10.zip`
- Metadata: `data_raw/specs/RAN1/metadata/download_status.csv`
- Log: `logs/specs/RAN1/download.log`
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

**Total Versions Available** (as of 2025-10-30):
| Spec   | Total Versions | First | Latest |
|--------|----------------|-------|--------|
| 38.211 | 189 versions   | 000   | j10    |
| 38.212 | 198 versions   | 000   | j10    |
| 38.213 | 219 versions   | 000   | j10    |
| 38.214 | 231 versions   | 000   | j10    |
| 38.215 | 132 versions   | 000   | j10    |

**Note**: We download ONLY the latest version (j10), not all 969 versions!

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
| **Use Case** | Large-scale (100K+ files) | Small-scale (5 files) |
| **Setup** | `sudo apt install aria2` | `pip install requests` (already installed) |

**Decision**: Use Python requests for Step-3
- Only 5 files (~7.7 MB total)
- Download time: ~1-2 minutes (acceptable)
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
- **Total specs**: 5
- **Total size**: 7.7 MB
- **Download time**: ~1.5 minutes
- **Network**: ~5 MB/min average
- **Success rate**: 100% (5/5 specs)

**Per-Spec Breakdown**:
| Spec   | Size (KB) | Download Time | Versions Scanned |
|--------|-----------|---------------|------------------|
| 38.211 | 1,225     | ~13 sec       | 189              |
| 38.212 | 2,082     | ~13 sec       | 198              |
| 38.213 | 1,315     | ~16 sec       | 219              |
| 38.214 | 3,059     | ~35 sec       | 231              |
| 38.215 | 170       | ~2 sec        | 132              |

**Time Breakdown**:
- FTP listing + version detection: ~20 sec total (4 sec per spec)
- HTTP download: ~79 sec total (15.8 sec per spec)
- Verification: ~2 sec total
- **Total**: ~101 seconds (~1.7 minutes)

### Comparison with Previous Steps

| Metric | Step-1 (Meetings) | Step-2 (CRs) | Step-3 (Specs) |
|--------|-------------------|--------------|----------------|
| **Files** | 119,843 | 2,455 | **5** |
| **Size** | ~50+ GB | ~2-3 GB | **7.7 MB** |
| **Time** | ~2 hours | ~1-2 hours | **~1.5 min** |
| **Method** | aria2c (必須) | aria2c (推薦) | **requests (충분)** |
| **Scripts** | 3 files | 5 files | **1 file** |
| **Complexity** | High | Medium | **Low** |

**Key Insight**: Step-3 is **80x faster** than Step-1 and **40x faster** than Step-2!

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
   - Adequate performance (7.7 MB in 1.5 min)

4. **Spec-Level Directory Organization**
   - `38.211/`, `38.212/`, etc.
   - Easy to find specific spec
   - Supports future multi-version downloads

### 💡 Best Practices

1. **Version Synchronization**
   - All 5 specs have same latest version (j10)
   - This simplifies analysis (consistent release)
   - Script handles per-spec detection anyway

2. **Metadata Tracking**
   - `download_status.csv` records version + date + size
   - Enables future update detection
   - Easy to audit

3. **Verification is Essential**
   - Even 5 small files can fail
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

**Symptoms**: Taking > 5 minutes for 7.7 MB

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

After completing Step 3 (Specifications), Phase-1 is **100% COMPLETE**!

**Phase-1 Summary**:
- Step 1: 119,843 meeting documents ✅
- Step 2: 2,455 change requests ✅
- Step 3: 5 specifications ✅
- **Total**: 122,303 files downloaded

**Next**: Phase 2 - Data Parsing and Structuring
- Parse specification content (DOCX → structured data)
- Link CRs to spec sections
- Track spec evolution across releases
- Extract tables, figures, and equations

---

## Related Documentation

- **Quick Reference**: [`data_raw/specs/RAN1/CLAUDE.md`](../../data_raw/specs/RAN1/CLAUDE.md)
- **Phase-1 Overview**: [`docs/phase-1/README.md`](README.md)
- **Step 1 (Meetings)**: [`docs/phase-1/step1_meetings-download.md`](step1_meetings-download.md)
- **Step 2 (CRs)**: [`docs/phase-1/step2_change-requests-download.md`](step2_change-requests-download.md)
- **Scripts**: `scripts/specs/RAN1/`
- **Logs**: `logs/specs/RAN1/`
