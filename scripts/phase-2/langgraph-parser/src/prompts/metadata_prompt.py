"""
메타데이터 추출 프롬프트

역할 1: 문서 헤더에서 회의 정보 추출
명세서 4.1 참조: 정규식 실패 시 LLM fallback
"""

METADATA_EXTRACTION_PROMPT = """You are a metadata extractor for 3GPP meeting documents.

## Task
Extract meeting metadata from the document header below.

## Required Fields
| Field | Description | Example |
|-------|-------------|---------|
| meeting_id | WG code + meeting number | RAN1_120 |
| tsg | TSG name | RAN |
| wg | Working Group | WG1 |
| wg_code | WG code | RAN1 |
| meeting_number | Meeting number | 120 |
| version | Document version | 1.0.0 |
| location | Meeting location | Athens, Greece |
| start_date | Start date (YYYY-MM-DD) | 2025-02-17 |
| end_date | End date (YYYY-MM-DD) | 2025-02-21 |
| source | Document source | MCC Support |
| document_for | Document purpose | Approval |

## Partial Data (already extracted by regex)
{partial_data}

## Document Header
{header_content}

## Instructions
1. Use partial_data where available (do not change correct values)
2. Extract missing fields from the header
3. Convert dates to ISO 8601 format (YYYY-MM-DD)
4. meeting_id = wg_code + "_" + meeting_number

## Output
Return ONLY a JSON object with all 11 fields, no explanation.
"""
