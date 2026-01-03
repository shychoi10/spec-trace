# Step-2: Preprocess 노드 구현 (python-docx 변환)

## 목표

역할 0 (Preprocess) 노드를 구현하여 .docx Final Minutes Report를 서식 마커가 보존된 Markdown으로 변환한다.

**Step-2 목표**:
- `utils/docx_converter.py` 유틸리티 구현
- `role_0_preprocess.py` LangGraph 노드 구현
- TOC 구조를 `toc_raw.yaml`로 직접 추출
- 실제 RAN1 문서로 변환 테스트

---

## 기술 스택

| 항목 | 선택 | 비고 |
|------|------|------|
| 변환 도구 | **python-docx** | v1.1.0+ |
| 입력 | .docx | Final Minutes Report |
| 출력 | Markdown + YAML | 서식 마커 보존 |

> **왜 python-docx인가?**
> - pandoc은 Word 하이라이트를 `***text***`로 변환하여 Agreement 마커 인식 불가
> - python-docx는 `run.font.highlight_color` 접근으로 하이라이트 완전 보존
> - TOC를 Word 스타일(TOC 1, TOC 2, TOC 3)에서 직접 추출 가능

---

## 서식 변환 규칙 (명세서 4.0)

| Word 서식 | python-docx 속성 | Markdown 출력 |
|-----------|------------------|---------------|
| 하이라이트 | `run.font.highlight_color != None` | `[텍스트]{.mark}` |
| 볼드 | `run.bold == True` | `**텍스트**` |
| 이탤릭 | `run.italic == True` | `*텍스트*` |
| 밑줄 | `run.underline == True` | `<u>텍스트</u>` |
| 취소선 | `run.font.strike == True` | `~~텍스트~~` |
| 볼드+하이라이트 | 복합 | `[**텍스트**]{.mark}` |

### 우선순위

서식이 중첩된 경우 다음 순서로 적용:
1. `{.mark}` (하이라이트 - 최외곽)
2. `**bold**`
3. `*italic*`
4. `<u>underline</u>`
5. `~~strike~~`

예: 볼드+하이라이트 텍스트 → `[**Agreement reached**]{.mark}`

---

## 파일 구조

```
scripts/phase-2/langgraph-parser/
├── src/
│   ├── utils/
│   │   └── docx_converter.py      # python-docx 변환 유틸리티
│   │
│   └── pipeline/
│       └── role_0_preprocess.py   # LangGraph 노드
```

---

## utils/docx_converter.py 설계

### 핵심 함수

```python
def convert_docx_to_markdown(
    input_path: str,
    output_dir: str,
) -> tuple[str, dict]:
    """
    .docx 파일을 Markdown + TOC 구조로 변환 (Spec 4.0 준수)

    Args:
        input_path: .docx 파일 경로
        output_dir: 출력 디렉토리

    Returns:
        tuple[str, dict]: (markdown_content, toc_raw)
            - markdown_content: 서식 마커 포함 본문
            - toc_raw: Spec 4.0 toc_raw.yaml 구조 (entries 래퍼)
    """
```

### TOC 추출 로직

```python
def extract_toc_from_docx(doc: Document) -> dict:
    """Word 스타일에서 TOC 구조 직접 추출 (Spec 4.0 준수)

    TOC 스타일 매핑:
        - 'TOC 1' → depth: 1
        - 'TOC 2' → depth: 2
        - 'TOC 3' → depth: 3

    Returns:
        dict: Spec 4.0 toc_raw.yaml 구조
            - entries: TOC 항목 리스트
                - text: 원본 텍스트 (예: "9.1.1 MIMO 14")
                - style: Word 스타일명 (예: "TOC 1")
                - depth: 계층 깊이 (1-3)
                - page: 페이지 번호
                - anchor: 하이퍼링크 anchor
                - unnumbered: true (번호 없는 항목만)
    """
```

### Run 처리 로직

```python
def process_run(run) -> str:
    """개별 Run의 서식을 Markdown으로 변환

    서식 중첩 처리:
        1. 하이라이트 → [text]{.mark}
        2. 볼드 → **text**
        3. 이탤릭 → *text*
        4. 밑줄 → <u>text</u>
    """
    text = run.text
    if not text:
        return ""

    # 서식 적용 (안쪽에서 바깥쪽으로)
    if run.underline:
        text = f"<u>{text}</u>"
    if run.italic:
        text = f"*{text}*"
    if run.bold:
        text = f"**{text}**"
    if run.font.highlight_color is not None:
        text = f"[{text}]{{.mark}}"

    return text
```

---

## role_0_preprocess.py 설계

### LangGraph 노드 시그니처

```python
def preprocess_node(state: ParserState) -> dict:
    """
    역할 0: 문서 전처리 노드

    입력:
        state.input_path: .docx 파일 경로
        state.output_dir: 출력 디렉토리

    출력:
        markdown_content: 서식 마커 포함 본문
        toc_raw: TOC 구조 리스트
        meeting_id: 회의 ID
    """
```

### 처리 흐름

```
입력 (state.input_path)
    ↓
python-docx로 문서 로드
    ↓
TOC 추출 (Word 스타일 기반)
    ↓ toc_raw.yaml 저장
본문 변환 (서식 마커 적용)
    ↓ document.md 저장
meeting_id 추출 (파일명 기반)
    ↓
출력 (markdown_content, toc_raw, meeting_id)
```

---

## 출력 파일 구조

```
output/phase-2/langgraph-parser/
├── converted/                     # python-docx 변환 결과
│   └── {meeting_id}/
│       ├── document.md           # 서식 마커 포함 본문
│       ├── toc_raw.yaml          # TOC 구조 (직접 추출)
│       └── media/                # 추출된 이미지 (선택)
│
└── results/                      # 최종 파싱 결과
    └── {meeting_id}/
        ├── meeting_info.yaml
        ├── toc.yaml
        └── ...
```

### toc_raw.yaml 예시 (Spec 4.0 준수)

```yaml
entries:
  - text: "1 Opening of the meeting 5"
    style: "TOC 1"
    depth: 1
    page: 5
    anchor: "opening-of-the-meeting"
  - text: "1.1 Call for IPR 5"
    style: "TOC 2"
    depth: 2
    page: 5
    anchor: "call-for-ipr"
  - text: "8 Maintenance on Release 18 14"
    style: "TOC 1"
    depth: 1
    page: 14
    anchor: "maintenance-on-release-18"
  - text: "8.1 Maintenance on Rel-18 work items 14"
    style: "TOC 2"
    depth: 2
    page: 14
    anchor: "maintenance-on-rel-18-work-items"
  - text: "MIMO 14"
    style: "TOC 3"
    depth: 3
    page: 14
    anchor: "mimo"
    unnumbered: true
```

> **Note**: `unnumbered: true`인 항목은 번호 없는 하위 섹션 (Virtual Numbering 대상)

---

## document.md 예시

```markdown
# 1 Opening of the meeting

## 1.1 Call for IPR

The Chairman reminded the delegates about the IPR declaration process...

# 8 Maintenance on Release 18

## 8.1 Maintenance on Rel-18 work items

### MIMO

[**Agreement reached**]{.mark}

The CR was approved with modifications.

TDoc R1-2501234 was [**agreed**]{.mark} as a category F CR.
```

---

## meeting_id 추출 규칙

### 파일명 패턴

```
Final_Minutes_report_RAN1#120_v100.docx
                      ↓
                  RAN1_120
```

### 정규식

```python
pattern = r'RAN(\d+)#(\d+)'
# 또는
pattern = r'TSGR1_(\d+)'
```

### 예시

| 파일명 | meeting_id |
|--------|------------|
| Final_Minutes_report_RAN1#120_v100.docx | RAN1_120 |
| Final_Minutes_report_RAN1#119_v100.docx | RAN1_119 |
| TSGR1_118_FinalMinutes.docx | RAN1_118 |

---

## 에러 처리

| 에러 | 처리 방법 |
|------|-----------|
| python-docx 미설치 | ImportError + 설치 가이드 |
| 파일 없음 | FileNotFoundError |
| TOC 스타일 없음 | state.warnings에 기록 + 빈 toc_raw |
| 서식 변환 실패 | 해당 run 건너뛰기 + state.warnings |
| meeting_id 추출 실패 | state.warnings에 기록 + "unknown" 반환 |

---

## 완료 조건

1. `utils/docx_converter.py` 구현 완료
2. `role_0_preprocess.py` 구현 완료
3. RAN1 #120 문서 변환 테스트 성공
4. **하이라이트가 `[text]{.mark}` 형식으로 변환됨**
5. **toc_raw.yaml이 Word 스타일에서 정확히 추출됨**
6. state.markdown_content에 변환 결과 저장 확인
7. state.toc_raw에 TOC 구조 저장 확인
8. state.meeting_id 정상 추출 확인

---

## 테스트 체크리스트

```bash
# 1. 변환 테스트
PYTHONPATH=scripts/phase-2/langgraph-parser .venv/bin/python -c "
from src.utils.docx_converter import convert_docx_to_markdown
md, toc = convert_docx_to_markdown(
    'data/data_extracted/meetings/RAN1/TSGR1_120/Report/Final_Minutes_report_RAN1#120_v100.docx',
    'output/phase-2/langgraph-parser/converted/RAN1_120'
)
print(f'Markdown length: {len(md)} chars')
print(f'TOC entries: {len(toc)}')
"

# 2. 하이라이트 마커 확인
grep -o '\[.*\]{\.mark}' output/phase-2/langgraph-parser/converted/RAN1_120/document.md | head -5

# 3. toc_raw.yaml 확인
cat output/phase-2/langgraph-parser/converted/RAN1_120/toc_raw.yaml
```

---

## 다음 Step

- **Step-3**: 역할 1 메타데이터 추출 노드 구현

---

**Last Updated**: 2025-12-31
**Status**: ✅ Complete (Spec 4.0 준수)
