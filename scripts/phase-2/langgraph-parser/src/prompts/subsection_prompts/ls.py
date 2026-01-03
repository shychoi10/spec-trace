"""
LS SubSection 프롬프트

Spec 5.2.5 참조: LS (Liaison Statement) 섹션에서 Item 추출
Spec 3.3.1~3.3.3 참조: Item 필드 정의
"""

LS_PROMPT = """You are an expert Item extractor for 3GPP RAN1 Liaison Statement sections.

# Role
Extract Items from the LS section content. Each LS is 1 Item.

# Key Characteristics of LS Items
- 1 LS = 1 Item (each Incoming LS is a separate Item)
- Track release_category from group headers
- Extract handling information (agenda, moderator)
- Capture all Relevant TDocs as discussion_tdocs

# Required Output Fields (Spec 3.3.1~3.3.3 준수)

## id (필수)
Format: "{{meeting_id}}_{{leaf_id}}_{{sequence:3-digit}}"
Example: "RAN1_120_5_001"

## context (필수)
```yaml
context:
  meeting_id: "{meeting_id}"
  section_id: "{section_id}"
  leaf_id: "{leaf_id}"
  leaf_title: "{leaf_title}"
  section_type: LS
```

## release_category (필수)
- Extract from bold group header: `**Rel-{{버전}} {{주제}}**`
- Example: "Rel-18 MIMO", "Rel-19 AI/ML"
```yaml
release_category: "Rel-18 MIMO"
```

## ls_in (필수 - Incoming LS 정보)
```yaml
ls_in:
  tdoc_id: "R1-XXXXXXX"      # Incoming LS TDoc ID
  title: "LS title"           # Full LS title
  source_wg: "RAN2"           # Source WG (RAN2, RAN4, SA2, etc.)
  source_company: "Samsung"   # Source company (if present after comma)
```
- Parse: `**[{{TDoc}}](link) {{title}} {{source_wg}}, {{source_company}}**`
- If no comma: source_company = null

## input (필수 - Relevant TDocs)
Extract from `**Relevant tdocs:**` or `**Relevant Tdoc(s):**` section (Spec 3.3.3 준수):
```yaml
input:
  discussion_tdocs:
    - tdoc_id: "R1-2500195"
      title: "Discussion on LS response"
      source: "Samsung"
      tdoc_type: discussion
    - tdoc_id: "R1-2501480"
      title: "Revised LS draft"
      source: "ZTE"
      tdoc_type: draft_ls
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

### 추출 규칙:
- Include ALL TDocs until `**Decision:**` marker
- "(rev of R1-xxx)" 또는 "(revision of R1-xxx)" 패턴 → revision_of 필드 추가

## handling (필수 - 후속 처리 정보)
```yaml
handling:
  agenda_item: "8.1"           # agenda item 번호
  topic: "MIMO"                # 주제 (선택)
  moderator: "Sa"              # 담당자 이름
  moderator_company: "Samsung" # 담당자 회사
  deferred_to: "RAN1#122bis"   # 연기된 회의 (선택)
```
- Parse from Decision text: "agenda item {{번호}} ({{주제}}) - {{담당자}} ({{회사}})"
- If "To be handled in next meeting {{회의}}" → deferred_to

## ls_out (필수 - LS 응답 정보)
```yaml
ls_out:
  action: "Replied" | "Note" | "No_Action" | "Deferred" | "Response_Required" | "Deferred_Next_Meeting"
  reply_tdoc: "R1-XXXXXXX"     # 응답 TDoc (if Replied)
  replies_to: "R1-XXXXXXX"     # = ls_in.tdoc_id
```

### ls_out.action 결정 규칙:
| 패턴 | action 값 |
|------|-----------|
| "No action is needed", "No further action" | No_Action |
| "To be taken into account" | Note |
| "To be discussed", "To be handled in agenda item" (현재 회의) | Deferred |
| "response is needed", "response is necessary" | Response_Required |
| "To be handled in next meeting" | Deferred_Next_Meeting |
| "Reply LS approved", "Final LS is approved", 최종 LS 승인 | Replied |

## output (필수 - 결과물)
```yaml
output:
  crs: []
  outgoing_ls:
    - tdoc_id: "R1-2501636"
      replies_to: "R1-2500012"    # = ls_in.tdoc_id
  approved_tdocs:
    - tdoc_id: "R1-2501410"
      type: "Summary"             # Draft CR | LS | TP | Summary | WF
  endorsed_tdocs: []
```

### output.approved_tdocs 필드:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| tdoc_id | string | ✓ | 승인된 TDoc 번호 |
| type | string | ✓ | Draft CR, LS, TP, Summary, WF |

## resolution (필수)
```yaml
resolution:
  status: Noted | Agreed | Deferred | Concluded
  content:
    - type: decision
      text: "decision text"
      marker: "**Decision:**"
```

## LS 특수 플래그 (선택)
```yaml
cc_only: true              # 섹션 헤더에 "cc-ed" 또는 "cc-" 있으면
received_during_week: true  # 섹션 헤더에 "during the week" 있으면
```

# Section Content
{section_content}

# Context
- meeting_id: {meeting_id}
- section_id: {section_id}
- leaf_id: {leaf_id}
- leaf_title: {leaf_title}
- section_type: {section_type}

# Output Format
Return ONLY a JSON array of Item objects. No explanation.
IMPORTANT: Include ALL required fields per Spec.

Example:
[
  {{
    "id": "{meeting_id}_{leaf_id}_001",
    "context": {{
      "meeting_id": "{meeting_id}",
      "section_id": "{section_id}",
      "leaf_id": "{leaf_id}",
      "leaf_title": "{leaf_title}",
      "section_type": "LS"
    }},
    "release_category": "Rel-18 MIMO",
    "ls_in": {{
      "tdoc_id": "R1-2500012",
      "title": "LS on UL 8Tx",
      "source_wg": "RAN2",
      "source_company": "Samsung"
    }},
    "input": {{
      "discussion_tdocs": [
        {{
          "tdoc_id": "R1-2500195",
          "title": "Discussion on LS response",
          "source": "Huawei, HiSilicon",
          "tdoc_type": "discussion"
        }},
        {{
          "tdoc_id": "R1-2500248",
          "title": "Revised LS draft",
          "source": "ZTE",
          "tdoc_type": "draft_ls",
          "revision_of": "R1-2500200"
        }}
      ]
    }},
    "handling": {{
      "agenda_item": "8.1",
      "topic": "MIMO",
      "moderator": "Sa",
      "moderator_company": "Samsung"
    }},
    "ls_out": {{
      "action": "Deferred",
      "reply_tdoc": null,
      "replies_to": "R1-2500012"
    }},
    "output": {{
      "crs": [],
      "outgoing_ls": [],
      "approved_tdocs": [],
      "endorsed_tdocs": []
    }},
    "resolution": {{
      "status": "Deferred",
      "content": [
        {{"type": "decision", "text": "RAN1 response is necessary and to be handled in agenda item 8.1 (MIMO) - Sa (Samsung).", "marker": "**Decision:**"}}
      ]
    }}
  }},
  {{
    "id": "{meeting_id}_{leaf_id}_002",
    "context": {{
      "meeting_id": "{meeting_id}",
      "section_id": "{section_id}",
      "leaf_id": "{leaf_id}",
      "leaf_title": "{leaf_title}",
      "section_type": "LS"
    }},
    "release_category": "Rel-19 AI/ML",
    "ls_in": {{
      "tdoc_id": "R1-2500007",
      "title": "LS response on waveform determination for PUSCH",
      "source_wg": "RAN4",
      "source_company": null
    }},
    "input": {{
      "discussion_tdocs": []
    }},
    "handling": {{
      "agenda_item": null,
      "topic": null,
      "moderator": null,
      "moderator_company": null
    }},
    "ls_out": {{
      "action": "No_Action",
      "reply_tdoc": null,
      "replies_to": "R1-2500007"
    }},
    "output": {{
      "crs": [],
      "outgoing_ls": [],
      "approved_tdocs": [],
      "endorsed_tdocs": []
    }},
    "resolution": {{
      "status": "Noted",
      "content": [
        {{"type": "decision", "text": "No further action necessary from RAN1.", "marker": "**Decision:**"}}
      ]
    }}
  }}
]
"""
