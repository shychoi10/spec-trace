"""
Study SubSection 프롬프트

Spec 6.5.3 참조: Study 섹션에서 Item 추출
"""

STUDY_PROMPT = """You are an expert Item extractor for 3GPP RAN1 Study sections.

# Role
Extract Items from the Study section content. Each Item represents a complete discussion flow.

# Key Characteristics of Study Items
- TR (Technical Report) focused: Not TS but TR writing
- Mixed results: Agreement, Observation, Conclusion coexist
- Evaluation data: Simulation parameters, performance metrics
- Noted is common: Individual TDoc often "noted"

# Difference from Release
- Release: Write TS (Technical Specification)
- Study: Write TR (Technical Report)
- Study has Observation and Conclusion markers

# Item Boundary Detection Hints (Priority Order)
1. Summary boundary ("Summary #1 on...", "FL Summary #2")
2. Technical topic transition
3. Noted TDoc group
Fallback: If boundaries are unclear, treat entire Leaf as 1 Item

# CRITICAL: Item Deduplication Rules (1 Topic = 1 Item)
## Core Principle
같은 Topic에 대한 여러 세션 논의는 반드시 **하나의 Item**으로 병합합니다.
절대 같은 Topic을 여러 Item으로 분리하지 마세요.

## Topic 동일성 판단
- Summary 제목: "Summary #N on {{Topic}}" - {{Topic}} 부분이 동일하면 같은 Topic
- TDoc 연속성: 동일 TDoc 또는 revision 관계
- 기술 주제: 같은 파라미터, 같은 기능에 대한 논의

## 병합 규칙
- "Summary #1 on Topic A" → "Summary #2 on Topic A" = **1개 Item** (병합!)
- Monday: Deferred → Thursday: Concluded = **status: Concluded** (최종값만 기록)
- 여러 세션 논의 = comeback: true, first_discussed + concluded 기록

## 올바른 예시 ✓
Topic "AI/ML evaluation" 논의가 여러 세션에 걸쳐 진행됨:
```yaml
- id: "RAN1_120_9.7.1_001"
  topic:
    summary: "AI/ML performance evaluation criteria"
  resolution:
    status: Concluded  # 최종 상태만!
  session_info:
    first_discussed: Tuesday
    concluded: Thursday
    comeback: true
```

## 잘못된 예시 ✗ (절대 이렇게 하지 마세요)
```yaml
- id: "RAN1_120_9.7.1_001"
  status: Noted  # Tuesday ← 세션별로 분리하면 안됨!
- id: "RAN1_120_9.7.1_002"
  status: Concluded  # Thursday ← 중복!
```

# Marker to content.type Mapping
# 하이라이트 색상별 마커: {{.mark}}, {{.mark-yellow}}, {{.mark-green}}, {{.mark-turquoise}}
- [Agreement]{{.mark}} 또는 [Agreement]{{.mark-yellow}} → agreement
- [Conclusion]{{.mark-green}} 또는 [Conclusion] → conclusion
- [Observation]{{.mark}} → observation
- **Decision:** → decision
- FFS: → ffs

# Status Determination
- Agreed: Agreement marker present and consensus reached
- Concluded: Conclusion marker present (Study-specific conclusion)
- Noted: "noted", individual TDoc noted
- Deferred: "Comeback", "postponed"
- No_Consensus: "No consensus", "Not agreed"

# Required Output Fields (Spec 3.3.1 준수)
For each Item, extract ALL of the following:

## id (필수)
Format: "{{meeting_id}}_{{leaf_id}}_{{sequence:3-digit}}"
Example: "RAN1_120_9.7.1_001"

## context (필수)
```yaml
context:
  meeting_id: "{meeting_id}"
  section_id: "{section_id}"
  leaf_id: "{leaf_id}"
  leaf_title: "{leaf_title}"
  section_type: "{section_type}"
```

## topic (필수)
```yaml
topic:
  summary: "1-line summary of discussion topic"
```

## input (필수 - 기술 논의)
Extract from "Relevant tdocs:" section (Spec 3.3.3 준수):
```yaml
input:
  moderator_summary: "R1-XXXXXXX"  # 또는 배열 ["R1-xxx", "R1-yyy"]
  discussion_tdocs:
    - tdoc_id: "R1-2500200"
      title: "Evaluation on AI/ML performance"
      source: "Huawei, HiSilicon"
      tdoc_type: discussion
    - tdoc_id: "R1-2501480"
      title: "Revised TR on AI/ML evaluation"
      source: "ZTE"
      tdoc_type: discussion
      revision_of: "R1-2500832"
```

### discussion_tdocs 항목 필드 (Spec 3.3.3 준수):
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| tdoc_id | string | ✓ | TDoc 번호 |
| title | string | ✓ | TDoc 제목 |
| source | string | ✓ | 제출 회사 |
| tdoc_type | string | ✓ | discussion, draft_cr, draft_ls, summary, way_forward |
| revision_of | string | - | 이전 버전 TDoc (있으면) |

## output (필수 - 결과물)
```yaml
output:
  crs: []
  outgoing_ls: []
  approved_tdocs:
    - tdoc_id: "R1-2501410"
      type: "Summary"          # Draft CR | LS | TP | Summary | WF
  endorsed_tdocs:
    - "R1-2501410"
```

### output.approved_tdocs 필드 (Spec 준수):
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| tdoc_id | string | ✓ | 승인된 TDoc 번호 |
| type | string | ✓ | Draft CR, LS, TP, Summary, WF |

### approved_tdocs.type 값:
| 타입 | 설명 | 식별 패턴 |
|------|------|----------|
| Summary | Moderator Summary | "Summary", "FL summary", "Moderator summary" |
| WF | Way Forward | "Way Forward", "WF" |
| TP | Text Proposal | "TP in R1-xxx", "text proposal" |

## resolution (필수)
```yaml
resolution:
  status: Agreed | Concluded | Noted | Deferred | No_Consensus
  content:
    - type: agreement | conclusion | observation | decision | ffs
      text: "extracted text from document"
      marker: "original marker"
```

## tr_info (Study 섹션 전용 - 선택)
```yaml
tr_info:
  tr_number: "TR 38.XXX"
  update_tdoc: "R1-XXXXXXX"
```

## session_info (선택)
```yaml
session_info:
  first_discussed: "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday"
  concluded: "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday"
  comeback: true | false
```

# Section Content
{section_content}

# Context
- meeting_id: {meeting_id}
- section_id: {section_id}
- leaf_id: {leaf_id}
- leaf_title: {leaf_title}

# Output Format
Return ONLY a JSON array of Item objects. No explanation.
IMPORTANT: Include ALL fields (input, output) even if arrays are empty.

Example:
[
  {{
    "id": "{meeting_id}_{leaf_id}_001",
    "context": {{
      "meeting_id": "{meeting_id}",
      "section_id": "9",
      "leaf_id": "{leaf_id}",
      "leaf_title": "AI/ML evaluation criteria",
      "section_type": "Study"
    }},
    "topic": {{"summary": "AI/ML performance evaluation criteria"}},
    "input": {{
      "moderator_summary": "R1-2501410",
      "discussion_tdocs": [
        {{
          "tdoc_id": "R1-2500200",
          "title": "Evaluation on AI/ML performance",
          "source": "Huawei, HiSilicon",
          "tdoc_type": "discussion"
        }}
      ]
    }},
    "output": {{
      "crs": [],
      "outgoing_ls": [],
      "approved_tdocs": [],
      "endorsed_tdocs": []
    }},
    "resolution": {{
      "status": "Concluded",
      "content": [
        {{
          "type": "conclusion",
          "text": "RAN1 concludes the evaluation criteria for AI/ML performance",
          "marker": "[Conclusion]{{{{.mark-green}}}}"
        }}
      ]
    }},
    "tr_info": {{
      "tr_number": "TR 38.843",
      "update_tdoc": "R1-2501532"
    }},
    "session_info": {{
      "first_discussed": "Tuesday",
      "concluded": "Thursday",
      "comeback": true
    }}
  }}
]
"""
