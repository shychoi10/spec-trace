# Step-3: 역할 1 메타데이터 추출 구현

## 목표

역할 1 노드를 구현하여 문서 헤더에서 회의 메타데이터를 추출하고 `meeting_info.yaml` 생성

**전략**: 정규식 우선, LLM fallback (비용 효율)

---

## 입력 (Step-2 출력)

- `state.markdown_content`: python-docx로 변환된 Markdown (서식 마커 포함)
- `state.toc_raw`: TOC 구조 리스트 (역할 2에서 사용)
- `state.meeting_id`: 회의 ID

---

## 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| 입력 | python-docx 변환 Markdown | 서식 마커 포함 |
| 1차 파싱 | 정규식 | 비용 0, 빠름 |
| 2차 파싱 | LLM (Gemini) | 누락 필드만 처리 |
| 스키마 | MeetingInfo (Pydantic) | 11개 필드 |
| 출력 | YAML | meeting_info.yaml |

---

## MeetingInfo 스키마

### 필수 필드 (7개)

| 필드 | 타입 | 예시 |
|------|------|------|
| source | str | "MCC Support" |
| document_type | str | "Final Minutes Report" |
| title | str | "Final Minutes report..." |
| date | str | "2025-02-17 – 2025-02-21" |
| meeting | str | "RAN1#120" |
| location | str | "Athens, Greece" |
| document_for | str | "Approval" |

### 선택 필드 (4개)

| 필드 | 타입 | 기본값 |
|------|------|--------|
| agenda_item | str | "" |
| version | str | "" |
| change_history | str | "" |
| toc_summary | str | "" |

---

## 구현 파일

| 파일 | 역할 |
|------|------|
| `src/models/meeting.py` | MeetingInfo 스키마 |
| `src/prompts/metadata_prompt.py` | LLM fallback 프롬프트 |
| `src/utils/metadata_parser.py` | 정규식 파싱 |
| `src/utils/llm_client.py` | LLM 클라이언트 |
| `src/pipeline/role_1_metadata.py` | LangGraph 노드 |

---

## 처리 흐름

```
state.markdown_content (python-docx 변환 결과)
    ↓
extract_header() - "Table of contents" 이전 영역 추출
    ↓
parse_metadata_regex() - 정규식 파싱
    ↓
누락 필드 있음?
    ├─ Yes → call_llm_for_metadata() → 병합
    └─ No → 직접 스키마 검증
    ↓
MeetingInfo 검증
    ↓
save_yaml() → meeting_info.yaml
```

> **Note**: python-docx 변환 결과에서 헤더 영역은 "Table of contents" 텍스트 이전까지의 내용입니다.

---

## 출력 예시 (RAN1_120)

```yaml
source: MCC Support
document_type: Final Minutes Report
title: Final Minutes report of meeting RAN1#120, Athens, Greece, 17-21 Feb
date: 2025-02-17 – 2025-02-21
meeting: RAN1#120
location: Athens, Greece
document_for: Approval
```

---

## 에러 처리

| 에러 | _error 구조 | 처리 |
|------|-------------|------|
| 헤더 추출 실패 | header_extraction_failed | 빈 meeting_info.yaml + _error |
| LLM 실패 | llm_fallback_failed | _warning 기록, 계속 진행 |
| 스키마 검증 실패 | validation_failed | 부분 데이터 + _error 저장 |

---

## 완료 조건

1. `metadata_node()` 함수 정상 동작
2. RAN1_120 메타데이터 추출 성공
3. `meeting_info.yaml` 파일 생성
4. 정규식으로 대부분 필드 추출 (LLM 호출 최소화)

---

## 다음 Step

- **Step-4**: 역할 2 TOC 파싱 노드 구현

---

**Last Updated**: 2025-12-30
**Status**: ✅ Complete
