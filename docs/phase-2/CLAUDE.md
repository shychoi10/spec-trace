# Phase-2 구현 가이드

## 핵심 원칙

### 1. Spec 기준 개발

**모든 구현은 `Tdoc_parser_specs.md`를 기준으로 합니다.**

- 구현 전: Spec에서 해당 섹션 확인
- 구현 후: Spec과 일치하는지 검토
- 불일치 발견 시: 즉시 사용자에게 알림

### 2. Spec 수정 프로세스

**Spec 내용에 추가/수정이 필요한 경우:**

1. ❌ 임의로 수정하지 않음
2. ✅ 사용자에게 먼저 알림
3. ✅ 변경 사유와 제안 내용 설명
4. ✅ 사용자 승인 후 수정

### 3. 구현-Spec 불일치 발견 시

```
1. 작업 중단
2. 불일치 내용 정리
3. 사용자에게 보고:
   - Spec 정의 내용
   - 현재 구현 내용
   - 권장 조치 (Spec 수정 또는 구현 수정)
4. 사용자 결정에 따라 진행
```

---

## True Agentic AI 원칙 (Spec 1.3장)

### 핵심 정의

> **하드코딩 규칙 대신 LLM의 의미 이해 기반 처리**
> LLM이 문맥과 의미를 파악하여 스스로 판단

### ❌ 금지 사항

```python
# 하드코딩 규칙 기반 분류 (Spec 위반)
if "maintenance" in title.lower():
    return "Maintenance"
```

### ✅ 올바른 접근

```python
# LLM 의미 기반 분류 (Spec 준수)
prompt = """
섹션 제목에 'Maintenance' 패턴이 있으면 Maintenance일 가능성이 높다.
단, 제목의 전체 의미를 파악하여 최종 판단하라.
"""
result = llm.invoke(prompt)
```

### 적용 영역

| 영역 | 설명 |
|------|------|
| 섹션 경계 판단 | 페이지 번호가 아닌 title 의미로 판단 |
| Item 경계 판단 | 하나의 논의 흐름을 의미 단위로 구분 |
| Type 판단 | 섹션 번호가 아닌 **내용으로** Type 결정 |

### 교훈

#### 교훈 1: 규칙 vs LLM (2025-12-31)

**문제**: LLM 분류에서 unknown이 18% 발생
**잘못된 해결**: 규칙 기반 분류기로 대체 → Spec 위반
**올바른 해결**:
1. 프롬프트 품질 개선
2. 배치 처리로 응답 개수 문제 해결
3. LLM 기반 유지

> "당장의 문제 해결에 급급해서 원칙을 위반하면 기준이 무너진다"

#### 교훈 2: 응답 truncation vs Unknown (2025-12-31)

**문제**: LLM 배치 응답에서 일부 섹션 누락 (30개 요청 → 29개 응답)
**원인 분석**:
- Truncation: LLM이 출력 도중 끊김 → **인프라 문제** (role_2에서 재요청)
- Unknown: LLM이 의미적으로 판단 불가 → **도메인 문제** (role_3에서 2차 판단)

**해결**: Spec 4.2.8 배치 처리
- 응답 검증: 요청 수 = 응답 수 확인
- 누락 시 개별 재요청 (최대 2회)
- 처리 이력 `_processing`에 기록

**결과**: RAN1_120, RAN1_122 모두 unknown 0개 달성

---

## 참조 문서

| 문서 | 역할 |
|------|------|
| `Tdoc_parser_specs.md` | **Single Source of Truth** - 모든 구현의 기준 |
| `step1_*.md` ~ `stepN_*.md` | 각 Step별 구현 가이드 |
| `README.md` | Phase-2 개요 |

---

## 주요 Spec 섹션

| Spec 섹션 | 내용 | 관련 코드 |
|-----------|------|-----------|
| 4.0 | 전처리 (python-docx 변환) | `role_0_preprocess.py`, `docx_converter.py` |
| 4.1 | 메타데이터 추출 | `role_1_metadata.py` |
| 4.2 | TOC 파싱 | `role_2_toc.py` |
| 4.2.8 | 대용량 TOC 배치 처리 | `role_2_toc.py` (BATCH_SIZE, MAX_RETRY) |
| 5.x | Section Agent | `role_3_sections.py` |
| 6.x | 프롬프트 정의 | `prompts/*.py` |

---

## 체크리스트

### 코드 작성 전
- [ ] Spec에서 해당 기능 정의 확인
- [ ] 입력/출력 스키마 확인
- [ ] 에러 처리 방식 확인

### 코드 작성 후
- [ ] Spec 필드명과 일치하는지 확인
- [ ] Spec 스키마와 일치하는지 확인
- [ ] 불일치 있으면 사용자에게 보고

---

**Last Updated**: 2025-12-31
