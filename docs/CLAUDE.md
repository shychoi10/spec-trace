# Documentation Guide

이 문서는 `docs/` 폴더의 네비게이션 가이드입니다.

---

## 문서 구조

```
docs/
├── CLAUDE.md              # 이 파일 (네비게이션)
└── phase-1/
    ├── README.md          # Phase-1 종합 가이드 (권위 문서)
    ├── step1_meetings-download.md
    ├── step2_change-requests-download.md
    ├── step3_specifications-download.md
    ├── step4_extraction.md
    ├── step5_data-cleanup-for-parsing.md
    └── step6_data-transformation-for-parsing.md
```

---

## 빠른 링크

### 프로젝트 문서
- **프로젝트 규칙 + 용어**: [CLAUDE.md](../CLAUDE.md)
- **진행 상황**: [progress.md](../progress.md)
- **프로젝트 소개**: [README.md](../README.md)

### Phase-1 문서
- **Phase-1 종합 가이드**: [phase-1/README.md](phase-1/README.md)
- **Step-1 Meetings Download**: [phase-1/step1_meetings-download.md](phase-1/step1_meetings-download.md)
- **Step-2 Change Requests**: [phase-1/step2_change-requests-download.md](phase-1/step2_change-requests-download.md)
- **Step-3 Specifications**: [phase-1/step3_specifications-download.md](phase-1/step3_specifications-download.md)
- **Step-4 Extraction**: [phase-1/step4_extraction.md](phase-1/step4_extraction.md)
- **Step-5 Cleanup**: [phase-1/step5_data-cleanup-for-parsing.md](phase-1/step5_data-cleanup-for-parsing.md)
- **Step-6 Transformation**: [phase-1/step6_data-transformation-for-parsing.md](phase-1/step6_data-transformation-for-parsing.md)

### 데이터 Quick Reference
- **Meetings**: [data/data_raw/meetings/RAN1/CLAUDE.md](../data/data_raw/meetings/RAN1/CLAUDE.md)
- **Change Requests**: [data/data_raw/change-requests/RAN1/CLAUDE.md](../data/data_raw/change-requests/RAN1/CLAUDE.md)
- **Specifications**: [data/data_raw/specs/RAN1/CLAUDE.md](../data/data_raw/specs/RAN1/CLAUDE.md)
- **Extracted Data**: [data/data_extracted/CLAUDE.md](../data/data_extracted/CLAUDE.md)

---

## 문서 역할

| 파일 | 역할 |
|------|------|
| `CLAUDE.md` (루트) | 프로젝트 규칙 + 용어 정의 |
| `progress.md` | 진행 상황 (Single Source of Truth) |
| `docs/phase-1/README.md` | Phase-1 기술 문서 (권위 문서) |
| `data/*/CLAUDE.md` | 각 데이터 폴더의 Quick Reference |

---

**Last Updated**: 2025-12-04
