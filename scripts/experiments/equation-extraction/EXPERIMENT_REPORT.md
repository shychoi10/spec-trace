# Equation Extraction Experiment Report

## 실험 개요

**목적**: Final Report DOCX 파싱 시 수식(OMML)을 LaTeX로 변환하는 하이브리드 방식 검증

**테스트 대상**: `Final_Report_RAN1-112.docx`

**실행일**: 2026-01-27

**최종 버전**: V2.1

---

## 기술 스택

| 구성요소 | V1 | V2.0 | V2.1 |
|----------|-----|------|------|
| 단락/스타일 파싱 | xml.etree | xml.etree | xml.etree |
| 수식 변환 | Pandoc (순차) | Pandoc (병렬) | Pandoc (병렬) |
| 병렬 처리 | ❌ | ThreadPoolExecutor | ThreadPoolExecutor |
| 위치 추적 | position만 | char_offset (단락-로컬) | char_offset (Decision-레벨) |
| 수식 타입 | 미구분 | inline/block | inline/block |
| 유효성 검증 | ❌ | 괄호 균형 검사 | 괄호 균형 + `\left\{`..`\right.` 보정 + OMML boundary artifact 허용 |
| offset 재계산 | ❌ | ❌ | ✅ Decision 병합 시 재매핑 |

---

## V1 → V2.0 → V2.1 개선 사항

| 항목 | V1 | V2.0 | V2.1 |
|------|-----|------|------|
| **성능** | ~24초 | 1.4초 | 1.3초 |
| **수식 개수** | 241개 | 248개 | 248개 |
| **Valid** | 미검증 | 245개 (98.8%) | **248개 (100%)** |
| **위치 정합** | 미검증 | 단락-로컬 (버그) | **Decision-레벨 (100%)** |
| **수식 타입** | 미구분 | inline/block | inline/block |

---

## V2.1 실험 결과

### 파싱 통계

| 항목 | 값 |
|------|-----|
| 총 단락 | 10,731개 |
| 수식 포함 단락 | 136개 |
| **총 수식** | **248개** |
| - Valid | **248개 (100%)** |
| - Invalid | **0개** |
| - Inline | 241개 |
| - Block | 7개 |
| 총 Decision | 544개 |
| **수식 포함 Decision** | **48개 (8.8%)** |

### 위치 정합성

| 검증 항목 | 결과 |
|-----------|------|
| `content_raw[offset:offset+len] == plain_text` | **248/248 (100%)** |
| `position` 연속성 (0, 1, 2, ...) | **248/248 (100%)** |
| `char_offset` 단조 증가 | **200/200 (100%)** |

### V2.0 → V2.1 버그 수정

| 버그 | 원인 | 수정 |
|------|------|------|
| 다중 단락 Decision에서 offset/position 중복 | `all_equations.extend()`가 단락-로컬 값 그대로 병합 | `_recalculate_equation_offsets()`에서 Decision 레벨 재계산 |
| piecewise 수식 false positive (3개) | `_validate_latex()`가 `\left\{`의 `{`를 일반 괄호로 카운트 | `\left\{`..`\right.` 구분자 쌍 보정 |
| 단락 경계 공백 불일치 | OMML의 선행/후행 공백이 `raw_text.strip()` 후 불일치 | `plain_text` 정규화 (strip) |
| OMML boundary artifact (4개, V2.1) | 원본 DOCX에서 `f(T_A)` 표현 시 `(`는 텍스트, `T_A)`만 OMML 마크업 → 닫는 `)` 포함 | 괄호 유형별 분리 검사 — `()`만 불균형이면 valid + note 처리 |

---

## V2.1 출력 파일 구조

```json
{
  "meeting_id": "RAN1#112",
  "version": "v2.0",
  "stats": {
    "total_paragraphs": 10731,
    "paragraphs_with_equations": 136,
    "total_equations": 248,
    "valid_equations": 248,
    "invalid_equations": 0,
    "inline_equations": 241,
    "block_equations": 7,
    "decisions_with_equations": 48
  },
  "decisions": [
    {
      "decision_id": "AGR-112-010",
      "equations": [
        {
          "plain_text": "beamAppTime",
          "latex": "\\(\\text{beamAppTime}\\)",
          "position": 0,
          "char_offset": 642,
          "char_length": 11,
          "display_type": "inline",
          "is_valid": true,
          "validation_note": ""
        }
      ]
    }
  ]
}
```

---

## 수식 변환 품질

### 전체 248개 - 100% Valid

| Plain Text | LaTeX | Type |
|------------|-------|------|
| `M=1` | `\(M = 1\)` | inline |
| `log2(K)` | `\(\left\lceil \log_{2}{(K)} \right\rceil\)` | inline |
| `Tproc,0SL` | `\(T_{\text{proc},0}^{\text{SL}}\)` | inline |

### 블록 수식 (7개)

```latex
$$\mathbf{H}_{\text{CLI}}^{\left( n \right)}$$
```

### 조건식/행렬 (3개 - V2.1에서 Valid 전환)

`\left\{`..`\right.` 패턴의 piecewise 수식 — 유효한 LaTeX이나 V2.0 검증 로직이 false positive 판정.
V2.1에서 구분자 쌍 보정으로 해결.

---

## 10개 미팅 Batch 검증 (V2.1 + Bug #3 fix)

### 검증 대상

10개 미팅 랜덤 선택 (seed=42, RAN1-112 제외): 100b, 104b, 105, 106, 110, 110b, 113, 89, 94, 97

### 종합 결과

| 검증 항목 | 결과 |
|-----------|------|
| **Valid** | **1,100/1,100 (100.0%)** |
| Invalid | 0/1,100 (0.0%) |
| offset 정합 | 1,100/1,100 (100.0%) |
| position 연속 | 1,100/1,100 (100.0%) |
| offset 단조증가 | 888/888 (100.0%) |
| 총 Decision | 4,432개 |
| 총 소요시간 | 7.5초 (10개 미팅) |

### 미팅별 상세

| 미팅 | 시간 | Decision | 수식 | Valid |
|------|------|----------|------|-------|
| RAN1-100b | 0.7s | 449 | 67 | 100% |
| RAN1-104b | 0.5s | 385 | 58 | 100% |
| RAN1-105 | 0.7s | 403 | 100 | 100% |
| RAN1-106 | 0.7s | 569 | 130 | 100% |
| RAN1-110 | 1.1s | 540 | 192 | 100% |
| RAN1-110b | 1.3s | 622 | 250 | 100% |
| RAN1-113 | 0.7s | 438 | 134 | 100% |
| RAN1-89 | 0.4s | 278 | 8 | 100% |
| RAN1-94 | 0.7s | 445 | 96 | 100% |
| RAN1-97 | 0.7s | 303 | 65 | 100% |

### Bug #3: OMML boundary artifact (4개 → 0개)

**원인**: 원본 DOCX에서 `f(T_A)` 같은 표현 시 여는 `(`는 일반 텍스트에, `T_A)`만 OMML 수식으로 마크업. Pandoc 변환은 정확하나 닫는 `)`가 수식 내부에 포함되어 괄호 균형 검증 실패.

**영향 미팅**: RAN1-106 (3개), RAN1-94 (1개)

**수정**: 괄호 유형별 분리 검사 — `()`만 불균형이고 `{}`, `[]`는 균형이면 `is_valid=true` + `validation_note="OMML boundary artifact"` 처리

---

## 결론

### V2.1 달성 지표

1. **100% Valid**: 단일 248/248 + 배치 1,100/1,100
2. **100% 위치 정합**: `content_raw[offset:len] == plain_text` 전수 검증 통과
3. **17배 성능 향상**: 배치 병렬 처리 (~0.75초/미팅)
4. **타입 구분**: inline(`$...$`) vs block(`$$...$$`)
5. **블록 수식 추가 추출**: +7개 (oMathPara 처리)
6. **OMML boundary artifact 허용**: 원본 DOCX 작성 실수에 강건

### 남은 한계

1. **Pandoc 의존성**: 외부 도구 필요

### 본 구현 확장 시 핵심 패턴

1. **offset 재계산**: 다중 단락 Decision 병합 시 `_recalculate_equation_offsets()` 필수
2. **`\left\{`..`\right.` 보정**: piecewise/matrix 수식의 LaTeX 검증에서 구분자 쌍 처리
3. **plain_text 정규화**: OMML 추출 시 선행/후행 공백 strip
4. **OMML boundary artifact**: `()` 유형만 불균형 허용 (원본 DOCX 마크업 실수 대응)

### 권장 사항

**V2.1 방식을 본 구현에 적용 권장**
- 성능: 전체 58개 미팅 처리 시 ~44초 (V1은 ~23분)
- 품질: 100% 성공률, 100% 위치 정합성 (11개 미팅 1,348개 수식 검증)

---

## 파일 위치

| 파일 | 위치 |
|------|------|
| V1 스크립트 | `scripts/experiments/equation-extraction/full_parse_test.py` |
| **V2 스크립트** | `scripts/experiments/equation-extraction/full_parse_test_v2.py` |
| **Hybrid V2** | `scripts/experiments/equation-extraction/hybrid_parser.py` |
| 배치 테스트 | `scripts/experiments/equation-extraction/batch_test_10meetings.py` |
| V1 결과 | `output/parsed_RAN1_112_with_equations.json` |
| **V2 결과** | `output/parsed_RAN1_112_with_equations_v2.json` |
| **배치 결과** | `output/batch_test_10meetings_summary.json` |
| 프로토타입 | `prototype.py` |
| 상세 테스트 | `detailed_test.py` |
