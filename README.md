# spec-trace

3GPP RAN1 표준화 데이터 수집 및 분석 프로젝트

## 프로젝트 개요

3GPP RAN1 Working Group의 표준화 데이터를 수집, 정리, 분석:
- **Meetings**: 회의 자료 (TSGR1_84b ~ 122, 62 meetings)
- **Change Requests**: 표준 변경 요청 (Rel-15 ~ 19, 1,845 CRs)
- **Specifications**: NR 물리계층 표준 문서 (8 specs)

---

## 문서

| 문서 | 설명 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 프로젝트 규칙 + 용어 정의 |
| [progress.md](progress.md) | 진행 상황 (Single Source of Truth) |
| [docs/phase-1/README.md](docs/phase-1/README.md) | Phase-1 기술 가이드 |

---

## 데이터 구조

```
data/
├── data_raw/              # 원본 다운로드 (ZIP)
│   ├── meetings/RAN1/     (119,843 files)
│   ├── change-requests/   (520 files)
│   └── specs/RAN1/        (8 files)
│
├── data_extracted/        # 압축 해제 (~42 GB)
│   └── meetings/RAN1/     (129,718 files)
│
└── data_transformed/      # 변환 완료 (DOC→DOCX)
    └── meetings/RAN1/
```

---

## 현재 상태

- **Phase-1**: Data Collection & Preparation (100% 완료)
- **Phase-2**: DB Construction (Not Started)

자세한 진행 상황은 [progress.md](progress.md)를 참조하세요.

---

## 라이센스

이 저장소는 3GPP 데이터를 포함하며, 3GPP 저작권 정책을 따릅니다.
