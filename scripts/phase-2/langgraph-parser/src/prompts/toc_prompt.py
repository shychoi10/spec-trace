"""
TOC 파싱 프롬프트

역할 2: 목차 구조 파악 및 섹션 분류

명세서 4.2, 6.3 참조:
- toc_raw (python-docx 추출) 입력
- section_type 판단 (의미 기반)
- skip 여부 결정
"""

# 레거시 프롬프트 (하위 호환용)
TOC_PROMPT = """
You are a TOC parser for 3GPP meeting documents.

Analyze the Table of Contents and for each section determine:
1. id: Section number (e.g., "9", "9.1", "9.1.1")
2. title: Section title
3. depth: Hierarchy depth (1=top level)
4. parent: Parent section id (null for depth 1)
5. children: List of child section ids
6. section_type: One of [Procedural, Maintenance, Release, Study, UE_Features, LS, Annex]
7. type_reason: Reasoning for the section_type classification
8. skip: Whether to skip processing (true for Procedural and non-essential Annex)
9. skip_reason: Reason for skipping (if skip=true)
10. virtual: Whether this is a virtual section for intro content

Section Type Guidelines:
- Procedural: Opening, Approval, Closing, Highlights sections
- Maintenance: Sections dealing with existing Release maintenance
- Release: Sections for new Release features (e.g., "Release 19")
- Study: Study Items and research topics
- UE_Features: UE capability and feature definitions
- LS: Incoming Liaison Statements
- Annex: Appendix sections (only B, C-1, C-2 are processed)

TOC Content:
{toc_content}

Return the result as a JSON array of section objects.
"""

# Step-4 프롬프트 (toc_raw 입력 기반)
# Spec 원칙 준수:
# - 원칙 1: 의미 기반 판단 (True Agentic AI)
# - 원칙 2: 힌트 제공, 강제하지 않음
TOC_PARSING_PROMPT = """You are a semantic analyzer for 3GPP RAN1 meeting documents.

## Task
Analyze each TOC section's **meaning** and classify its type.
NOTE: id, title, depth, parent, children, virtual are already provided.
You need to determine: section_type, type_reason, skip, skip_reason

## Your Role
You are an expert in 3GPP meeting document structure. Use your understanding of:
- Meeting proceedings and administrative content
- Technical work items and their lifecycle
- The relationship between parent and child sections

## Output Format (JSON Array)
For EACH section, return:
```json
{{
  "section_type": "Procedural|Maintenance|Release|Study|UE_Features|LS|Annex|unknown",
  "type_reason": "Brief explanation of your reasoning",
  "skip": true/false,
  "skip_reason": "reason if skip=true, null otherwise"
}}
```

## Semantic Hints (use as guidance, not strict rules)
These patterns often indicate certain section types:

| Pattern | Likely Type | Context |
|---------|-------------|---------|
| "Annex" in title | Annex | Supplementary material |
| "Liaison" in title | LS | External communication |
| "Opening", "Closing", "Approval" | Procedural | Meeting administration |
| "UE Features" or "UE feature" | UE_Features | Device capability definitions |
| "Study" or standalone "SI" | Study | Research and investigation |
| "Maintenance" or "Pre-Rel" | Maintenance | Existing spec updates |
| "Release XX" (with number) | Release | New release features |

## Key Principles
1. **Meaning over keywords**: Consider the full context, not just keyword matching
2. **Inheritance**: Child sections typically share their parent's purpose
3. **Title analysis**: Understand what the section is actually about
4. **Unknown is valid**: Use "unknown" if you genuinely cannot determine the type

## skip Guidance
- Procedural sections (meeting admin) are typically skipped
- Annex A (Tdoc list), D-H are supplementary and skipped
- Annex B (CRs), C (LSs) contain important technical content
- Technical content sections should NOT be skipped

## Parent Context (for inheritance)
{parent_context}

## Sections to Classify
{toc_raw_yaml}

## Critical Requirement
You MUST return EXACTLY {num_sections} JSON objects in the same order as input.
Each input section needs exactly one corresponding output object.

Return ONLY the JSON array, no other text.
"""

# 배치 처리용 프롬프트 (소규모 배치)
TOC_BATCH_PROMPT = """You are a semantic analyzer for 3GPP RAN1 meeting documents.

## Task
Classify the section_type for these {batch_size} sections.

## Section Types
- Procedural: Meeting administration (opening, closing, approval, etc.)
- Maintenance: Updates to existing specs
- Release: New release features (Release 18, 19, etc.)
- Study: Research items (Study Item, SI)
- UE_Features: Device capability definitions
- LS: Liaison Statements (external communication)
- Annex: Supplementary material

## Inheritance Rule
If a section has no clear indicator, it likely inherits from its parent.
Parent context: {parent_context}

## Sections to Classify
{sections_yaml}

## Output
Return a JSON array with exactly {batch_size} objects:
```json
[
  {{"section_type": "...", "type_reason": "...", "skip": bool, "skip_reason": "..."}},
  ...
]
```

## Skip Rules
- Procedural → skip: true
- Annex A, D, E, F, G, H → skip: true
- Others → skip: false

Return ONLY the JSON array.
"""
