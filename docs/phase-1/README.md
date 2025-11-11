# Phase 1: Raw Data Collection & Preparation

## 목표

3GPP RAN1 데이터 수집 및 파싱 준비:
- Raw data 다운로드 (Meetings, Change Requests, Specifications)
- ZIP 압축 해제
- 파싱 전 데이터 정리

## 데이터 소스

- **Meetings**: 3GPP FTP (TSGR1_84b ~ 122)
- **Change Requests**: 3GPP Portal + FTP (Rel-15 ~ 19)
- **Specifications**: 3GPP FTP (38.211-215, v.j10)

---

## Steps

| Step | 설명 | 상태 | 결과 |
|------|------|------|------|
| **[Step-1](./step1_meetings-download.md)** | Meetings Download | ✅ | 62 meetings, 119,843 files |
| **[Step-2](./step2_change-requests-download.md)** | Change Requests Download | ✅ | 1,845 CRs, 520 files, 82% coverage |
| **[Step-3](./step3_specifications-download.md)** | Specifications Download | ✅ | 8 specs, 9.2 MB |
| **[Step-4](./step4_extraction.md)** | ZIP Extraction | ✅ | 119,797 ZIPs → 42 GB |
| **[Step-5](./step5_data-cleanup-for-parsing.md)** | Data Cleanup for Parsing | ✅ | 59 meetings, 156 MB cleanup |
| **[Step-6](./step6_data-transformation-for-parsing.md)** | Data Transformation for Parsing | ✅ | Complete (All sub-steps done) |

**Phase-1 Status**: 🚧 **In Progress (86%)** - 6/7 Steps Complete
**Current**: Step-6 Complete, Step-7 Ready
**Next**: Step-7 Parsing → Phase-2 DB Construction

---

## 전체 결과

### 다운로드 완료 (Steps 1-3)

**Meetings** (Step-1):
- 62개 회의 (TSGR1_84b ~ 122)
- 119,843 files
- ~2 hours (aria2c)

**Change Requests** (Step-2):
- 1,845 CRs crawled (Rel-15 ~ 19, 5 releases)
- 520 TSG TDoc files downloaded (509 unique + 11 hardlinks)
- 1,476 CRs covered (80% success)
- All 8 specs (38.201-202, 38.211-215, 38.291)
- ~6 minutes (parallel URL extraction + aria2c)

**Specifications** (Step-3):
- 8 specs (Tier 1: 38.211-215, Tier 2: 38.201-202, Tier 4: 38.291)
- 9.2 MB
- Version j10 (Tier 1+4), j00 (Tier 2)
- ~2 minutes (Python requests)

### 압축 해제 완료 (Step-4)

**Overall**:
- 119,797 ZIPs 처리
- 130,430 files 추출
- 42 GB 총 용량
- 99.93% 성공률

**By Category**:
- Meetings: 119,687 ZIPs → 129,718 files (42 GB)
- Change Requests: 520 ZIPs → ~3,000 files (estimated)
- Specifications: 8 ZIPs → 8 files (9.2 MB)

### 데이터 정리 완료 (Step-5)

**Target**:
- System metadata: 40 MB (__MACOSX, .DS_Store)
- Report archives: 106 MB (Archive + Draft 버전들)
- Temp files: <1 MB (*.tmp, empty dirs)

**Total Cleanup**: 156 MB (완료)

**Result**:
- 59개 미팅 처리
- Archive 폴더: 0개 (100% 제거)
- 중복 Draft: 0개 (100% 제거)
- 깨끗한 구조: 58/59 미팅 (98.3%)

---

## 데이터 구조

### 최종 디렉토리 구조

```
data/
├── data_raw/              # Steps 1-3: 원본 다운로드
│   ├── meetings/RAN1/
│   │   └── TSGR1_XXX/
│   │       ├── Docs/      (ZIP files)
│   │       └── Report/    (ZIP files)
│   ├── change-requests/RAN1/
│   │   └── Rel-XX/TSG/    (ZIP files)
│   └── specs/RAN1/
│       └── 38.21X/        (ZIP files)
│
└── data_extracted/        # Step-4: 압축 해제 결과 (→ Step-5: Cleanup)
    ├── meetings/RAN1/     (129,718 files, 42 GB)
    │   └── TSGR1_XXX/
    │       ├── Docs/
    │       │   └── R1-XXXXXXX/
    │       │       └── *.doc(x)
    │       └── Report/
    │           └── Final_Minutes_*/
    ├── change-requests/RAN1/ (706 files, 122 MB)
    │   └── Rel-XX/TSG/
    │       └── RP-XXXXXX/
    │           └── 38.21X_CR*.doc(x)
    └── specs/RAN1/        (5 files, 9.9 MB)
        └── 38.21X/
            └── 382XX-j10.docx
```

### 파일 형식 분포 (data_extracted)

| 형식 | 개수 | 비율 | 파싱 여부 |
|------|------|------|----------|
| DOCX | 97,598 | 74.8% | ✅ Primary |
| DOC | 23,434 | 18.0% | ✅ Primary |
| PPTX/PPT | 4,215 | 3.3% | 🔶 Optional |
| XLSX | 2,665 | 2.0% | 🔶 Optional |
| ZIP | 685 | 0.5% | ❌ Skip |
| PDF | 290 | 0.2% | ✅ Secondary |
| 기타 | 1,543 | 1.2% | ❌ Skip |

**파싱 타겟**: DOC/DOCX (121,032 files, 92.8%)

---

## 문서 구조

각 Step은 동일한 4가지 구성 요소를 가짐:

1. **상세 가이드** (`docs/phase-1/stepN_*.md`)
   - 완전한 기술 문서 (Single Source of Truth)
   - 다운로드/추출/정리 절차
   - 성능 분석, Troubleshooting

2. **빠른 참조** (`data/data_raw/*/RAN1/CLAUDE.md`)
   - 타겟 목록 (meetings/CRs/specs)
   - 현재 상태, 빠른 명령어
   - 상세 가이드 참조 링크

3. **실행 스크립트** (`scripts/phase-1/*/RAN1/`)
   - Python 실행 스크립트
   - 다단계 워크플로우는 번호 prefix (01-05)

4. **작업 로그** (`logs/phase-1/*/RAN1/`)
   - 실행 로그, 검증 리포트
   - aria2c 입력 파일, 통계

---

## 워크플로우 패턴

### Download Pattern (Steps 1-3)

```
1. List Generation  → 2. Download  → 3. Verification
   (FTP/Portal)        (aria2c/requests)  (checksums)
```

### Extraction Pattern (Step-4)

```
1. Find ZIPs  → 2. Extract  → 3. Verify  → 4. Cleanup
   (find)        (unzip)       (count)      (metadata)
```

### Cleanup Pattern (Step-5)

```
1. Analyze  → 2. Categorize  → 3. Remove  → 4. Verify
   (find)       (risk assess)    (rm -rf)    (check)
```

---

## 기술 스택

### 필수 도구

**System packages**:
```bash
sudo apt install -y aria2 python3-requests python3-bs4
```

**Python packages**:
```bash
pip3 install requests beautifulsoup4
```

### 사용 도구

- **aria2c**: 대용량 배치 다운로드 (Steps 1-2)
- **Python requests**: 소규모 다운로드 (Step-3)
- **BeautifulSoup4**: 3GPP Portal HTML 파싱 (Step-2)
- **unzip**: ZIP 압축 해제 (Step-4)

---

## 성능 요약

| Step | 작업 | 파일 수 | 시간 | 방법 | 성공률 |
|------|------|---------|------|------|--------|
| 1 | Meetings DL | 119,843 | 2h | aria2c | 100% |
| 2 | CRs DL | 520 files | 1-2h | Portal+aria2c | 100% |
| 3 | Specs DL | 8 specs | 1.5min | requests | 100% |
| 4 | Extraction | 119,797 ZIPs | 2-3min | unzip (8 threads) | 99.93% |
| 5 | Cleanup | 5,000+ items | ~10min | rm+find | 100% |
| 6 | Transform | 23,413 DOCs | 1-2h | LibreOffice (8 workers) | ~99% |

**Total Time**: ~5-6 hours (Steps 1-6)

---

## 다음 단계

### Phase-2: Data Parsing

**Input**: 깨끗한 `data_extracted` (Step-5 완료 ✅)

**Tasks**:
1. DOC/DOCX 파싱 (121,032 files)
2. 메타데이터 추출 (TDoc 번호, 제목, 저자)
3. 텍스트 추출 및 구조화
4. 데이터베이스 적재

**Status**: Ready to start
**Document**: [Phase-2 README](../phase-2/README.md)

---

## 참고 문서

### 프로젝트 문서
- **프로젝트 개요**: [CLAUDE.md](../../CLAUDE.md)
- **진행 상황**: [progress.md](../../progress.md)
- **README**: [README.md](../../README.md)

### Phase-1 상세 문서
- [Step-1: Meetings Download](./step1_meetings-download.md)
- [Step-2: Change Requests Download](./step2_change-requests-download.md)
- [Step-3: Specifications Download](./step3_specifications-download.md)
- [Step-4: ZIP Extraction](./step4_extraction.md)
- [Step-5: Data Cleanup for Parsing](./step5_data-cleanup-for-parsing.md)

### 외부 리소스
- 3GPP FTP Server: `ftp://ftp.3gpp.org/`
- 3GPP Portal: `https://www.3gpp.org/ftp/`

---

**Last Updated**: 2025-11-11
**Phase-1 Status**: 6/7 Steps Complete (86%) - Step-7 Ready
