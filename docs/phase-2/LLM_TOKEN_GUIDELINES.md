# LLM Token 설정 가이드라인

## 개요

이 문서는 Phase-2 LangGraph System에서 LLM 호출 시 `max_tokens` 설정에 대한 규칙을 정의합니다.

---

## 문제 배경

### 증상
- `JSONDecodeError: Unterminated string starting at...`
- `Expecting value: line 1 column 1 (char 0)` (빈 응답)
- LLM 응답이 중간에 잘림

### 원인
1. **max_tokens 부족**: 출력 크기 대비 토큰 한계가 낮음
2. **JSON 구조 오버헤드**: 실제 콘텐츠 외에 JSON 키, 중괄호 등 추가 토큰 필요
3. **토큰 ≠ 문자**: 1 토큰 ≈ 3-4자 (영어), JSON 특수문자는 토큰 소모 큼

---

## Token 계산 공식

```
필요 토큰 = (예상 출력 문자수 / 3) × 1.5 (안전 마진)
```

### 예시
- 20개 Issue × 1,500자/Issue = 30,000자
- 필요 토큰 = (30,000 / 3) × 1.5 = **15,000 토큰** (최소)
- JSON 오버헤드 포함 = **20,000+ 토큰** 권장

---

## Agent별 max_tokens 설정 규칙

### 1. BoundaryDetector (Incoming LS)
| 항목 | 값 |
|------|-----|
| 현재 설정 | 32,000 |
| **권장 설정** | **48,000** |
| 이유 | 20+ Issues × 1,500자 + JSON 오버헤드 |

### 2. MaintenanceBoundaryDetector
| 항목 | 값 |
|------|-----|
| 현재 설정 | 8,192 |
| **권장 설정** | **16,000** |
| 이유 | 10-40 Issues × 500자 + JSON 오버헤드 |

### 3. MetaSectionAgent
| 항목 | 값 |
|------|-----|
| 현재 설정 | 1,024 |
| 권장 설정 | 1,024 (유지) |
| 이유 | 단순 분류 결과 (~200자) |

### 4. SummaryGenerator
| 항목 | 값 |
|------|-----|
| 현재 설정 | 4,096 |
| 권장 설정 | 8,192 |
| 이유 | 요약 길이 가변적 |

### 5. DocumentParser (LLM Fallback)
| 항목 | 값 |
|------|-----|
| 현재 설정 | 16,000 |
| 권장 설정 | 16,000 (유지) |
| 이유 | 충분함 |

---

## max_tokens 설정 시 체크리스트

### 새 Agent 작성 시
- [ ] 예상 출력 크기 계산 (문자 수)
- [ ] Token 계산 공식 적용
- [ ] 최소 1.5x 안전 마진 확보
- [ ] JSON 출력이면 추가 30% 마진

### JSON 출력 특별 고려사항
```json
// JSON 오버헤드 예시
{
  "boundaries": [  // 이 구조 자체가 토큰 소모
    {
      "item_number": 1,  // 키 이름도 토큰
      "ls_id": "R1-2501234",
      ...
    }
  ]
}
```

**규칙**: JSON 출력은 일반 텍스트 대비 **+50% 토큰** 추가 할당

---

## 응답 잘림 방지 전략

### 1. Chunking 전략
긴 입력은 청크로 분할하여 처리:
```python
chunk_size = 15000  # 입력 청크
max_tokens = 8192   # 각 청크당 출력
```

### 2. 점진적 증가 전략
실패 시 토큰 증가 재시도:
```python
token_levels = [8192, 16000, 32000, 48000]
for max_tokens in token_levels:
    response = llm.generate(..., max_tokens=max_tokens)
    if is_complete(response):
        break
```

### 3. 응답 검증
```python
# finish_reason 체크
if finish_reason == 2:  # MAX_TOKENS
    logger.warning("응답 잘림 - 토큰 증가 필요")
    return retry_with_more_tokens()
```

---

## Gemini 2.5 Flash 제한사항

| 항목 | 값 |
|------|-----|
| 최대 입력 토큰 | 1,048,576 (1M) |
| 최대 출력 토큰 | 65,536 (65K) |
| 권장 출력 토큰 | 48,000 이하 |

**주의**: 65K 가까이 설정하면 불안정할 수 있음. 48K 이하 권장.

---

## 수정 필요 파일

### 즉시 수정 필요
1. `src/agents/sub_agents/boundary_detector.py`
   - Line 102: `max_tokens=32000` → `max_tokens=48000`

2. `src/agents/maintenance/maintenance_boundary_detector_agent.py`
   - Line 120: `max_tokens=8192` → `max_tokens=16000`
   - Line 214: `max_tokens=4096` → `max_tokens=8192`

---

## 모니터링

### 로그에서 확인할 항목
```
[Warning] 응답이 max_tokens에 의해 잘림 (finish_reason=MAX_TOKENS)
```

이 경고가 보이면 해당 Agent의 max_tokens 증가 필요.

---

*작성일: 2025-12-03*
*Phase-2 LangGraph System*
