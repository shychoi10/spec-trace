"""
역할 1: 메타데이터 추출

명세서 4.1 참조:
- 입력: TOC 이전 헤더 영역
- 전략: 정규식 우선, LLM fallback
- 출력: meeting_info.yaml
- 에러: 파싱 실패 → _error 기록
"""

from datetime import datetime
from pathlib import Path

from ..models.meeting import MeetingInfo
from ..prompts.metadata_prompt import METADATA_EXTRACTION_PROMPT
from ..state import ParserState
from ..utils.file_io import save_yaml
from ..utils.llm_client import call_llm_for_metadata
from ..utils.markdown import extract_header
from ..utils.metadata_parser import parse_metadata_regex


def metadata_node(state: ParserState) -> dict:
    """메타데이터 추출 노드

    전략:
        1. 헤더 영역 추출 (TOC 이전)
        2. 정규식 파싱 (비용 효율)
        3. 누락 시 LLM fallback
        4. MeetingInfo 스키마 검증
        5. meeting_info.yaml 저장 (에러 시 _error 포함)

    명세서 참조:
        - 4.1: 역할 1 상세
        - 3.3.3: _error 구조 {error_type, error_message}

    Args:
        state: ParserState (markdown_content, output_dir 필요)

    Returns:
        dict: State 업데이트 (meeting_info, current_step, errors, warnings)
    """
    errors = []  # State용 ErrorRecord 리스트
    warnings = []
    output_dir = Path(state["output_dir"])
    yaml_path = output_dir / "meeting_info.yaml"

    # 1. 헤더 추출
    header_text = extract_header(state["markdown_content"])
    if not header_text:
        errors.append({
            "role": "role_1",
            "section_id": None,
            "error_type": "header_extraction_failed",
            "error_message": "헤더 영역을 추출할 수 없습니다",
            "timestamp": datetime.now().isoformat(),
        })
        # 명세서 4.1: 헤더 파싱 실패 시 _error와 함께 저장
        save_yaml(
            {
                "_error": {
                    "error_type": "header_extraction_failed",
                    "error_message": "헤더 영역을 추출할 수 없습니다",
                }
            },
            yaml_path,
        )
        return {"current_step": "role_1_failed", "errors": errors}

    # 2. 정규식 파싱
    parsed_data, missing_fields = parse_metadata_regex(header_text)

    # 3. LLM fallback (누락 필드 있으면)
    if missing_fields:
        try:
            llm_data = call_llm_for_metadata(
                header_text=header_text,
                partial_data=parsed_data,
                prompt_template=METADATA_EXTRACTION_PROMPT,
            )
            # 누락 필드만 LLM 결과로 채우기
            if parsed_data:
                for field in missing_fields:
                    if field in llm_data:
                        parsed_data[field] = llm_data[field]
            else:
                parsed_data = llm_data
            # missing_fields 업데이트
            missing_fields = [f for f in missing_fields if f not in (parsed_data or {})]
        except Exception as e:
            # 명세서 3.3.3: _warning 구조
            warnings.append({
                "role": "role_1",
                "section_id": None,
                "warning_type": "llm_fallback_failed",
                "message": f"LLM fallback 실패: {e}",
            })

    # 4. 스키마 검증
    try:
        meeting_info = MeetingInfo(**parsed_data)
        meeting_info_dict = meeting_info.model_dump()
        # 성공: YAML 저장
        save_yaml(meeting_info_dict, yaml_path)
    except Exception as e:
        # 명세서 4.1: 필수 필드 누락 → 추출된 필드만 저장 + _error
        errors.append({
            "role": "role_1",
            "section_id": None,
            "error_type": "validation_failed",
            "error_message": f"MeetingInfo 검증 실패: {e}",
            "timestamp": datetime.now().isoformat(),
        })
        # 부분 데이터 + _error 저장
        partial_result = parsed_data or {}
        partial_result["_error"] = {
            "error_type": "validation_failed",
            "error_message": f"필수 필드 누락: {missing_fields}",
        }
        save_yaml(partial_result, yaml_path)
        return {
            "meeting_info": parsed_data,  # 부분 데이터라도 State에 전달
            "current_step": "role_1_failed",
            "errors": errors,
            "warnings": warnings,
        }

    return {
        "meeting_info": meeting_info_dict,
        "current_step": "role_1_completed",
        "errors": errors if errors else [],
        "warnings": warnings if warnings else [],
    }
