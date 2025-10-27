# spec-trace

3GPP 표준 문서 및 회의 자료 데이터 저장소

## 데이터 구조

```
data/
├── change_requests/    # 3GPP Change Requests
│   └── RAN1/           # RAN1 Working Group
│       ├── Rel-17/     # Release 17
│       ├── Rel-18/     # Release 18
│       └── Rel-19/     # Release 19
├── meetings/           # 회의 자료
│   └── RAN1/           # RAN1 Working Group
│       └── TSGR1_*/    # 58개 미팅 (84b ~ 122)
└── specs/              # 표준 문서
    ├── RAN1/           # RAN1 표준 (38.211-38.215)
    └── RAN2/           # RAN2 표준 (38.321)
```

## 주의사항

- `data/` 디렉토리는 Git에 추적되지 않습니다 (용량이 큽니다)
- 로컬에서만 사용됩니다

## 라이센스

이 저장소는 3GPP 데이터를 포함하고 있으며, 3GPP의 저작권 정책을 따릅니다.
