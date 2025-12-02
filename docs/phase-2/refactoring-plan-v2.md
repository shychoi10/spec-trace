# LangGraph Multi-Agent System 리팩토링 계획 v2

## 현황 분석 (2024-12-01)

### 테스트 결과
| 항목 | 현재 출력 | Ground Truth | 달성률 |
|------|----------|--------------|--------|
| Primary Issues | 10개 | 19개 | 52.6% |
| CC-only Items | 0개 | 12개 | 0% |
| LS ID 정확도 | R1-24xxxxx | R1-25xxxxx | 0% |
| Tdocs 추출 | 0개 | 128개 | 0% |
| Issue Type 분류 | 전부 Non-action | 다양함 | ~30% |
| **종합 점수** | - | - | **30.4/100** |

### 식별된 핵심 문제 (우선순위 순)

---

## Phase 1: Critical Fixes (즉시 수행 필요)

### 1.1 BoundaryDetector 수정 [높음]

**문제**:
- `content[:15000]` 절단으로 문서 일부만 분석됨
- LLM 응답에 `start_idx`/`end_idx` 없음

**해결책**:
```python
# boundary_detector.py

# AS-IS (line 82)
prompt = f"""...
{content[:15000]}  # Truncate if too long
"""

# TO-BE: 청킹 방식으로 전체 문서 분석
def _detect_boundaries_chunked(self, content: str) -> list[dict]:
    """전체 문서를 청크 단위로 분석하여 모든 Issue 감지"""
    chunk_size = 12000
    overlap = 2000
    all_boundaries = []

    for i in range(0, len(content), chunk_size - overlap):
        chunk = content[i:i + chunk_size]
        boundaries = self._detect_in_chunk(chunk, offset=i)
        all_boundaries.extend(boundaries)

    return self._deduplicate_boundaries(all_boundaries)
```

**추가 수정**: LLM 프롬프트에서 `start_idx`, `end_idx` 반환 요청

### 1.2 MetadataExtractor JSON 파싱 안정화 [높음]

**문제**:
- LLM이 `list`를 반환할 때 `dict.get()` 호출 실패
- 6/10 Issue에서 에러 발생

**해결책**:
```python
# metadata_extractor.py

# AS-IS
data = parsed_json.get("ls_id", "unknown")

# TO-BE: 타입 체크 추가
def _safe_parse_response(self, response: str) -> dict:
    parsed = json.loads(response)

    # list인 경우 첫 번째 요소 사용
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else {}

    # dict가 아닌 경우 빈 dict 반환
    if not isinstance(parsed, dict):
        return {}

    return parsed
```

### 1.3 TdocLinker max_tokens 증가 [높음]

**문제**:
- `max_tokens=1500`으로 JSON 응답이 절단됨
- 10/10 재시도 모두 실패

**해결책**:
```python
# tdoc_linker.py

# AS-IS (line ~70)
response = self.llm.generate(prompt, temperature=0.2, max_tokens=1500)

# TO-BE: 토큰 수 증가 + streaming 고려
response = self.llm.generate(
    prompt,
    temperature=0.2,
    max_tokens=4000,  # 충분한 토큰 확보
    response_format={"type": "json_object"}  # JSON 모드 강제
)
```

**대안**: Tdoc 추출을 여러 번 나눠서 실행 (10개씩)

---

## Phase 2: Accuracy Improvements (정확도 개선)

### 2.1 LS ID 추출 정확도 [중간]

**문제**: R1-2500007이 R1-2400007로 잘못 추출됨

**해결책**: 프롬프트 개선 + 검증 로직
```python
# metadata_extractor.py 프롬프트 개선
prompt = f"""Extract the LS ID from this text.

IMPORTANT:
- RAN1 #120 meeting LS IDs start with R1-25xxxxx (year 2025)
- Format: R1-25NNNNN (7 digits after R1-)
- Do NOT confuse with R1-24xxxxx (year 2024)

Text:
{issue_text[:5000]}

Return JSON: {{"ls_id": "R1-25xxxxx"}}
"""
```

### 2.2 Issue Type 분류 개선 [중간]

**문제**: 모든 Issue가 "Non-action Issue"로 분류됨

**현재 상태**: `decision_classifier.py`에 이미 개선된 프롬프트가 있지만,
upstream 문제(MetadataExtractor 실패)로 인해 Issue 텍스트가 불완전

**해결책**:
1. Phase 1 수정 후 재테스트
2. 필요시 classification 예시 추가
```python
# 예시 추가
examples = """
Examples:
- "RAN1 response necessary" → Actionable Issue
- "No further action necessary" → Non-action Issue
- "To be taken into account" → Reference Issue
- "CC:" only mentioned → Reference Issue (CC-only)
"""
```

### 2.3 CC-only Items 처리 [중간]

**문제**: CC-only LS가 전혀 감지되지 않음 (Ground Truth: 12개)

**해결책**: BoundaryDetector에서 CC-only 항목 별도 감지
```python
# boundary_detector.py 프롬프트 수정
prompt = f"""
Identify ALL items in this Incoming LS section:

1. Primary LS Items: Items where RAN1 is the direct recipient
2. CC-only Items: Items where RAN1 is only CC'd (look for "CC:" mentions)

Return JSON:
{{
  "primary_items": [...],
  "cc_only_items": [...]
}}
"""
```

---

## Phase 3: Architecture Improvements (구조 개선)

### 3.1 에러 복구 메커니즘 강화

**현재**: 단순 try-except + 기본값 반환
**개선**: 재시도 + 대체 전략
```python
class RobustSubAgent:
    def process(self, state):
        for attempt in range(3):
            try:
                return self._try_process(state)
            except JSONDecodeError:
                # 프롬프트 단순화 후 재시도
                return self._simplified_process(state)
            except LLMError:
                # 대기 후 재시도
                time.sleep(2 ** attempt)

        return self._fallback_result(state)
```

### 3.2 진행 상황 추적 개선

**현재**: 로그만 출력
**개선**: 구조화된 메트릭 수집
```python
@dataclass
class ProcessingMetrics:
    total_issues: int
    successful_extractions: int
    failed_extractions: list[str]
    confidence_scores: list[float]
    processing_time: float
```

### 3.3 검증 스크립트 개선

**현재**: `validate_output.py`가 Ground Truth 형식 불일치
**개선**: Ground Truth 형식에 맞는 검증
```python
# validate_output.py 수정
def extract_key_info(text):
    info = {
        # Ground Truth는 "### **Issue:" 패턴 사용
        "issue_count": len(re.findall(r"^### \*\*Issue:", text, re.MULTILINE)),
        # LS ID 패턴도 수정
        "ls_ids": set(re.findall(r"R1-25\d{5}", text)),
        ...
    }
```

---

## 실행 계획

### Week 1: Phase 1 (Critical Fixes)
- [ ] Day 1-2: BoundaryDetector 청킹 구현
- [ ] Day 3: MetadataExtractor JSON 파싱 안정화
- [ ] Day 4: TdocLinker max_tokens 조정
- [ ] Day 5: 통합 테스트

### Week 2: Phase 2 (Accuracy)
- [ ] Day 1-2: LS ID 추출 정확도 개선
- [ ] Day 3: Issue Type 분류 검증
- [ ] Day 4-5: CC-only Items 처리

### Week 3: Phase 3 (Architecture)
- [ ] Day 1-2: 에러 복구 메커니즘
- [ ] Day 3: 메트릭 수집
- [ ] Day 4-5: 최종 검증 및 문서화

---

## 예상 목표

| 항목 | 현재 | Phase 1 후 | Phase 2 후 | 최종 목표 |
|------|------|-----------|-----------|----------|
| Primary Issues | 52.6% | 80% | 95% | 100% |
| CC-only Items | 0% | 0% | 80% | 95% |
| LS ID 정확도 | 0% | 90% | 100% | 100% |
| Tdocs 추출 | 0% | 70% | 90% | 95% |
| Issue Type | 30% | 60% | 85% | 95% |
| **종합 점수** | 30.4 | 70 | 85 | 95+ |

---

## 참고: True Agentic AI 원칙 준수

모든 수정 사항은 CLAUDE.md의 "True Agentic AI 원칙"을 준수합니다:
- ❌ Regex 사용 금지 (텍스트 분석용)
- ❌ 하드코딩 규칙 금지
- ✅ 모든 분석은 LLM 프롬프트로 처리
- ✅ JSON 파싱은 LLM 응답 구조화에만 사용
