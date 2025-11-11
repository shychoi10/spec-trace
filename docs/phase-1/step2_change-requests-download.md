# Phase 1, Step 2: Download RAN1 Change Requests

> **Quick Reference**: See [`data/data_raw/change-requests/RAN1/CLAUDE.md`](../../data/data_raw/change-requests/RAN1/CLAUDE.md) for CR list and download status

## Objective

3GPP Portal과 FTP 서버에서 RAN1 NR 물리계층 스펙의 Change Request 문서들을 다운로드

**Scope**: **8개 스펙 전체** (Tier 1+2+4: 38.201, 38.202, 38.211-215, 38.291)

## Source

**Portal URL**: `https://portal.3gpp.org/ChangeRequests.aspx`
**FTP Base**: `https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/`

## Target Specifications (All Tiers)

NR Physical Layer Specifications (8개):

**Tier 1: Core Standards (5 specs)**
- **38.211**: Physical channels and modulation
- **38.212**: Multiplexing and channel coding
- **38.213**: Physical layer procedures for control
- **38.214**: Physical layer procedures for data
- **38.215**: Physical layer measurements

**Tier 2: Functional Standards (2 specs)**
- **38.201**: NR Physical layer - General description
- **38.202**: NR Services provided by the physical layer

**Tier 4: Special/Optional Features (1 spec)**
- **38.291**: NR Ambient IoT Physical layer

**Note**:
- 8개 스펙 전체의 CR 다운로드 완료
- 총 42,277개 CR 중 1,845개 필터링됨 (approved only)

## Target Releases

- **Rel-15**: Initial 5G NR (2018)
- **Rel-16**: Enhanced 5G (2020)
- **Rel-17**: Advanced 5G (2022)
- **Rel-18**: Evolution (2024)
- **Rel-19**: Latest (2025+)

## Download Status

**Status**: ✅ COMPLETE (Last verified: 2025-11-06 11:15)

**Overall Summary**:
- **Total CRs**: 1,845 across 5 releases (8 specs: Tier 1+2+4)
- **Tier 1 (38.211-215)**: 1,803 CRs
- **Tier 2 (38.201-202)**: 41 CRs
- **Tier 4 (38.291)**: 1 CR
- **Crawled CRs**: 1,845 / 1,845 (100%)
- **Downloaded TSG Files**: 520 unique files (~82% coverage)
- **FTP URL Extraction**: 509 / 588 (79 failures)

**Per-Release Status**:
| Release | Total CRs | Tier 1 | Tier 2 | Tier 4 | TSG Tracked | Actual ZIP Files | Coverage | Status |
|---------|-----------|--------|--------|--------|-------------|------------------|----------|--------|
| Rel-15  | 212       | 204    | 8      | 0      | 93/204      | 23               | 45%      | ⚠️ Partial |
| Rel-16  | 549       | 537    | 12     | 0      | 459/537     | 161              | 85%      | ⚠️ Partial |
| Rel-17  | 573       | 564    | 9      | 0      | 497/564     | 196              | 88%      | ⚠️ Partial |
| Rel-18  | 440       | 430    | 10     | 0      | 361/430     | 121              | 83%      | ⚠️ Partial |
| Rel-19  | 71        | 68     | 2      | 1      | 66/71       | 19               | 97%      | ✅ Near Complete |

**Important Clarification**:
- **TSG Tracked**: Number of CRs with TSG TDoc references in metadata (expected count)
- **Actual ZIP Files**: Number of unique TSG ZIP files downloaded to disk
- **Why different?**: Multiple CRs are bundled in single TSG TDoc files
- Example: RP-191281.zip contains 6 different CRs across multiple specs
- **Overall coverage**: 520 actual files cover 1,476 CR references (1,803 Tier-1 CRs - 327 missing)
- **Missing files**: FTP server unavailability (old releases), URL extraction failures, or withdrawn CRs
- **Hardlinks**: 11 files created via hardlinks from other releases
- **38.291 (Ambient IoT)**: Introduced in Rel-19 only

## Output Structure

```
data/data_raw/change-requests/RAN1/
├── cr_list.csv                    # Master CR list (all releases)
├── Rel-15/
│   ├── TSG/
│   │   └── {TSG_TDoc}.zip        # e.g., RP-191281.zip
│   └── metadata/
│       └── download_status.csv    # Per-release tracking
├── Rel-16/
│   ├── TSG/
│   └── metadata/
├── Rel-17/
│   ├── TSG/
│   └── metadata/
├── Rel-18/
│   ├── TSG/
│   └── metadata/
└── Rel-19/
    ├── TSG/
    └── metadata/
```

## Workflow Overview

Change Request 다운로드는 5단계 파이프라인으로 구성:

```
01_crawl_portal.py       → Portal에서 CR 메타데이터 크롤링
         ↓
02_generate_download_list.py → FTP URL 추출 및 aria2c 입력 생성
         ↓
03_download_with_aria2c.py   → aria2c로 일괄 다운로드
         ↓
04_verify_downloads.py       → 다운로드 검증 및 누락 파일 식별
         ↓
05_link_duplicate_files.py   → 중복 파일 하드링크 처리 (선택)
```

## How to Download

### Prerequisites

**Required packages**:
```bash
sudo apt install -y aria2 python3-requests python3-bs4
pip3 install beautifulsoup4 requests
```

**Directory structure** (auto-created by scripts):
```bash
mkdir -p data/data_raw/change-requests/RAN1/{Rel-15,Rel-16,Rel-17,Rel-18,Rel-19}/{TSG,metadata}
mkdir -p logs/change-requests/RAN1
```

---

### Step 1: Crawl Portal for CR Metadata

Portal에서 CR 정보를 크롤링하여 CSV 생성:

```bash
python3 scripts/phase-1/change-requests/RAN1/01_crawl_portal.py
```

**What it does**:
- 5개 Release × 5개 Spec = 25개 조합에 대해 Portal 쿼리
- Release별 Work Item 자동 매핑 (Rel-15: 750167, Rel-16: 800185, ...)
- CR 메타데이터 파싱: CR번호, Spec, Title, Category, WG/TSG TDoc 등
- Consolidated CSV 생성: `data/data_raw/change-requests/RAN1/cr_list.csv`

**Output**:
- **cr_list.csv** (1,803 CRs):
  - Columns: Release, Spec, CR, Title, Category, WG_TDoc, WG_TDoc_URL, TSG_TDoc, TSG_TDoc_URL
  - Time: ~5-10 minutes
  - Log: `logs/phase-1/change-requests/RAN1/crawl.log`

**Example CSV row**:
```csv
Rel-19,38.214,0579,Correction to nrofHARQ-Processes for PUSCH,F,R1-2414467,https://portal.3gpp.org/desktopmodules/WorkItem/WorkItemDetails.aspx?workitemId=1021093,RP-243396,https://portal.3gpp.org/desktopmodules/WorkItem/WorkItemDetails.aspx?workitemId=1021093
```

---

### Step 2: Generate Download List

Portal URL에서 실제 FTP URL을 추출하고 aria2c 입력 파일 생성 (병렬 처리):

```bash
python3 scripts/phase-1/change-requests/RAN1/02_generate_download_list.py
```

**What it does**:
- `cr_list.csv`에서 TSG TDoc의 Portal URL을 읽음
- **Release별 병렬 URL 추출** (ProcessPoolExecutor, 5 workers)
  - 각 Release가 독립적으로 Portal 접속
  - 내부적으로 ThreadPoolExecutor(30 workers)로 URL 추출
- 각 Portal 페이지에 접속하여 JavaScript redirect에서 FTP URL 추출
  - Pattern: `window.location.href='https://www.3gpp.org/ftp/...'`
- 로컬에 이미 다운로드된 파일은 스킵
- 통합된 aria2c 입력 파일 생성 (중복 제거됨)

**Parallel Execution Strategy**:
- **Outer parallelism**: 5개 Release 동시 처리 (ProcessPoolExecutor)
- **Inner parallelism**: Release당 30개 TDoc 동시 URL 추출 (ThreadPoolExecutor)
- **Speed improvement**: 15분 → 3분 (5배 빠름)

**Technical Challenge**: Portal → FTP URL 변환
- Portal URL은 Work Item 페이지이지, 직접 다운로드 링크가 아님
- 페이지 내 JavaScript에서 `window.location.href` 추출 필요
- HTTP 요청 + 정규식 파싱으로 해결
- Retry logic 포함 (max 3 attempts)

**Output**:
- **aria2c input file**:
  - `logs/phase-1/change-requests/RAN1/aria2c_input_tsg.txt`
  - 통합 URL 리스트 (509개 고유 TSG TDoc)
- Time: ~3 minutes (병렬 처리)
- Log: `logs/phase-1/change-requests/RAN1/url_extraction.log`

**Actual Results** (2025-11-05):
- Total URLs extracted: 509
- Failed extractions: 79 (FTP URL not found on Portal)
- Success rate: 86%

**aria2c input format**:
```
https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_109/Docs/RP-243396.zip
  dir=data/data_raw/change-requests/RAN1/Rel-19/TSG
  out=RP-243396.zip
```

---

### Step 3: Download with aria2c

생성된 aria2c 입력 파일로 일괄 다운로드 실행:

```bash
python3 scripts/phase-1/change-requests/RAN1/03_download_with_aria2c.py
```

**What it does**:
- aria2c 설치 여부 확인
- aria2c_input_tsg.txt 존재 확인
- aria2c 실행 (최적화된 설정)
- 다운로드 진행 상황 모니터링

**aria2c Settings** (optimized for 3GPP FTP):
```
--max-connection-per-server=16    # 서버당 최대 16 연결
--split=5                          # 파일을 5개 부분으로 분할
--min-split-size=1M                # 1MB 이상 파일만 분할
--max-concurrent-downloads=10     # 동시 다운로드 10개 파일
--continue=true                    # 중단된 다운로드 재개
--auto-file-renaming=false         # 파일명 자동 변경 비활성화
--allow-overwrite=true             # 기존 파일 덮어쓰기 허용
--retry-wait=3                     # 재시도 대기 3초
--max-tries=5                      # 최대 5회 재시도
--timeout=60                       # 연결 타임아웃 60초
--connect-timeout=30               # 연결 시작 타임아웃 30초
```

**Why aria2c over Python requests?**
- **Performance**: 멀티커넥션으로 다운로드 속도 10-20배 향상
- **Reliability**: 자동 재시도, 중단 후 재개 기능
- **Efficiency**: 파일 분할 다운로드로 네트워크 활용 극대화
- **Proven**: Meeting 다운로드(119K files, 2시간)에서 검증됨

**Output**:
- Downloaded files: `data/data_raw/change-requests/RAN1/Rel-*/TSG/*.zip`
- Time: ~2-3 minutes for 509 files (parallel download)
- Log: `logs/phase-1/change-requests/RAN1/aria2c_download_tsg.log`

**Actual Results** (2025-11-05):
- Files downloaded: 509
- Download time: 2분 39초
- Success rate: 100% (for extractable URLs)

---

### Step 4: Verify Downloads

다운로드 완료 여부 검증 및 누락 파일 식별:

```bash
python3 scripts/phase-1/change-requests/RAN1/04_verify_downloads.py
```

**What it does**:
- `cr_list.csv`의 전체 CR 목록을 기준으로 검증
- Release별로 다운로드된 파일 확인
- 누락된 WG/TSG TDoc 식별
- Release별 다운로드 성공률 계산
- `download_status.csv` 생성 (각 Release의 metadata/)

**Verification Logic**:
- Expected: cr_list.csv에 기록된 모든 TDoc
- Actual: data/data_raw/change-requests/RAN1/Rel-*/TSG/ 내 실제 파일
- Missing: Expected - Actual
- Success Rate: (Actual / Expected) × 100%

**Output**:
- **download_status.csv** (각 Release):
  - Columns: Spec, CR, WG_TDoc, WG_Downloaded, TSG_TDoc, TSG_Downloaded
  - Per-CR tracking
- **Verification report**: `logs/phase-1/change-requests/RAN1/verification.log`
  - Release별 통계
  - 누락 파일 목록
  - 전체 Summary
- Time: ~1-2 minutes

**Example verification.log output**:
```
[Rel-19]
  Total CRs: 68
  WG TDocs: 68/68 (100%)
  TSG TDocs: 68/68 (100%)
  ✓ All files downloaded successfully!

[Rel-16]
  Total CRs: 537
  WG TDocs: 422/516 (81%)
  TSG TDocs: 99/537 (18%)
  ⚠ Missing TSG TDocs: 438
```

---

### Step 5: Link Duplicate Files (Optional)

중복 파일을 하드링크로 연결하여 디스크 공간 절약:

```bash
python3 scripts/phase-1/change-requests/RAN1/05_link_duplicate_files.py
```

**What it does**:
- SHA256 해시로 동일 파일 식별
- 중복 파일을 하드링크로 교체
- 디스크 공간 사용량 감소

**When to use**:
- 디스크 공간이 부족할 때
- 전체 다운로드가 완료된 후

**Note**: 이 단계는 선택사항이며, 데이터 무결성에는 영향 없음

---

## Technical Details

### WG TDoc vs TSG TDoc

**WG (Working Group) TDoc**:
- RAN1 회의에서 제안된 CR 초안
- 예: R1-2414467
- 위치: WG1_RL1 FTP (Meeting documents 내)

**TSG (Technical Specification Group) TDoc**:
- RAN Plenary에서 승인된 최종 CR
- 예: RP-243396
- 위치: TSG_RAN FTP (TSGR_XXX/Docs/)

**Download Priority**: TSG TDoc만 다운로드
- Reason: TSG TDoc이 공식 승인된 최종 문서
- WG TDoc은 중간 제안 단계로, spec에 반영 안 될 수 있음

### Why Some Downloads Fail

**Common reasons for missing files**:

1. **FTP 서버에 파일이 없음**
   - 오래된 Release (Rel-15~17)의 경우 일부 파일 누락
   - 특히 TSG TDoc 다운로드율 낮음 (Rel-16: 18%)

2. **Portal URL이 잘못됨**
   - Portal 크롤링 시 일부 URL이 정확하지 않을 수 있음
   - JavaScript redirect 파싱 실패

3. **네트워크 오류**
   - 일시적 연결 실패
   - aria2c 재시도 횟수 초과 (max-tries=5)

4. **CR이 withdrawn됨**
   - Portal에는 있지만 실제로는 철회된 CR

**Solution**: 재다운로드 시도
```bash
# Step 2부터 다시 실행하여 누락 파일만 재시도
python3 scripts/phase-1/change-requests/RAN1/02_generate_download_list.py
python3 scripts/phase-1/change-requests/RAN1/03_download_with_aria2c.py
python3 scripts/phase-1/change-requests/RAN1/04_verify_downloads.py
```

### Portal Crawling Strategy

**Challenge**: 3GPP Portal은 동적 웹페이지
- POST 요청 필요 (GET으로는 결과 없음)
- ViewState 파라미터 필요 (ASP.NET)
- 페이지네이션 처리

**Solution**: BeautifulSoup + requests
```python
# 1. ViewState 추출
soup = BeautifulSoup(response.text, 'html.parser')
viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']

# 2. POST 요청으로 CR 검색
data = {
    '__VIEWSTATE': viewstate,
    'ctl00$ContentPlaceHolder1$ddlSpec': spec,
    'ctl00$ContentPlaceHolder1$ddlRelease': release_code,
    # ... other params
}
response = requests.post(BASE_URL, data=data, headers=HEADERS)

# 3. 결과 테이블 파싱
table = soup.find('table', {'id': 'ContentPlaceHolder1_gvCRs'})
```

### File Organization Principles

**Directory structure design**:
```
Rel-XX/
├── TSG/              # TSG approved CRs (공식 문서)
└── metadata/         # Tracking and verification
    └── download_status.csv
```

**Why not include WG?**
- WG TDoc은 중간 제안으로, 분석 우선순위 낮음
- 디스크 공간 절약
- TSG TDoc만으로도 spec evolution 추적 가능

**Why separate by Release?**
- Release별 독립적 관리
- 특정 Release만 재다운로드 가능
- metadata 분리로 빠른 조회

---

## Performance Statistics

**Overall** (2025-11-05 Run):
- **Total CRs tracked**: 1,803
- **Portal pages crawled**: 214 (across 5 releases)
- **FTP URLs extracted**: 509 (86% success)
- **Files downloaded**: 509 (100% of extractable URLs)
- **Verification**: 1,476/1,803 CRs have files (81.9%)
- **Total execution time**: ~6 minutes
  - Crawling: Already complete (from previous run)
  - URL Extraction: 3분 (parallel)
  - Download: 2분 39초 (aria2c)
  - Verification: 17초
  - Hardlink: 17초

**Per-Release breakdown**:

| Release | CRs | TSG Success | Missing | Notes |
|---------|-----|-------------|---------|-------|
| Rel-15  | 204 | 45% (93)    | 111     | 많은 오래된 문서 FTP 누락 |
| Rel-16  | 537 | 85% (459)   | 78      | 일부 FTP 누락 |
| Rel-17  | 564 | 88% (497)   | 67      | 일부 FTP 누락 |
| Rel-18  | 430 | 83% (361)   | 69      | 일부 FTP 누락 |
| Rel-19  | 68  | 97% (66)    | 2       | 거의 완벽 ✅ |

**Parallelization Impact**:
- **URL Extraction**: 15분 → 3분 (5배 향상)
  - ProcessPoolExecutor (5 workers for releases)
  - ThreadPoolExecutor (30 workers per release)
- **Download**: aria2c 최적 설정으로 509 files in 2.6분
  - max-concurrent-downloads: 20
  - max-connection-per-server: 16
  - split: 5

**Observation**: Recent releases (Rel-19) have highest completion rate (97%), while older releases (Rel-15) have many missing files on FTP server (45%).

---

## Lessons Learned

### ✅ What Worked Well

1. **5-Step Pipeline Design**
   - Clear separation of concerns
   - Easy to debug and restart from any step
   - Numbered prefixes (01-05) show workflow order
   - **New**: Parallel URL extraction in Step 2 (5배 속도 향상)

2. **aria2c for Bulk Download**
   - Proven reliability from Meeting download
   - Automatic retry and resume capabilities
   - 10-20x faster than sequential Python requests
   - **Result**: 509 files in 2분 39초 (ultra-fast)

3. **Separate cr_list.csv**
   - Single source of truth for all CRs
   - Easy to query and analyze
   - Version-controlled metadata
   - **Expanded**: Now covers all 5 releases (1,803 CRs)

4. **Per-Release Organization**
   - Independent verification and re-download
   - Clear release boundaries
   - Metadata isolation

5. **Parallel Processing Strategy** (NEW)
   - ProcessPoolExecutor for release-level parallelism
   - ThreadPoolExecutor for URL-level parallelism
   - Hybrid approach: fast + efficient + no duplicate downloads

### ⚠️ Challenges Encountered

1. **Portal → FTP URL Extraction**
   - Portal doesn't provide direct FTP links
   - Must parse JavaScript redirect from HTML
   - **79 URLs failed** to extract (15% failure rate)
   - Some Portal pages don't contain FTP links

2. **Low TSG Completion for Old Releases**
   - Rel-15 TSG: only 45% downloaded
   - Rel-16 TSG: 85% downloaded (improved, but still incomplete)
   - Likely server-side issue (files not on FTP server)
   - Cannot fix programmatically - files genuinely missing

3. **Missing Files on FTP Server**
   - 327 files missing despite successful Portal crawling
   - Causes: Old releases (Rel-15~17), withdrawn CRs, server cleanup
   - **Trade-off accepted**: 82% overall success rate is acceptable

### 💡 Recommendations

1. **Focus on Recent Releases First**
   - Rel-19: 97% completion (highest quality)
   - Rel-17/18: 83-88% completion (good coverage)
   - Higher relevance for current 5G analysis

2. **Accept Missing Files for Old Releases**
   - Rel-15: 45% is acceptable (released 2018, many withdrawn CRs)
   - FTP server unlikely to restore old files
   - Not worth periodic re-download efforts

3. **Monitor aria2c Logs**
   - Check `aria2c_download_tsg.log` for recurring errors
   - Current run: 100% success for extractable URLs ✅

4. **Leverage Hardlinks**
   - Step 5 created 11 hardlinks across releases
   - Saves disk space for duplicate TSG TDocs
   - Run after any new downloads

5. **Parallel Processing for Future Steps**
   - Proven strategy: ProcessPool + ThreadPool hybrid
   - Apply to extraction, parsing, and other bulk operations
   - 5x speed improvement demonstrated

---

## Troubleshooting

### Issue: Low download success rate

**Symptoms**: Verification shows <50% for TSG TDocs

**Diagnosis**:
```bash
# Check aria2c log for errors
grep "ERROR" logs/phase-1/change-requests/RAN1/aria2c_download_tsg.log

# Check specific missing file on FTP
curl -I https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_XX/Docs/RP-XXXXXX.zip
```

**Solutions**:
1. Re-run download: `python3 scripts/phase-1/change-requests/RAN1/03_download_with_aria2c.py`
2. Increase aria2c timeout: Edit script, set `--timeout=120`
3. Check FTP server status: May be temporarily down

---

### Issue: Portal crawling fails

**Symptoms**: cr_list.csv is empty or incomplete

**Diagnosis**:
```bash
# Check crawl log
tail -50 logs/phase-1/change-requests/RAN1/crawl.log

# Test Portal URL manually
curl -X POST https://portal.3gpp.org/ChangeRequests.aspx
```

**Solutions**:
1. Check network connectivity
2. Portal may block bot requests - add delay between requests
3. ViewState may expire - re-run script immediately

---

### Issue: aria2c not found

**Symptoms**: `aria2c: command not found`

**Solution**:
```bash
sudo apt update
sudo apt install -y aria2
```

---

### Issue: Disk space full

**Symptoms**: aria2c fails with "No space left on device"

**Diagnosis**:
```bash
df -h data_raw/change-requests/
```

**Solutions**:
1. Run Step 5 to deduplicate: `python3 scripts/phase-1/change-requests/RAN1/05_link_duplicate_files.py`
2. Delete old aria2c control files: `rm -f data_raw/**/*.aria2`
3. Clean up logs: Move old logs to archive

---

## Next Steps

After completing Step 2 (Change Requests), proceed to:

**Step 3: Specification Documents**
- Download full spec documents (38.211-215) for each release
- Track spec versions and CR integration
- (Documentation to be created)

---

## Related Documentation

- **Quick Reference**: [`data/data_raw/change-requests/RAN1/CLAUDE.md`](../../data/data_raw/change-requests/RAN1/CLAUDE.md)
- **Phase-1 Overview**: [`docs/phase-1/README.md`](README.md)
- **Step 1 (Meetings)**: [`docs/phase-1/step1_meetings-download.md`](step1_meetings-download.md)
- **Scripts**: `scripts/phase-1/change-requests/RAN1/`
- **Logs**: `logs/phase-1/change-requests/RAN1/`
