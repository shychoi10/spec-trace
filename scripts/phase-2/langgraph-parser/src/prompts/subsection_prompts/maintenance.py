"""
Maintenance SubSection 프롬프트

Spec 6.5.1 참조: Maintenance 섹션에서 Item 추출
Spec 3.3.1~3.3.4 참조: Item 필드 정의
"""

MAINTENANCE_PROMPT = """You are an expert Item extractor for 3GPP RAN1 Maintenance sections.

# Role
Extract Items from the Maintenance section content. Each Item represents a complete discussion flow.

# Key Characteristics of Maintenance Items
- Unit: Moderator Summary (논의 단위)
- Main results: Agreement, CR (Change Request)
- CR-centric: Focus on Change Requests for existing specs
- Session markers: "From Monday session" etc.
- Comeback pattern: Multiple sessions may discuss the same topic

# Item Boundary Detection Rules
**CRITICAL**: 대부분의 Leaf는 **1개 Item**입니다!
- 같은 Leaf 내의 Summary #1, #2, #3은 **모두 같은 Item**으로 병합
- 섹션 시작의 TDoc 목록은 해당 Leaf의 **모든 discussion_tdocs**
- 별도 Item 분리는 **명확히 다른 기술 주제**일 때만

**1 Leaf = 1 Item (기본 원칙)**
- Summary가 여러 개여도 같은 Topic이면 1 Item
- discussion_tdocs는 Leaf 시작 부분의 전체 TDoc 목록

# CRITICAL: Item Deduplication Rules (1 Topic = 1 Item)
## Core Principle
같은 Topic에 대한 여러 세션 논의는 반드시 **하나의 Item**으로 병합합니다.
절대 같은 Topic을 여러 Item으로 분리하지 마세요.

## Topic 동일성 판단
- Summary 제목: "Summary #N on {{Topic}}" - {{Topic}} 부분이 동일하면 같은 Topic
- TDoc 연속성: 동일 TDoc 또는 revision 관계 (R1-2500200 → R1-2500520)
- 기술 주제: 같은 파라미터, 같은 기능에 대한 논의

## 병합 규칙
- "Summary #1 on Topic A" → "Summary #2 on Topic A" = **1개 Item** (병합!)
- Monday: Deferred → Thursday: Agreed = **status: Agreed** (최종값만 기록)
- 여러 세션 논의 = comeback: true, first_discussed + concluded 기록

## 올바른 예시 ✓
Topic "power reduction" 논의가 Mon→Tue→Thu에 걸쳐 진행됨:
```yaml
- id: "RAN1_120_8.1v1_001"
  topic:
    summary: "transmission power reduction for STxMP"
  input:
    moderator_summary: ["R1-2501410", "R1-2501520"]  # Summary #1, #2
    discussion_tdocs:
      - "R1-2500200"
      - tdoc_id: "R1-2501480"
        revision_of: "R1-2500832"
  output:
    approved_tdocs: []
  resolution:
    status: No_Consensus
  session_info:
    first_discussed: Monday
    concluded: Thursday
    comeback: true
```

## 잘못된 예시 ✗ (절대 이렇게 하지 마세요)
```yaml
- id: "RAN1_120_8.1v1_001"
  status: Deferred  # Monday ← 이렇게 세션별로 분리하면 안됨!
- id: "RAN1_120_8.1v1_002"
  status: Deferred  # Tuesday ← 중복!
- id: "RAN1_120_8.1v1_003"
  status: No_Consensus  # Thursday ← 중복!
```

# Marker to content.type Mapping
# 하이라이트 색상별 마커: {{.mark}}, {{.mark-yellow}}, {{.mark-green}}, {{.mark-turquoise}}
- [Agreement]{{.mark}} 또는 [Agreement]{{.mark-yellow}} → agreement
- **Decision:** → decision
- [Conclusion]{{.mark-green}} 또는 [Conclusion] → conclusion
- FFS: → ffs
- [Working Assumption]{{.mark}} 또는 [Working Assumption]{{.mark-turquoise}} → working_assumption

# Status Determination
- Agreed: Agreement marker present and consensus reached
- Concluded: Conclusion marker present
- Noted: "noted", "No further action"
- Deferred: "Comeback", "postponed"
- No_Consensus: "No consensus", "Not agreed"

# Required Output Fields (Spec 3.3.1 준수)
For each Item, extract ALL of the following:

## id (필수)
Format: "{{meeting_id}}_{{leaf_id}}_{{sequence:3-digit}}"
Example: "RAN1_120_8.1v1_001"

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
**CRITICAL**: Leaf 시작 부분의 TDoc 목록을 **모두** 추출하세요!

### discussion_tdocs 추출 규칙:
**Leaf 시작 부분의 TAB 구분 TDoc 목록 = 해당 Item의 discussion_tdocs**
- 이 목록은 해당 Leaf 전체의 논의 자료
- Summary 이전에 나열된 **모든 TDoc**을 추출
- 각 줄: `R1-XXXXXXX\t{{제목}}\t{{회사명}}` 형식

### 추출 우선순위:
1. **Leaf 시작 TDoc 목록** (탭 구분): Summary 이전의 모든 TDoc
2. **Relevant tdocs 섹션**: `Relevant tdocs:` 마커 아래 TDoc들

### 원본 형식 인식 (IMPORTANT):
**형식 1 - 탭 구분 (가장 흔함)**:
```
R1-2500536	Draft CR on transmission power reduction for STxMP	ZTE Corporation, Sanechips
R1-2500537	Discussion on transmission power reduction for STxMP	ZTE Corporation, Sanechips
```

**형식 2 - 링크 형식**:
```
[R1-2500536](link) Draft CR on transmission power reduction... ZTE Corporation
```

**형식 3 - Relevant tdocs 블록**:
```
**Relevant tdocs:**
R1-2500200, R1-2500201, R1-2500202
```

### moderator_summary 추출:
**IMPORTANT**: Summary TDoc은 볼드체(`**`)로 표시되며 배열로 추출:
- `**R1-2501462****	Summary#1 on STxMP****	Moderator (Samsung)**` → R1-2501462
- `**R1-2501597****	Summary#2 on STxMP****	Moderator (Samsung)**` → R1-2501597
- **반드시** 모든 Summary를 배열로 수집: ["R1-2501462", "R1-2501597"]
- Summary TDoc 식별: 제목에 "Summary", "FL summary", "Moderator summary" 포함

```yaml
input:
  moderator_summary: ["R1-2501462", "R1-2501597"]  # 해당 Item과 관련된 Summary들
  discussion_tdocs:
    - tdoc_id: "R1-2500536"
      title: "Draft CR on transmission power reduction for STxMP"
      source: "ZTE Corporation, Sanechips"
      tdoc_type: draft_cr
    - tdoc_id: "R1-2500537"
      title: "Discussion on transmission power reduction for STxMP"
      source: "ZTE Corporation, Sanechips"
      tdoc_type: discussion
```

### discussion_tdocs 항목 필드 (Spec 3.3.3 준수):
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| tdoc_id | string | ✓ | TDoc 번호 (R1-XXXXXXX) |
| title | string | ✓ | TDoc 제목 |
| source | string | ✓ | 제출 회사 (쉼표로 구분된 복수 가능) |
| tdoc_type | string | ✓ | discussion, draft_cr, draft_ls, summary, way_forward |
| revision_of | string | - | 이전 버전 TDoc (있으면) |

### tdoc_type 결정:
- "Discussion on..." → discussion
- "Draft CR on..." → draft_cr
- "LS on..." → draft_ls
- "Summary..." → summary
- "Way Forward..." → way_forward
- 기타 → discussion (기본값)

## output (필수 - 결과물)
Extract approved CRs, outgoing LSs, approved TDocs, and endorsed TDocs (Spec 3.3.3 준수):
```yaml
output:
  crs:
    - tdoc_id: "R1-2501572"
      target_spec: "38.212"
      cr_number: "0210"        # Annex B에서 확인 가능
      category: "F"            # F|A|B|C|D
      release: "Rel-18"
      work_item: "NR_MIMO_evo_DL_UL-Core"
      revision_of: null
  outgoing_ls:
    - tdoc_id: "R1-2501636"
      replies_to: "R1-2500012"
  approved_tdocs:
    - tdoc_id: "R1-2501410"
      type: "Summary"          # Draft CR | LS | TP | Summary | WF
    - tdoc_id: "R1-2501520"
      type: "WF"
  endorsed_tdocs:
    - "R1-2501410"
```

### output.crs 필드 (Spec 준수):
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| tdoc_id | string | ✓ | CR TDoc 번호 |
| target_spec | string | ✓ | 대상 스펙 (예: "38.212") |
| cr_number | string | - | CR 번호 |
| category | string | - | F(Essential)|A(Earlier)|B(Add)|C(Modify)|D(Editorial) |
| release | string | ✓ | 대상 Release |
| work_item | string | - | Work Item 코드 |
| revision_of | string | - | 이전 CR TDoc |

### output.approved_tdocs 필드 (Spec 준수):
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| tdoc_id | string | ✓ | 승인된 TDoc 번호 |
| type | string | ✓ | Draft CR, LS, TP, Summary, WF |

### approved_tdocs.type 값:
| 타입 | 설명 | 식별 패턴 |
|------|------|----------|
| Draft CR | Change Request 초안 | "Draft CR", "alignment CR" |
| LS | Liaison Statement | "LS", "Reply LS" |
| TP | Text Proposal | "TP in R1-xxx", "text proposal" |
| Summary | Moderator Summary | "Summary", "FL summary", "Moderator summary" |
| WF | Way Forward | "Way Forward", "WF" |

### 승인 패턴 인식:
- "[approved in R1-xxx]{{.mark}}" → crs 또는 outgoing_ls 또는 approved_tdocs
- "Draft CR" 승인 → crs (상세 정보와 함께)
- "LS", "Reply LS" 승인 → outgoing_ls
- "TP in R1-xxx is agreed" → approved_tdocs (type: TP)
- "FL summary in R1-xxx" 승인 → approved_tdocs (type: Summary)
- "Way Forward in R1-xxx" 승인 → approved_tdocs (type: WF)
- "is endorsed" → endorsed_tdocs

## resolution (필수)
```yaml
resolution:
  status: Agreed | Concluded | Noted | Deferred | No_Consensus
  content:
    - type: agreement | conclusion | decision | ffs | working_assumption
      text: "extracted text from document"
      marker: "original marker like [Agreement]{{.mark}}"
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
      "section_id": "8",
      "leaf_id": "{leaf_id}",
      "leaf_title": "Example maintenance topic",
      "section_type": "Maintenance"
    }},
    "topic": {{"summary": "PUSCH power control for STxMP"}},
    "input": {{
      "moderator_summary": ["R1-2501410", "R1-2501520"],
      "discussion_tdocs": [
        {{
          "tdoc_id": "R1-2500200",
          "title": "Discussion on power control",
          "source": "Huawei, HiSilicon",
          "tdoc_type": "discussion"
        }},
        {{
          "tdoc_id": "R1-2501480",
          "title": "Revised CR on PUSCH power",
          "source": "ZTE",
          "tdoc_type": "draft_cr",
          "revision_of": "R1-2500832"
        }}
      ]
    }},
    "output": {{
      "crs": [
        {{
          "tdoc_id": "R1-2501572",
          "target_spec": "38.214",
          "cr_number": "0315",
          "category": "F",
          "release": "Rel-18",
          "work_item": "NR_MIMO_evo_DL_UL-Core"
        }}
      ],
      "outgoing_ls": [],
      "approved_tdocs": [
        {{
          "tdoc_id": "R1-2501410",
          "type": "Summary"
        }}
      ],
      "endorsed_tdocs": []
    }},
    "resolution": {{
      "status": "Agreed",
      "content": [
        {{
          "type": "agreement",
          "text": "RAN1 agrees on the power control procedure for STxMP",
          "marker": "[Agreement]{{{{.mark}}}}"
        }}
      ]
    }},
    "session_info": {{
      "first_discussed": "Monday",
      "concluded": "Thursday",
      "comeback": true
    }}
  }}
]
"""
