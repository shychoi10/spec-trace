"""
역할 0: 문서 전처리

python-docx를 사용하여 .docx → Markdown + TOC 구조 변환
- 하이라이트 마커 보존: [text]{.mark}
- TOC 구조 직접 추출: toc_raw.yaml
"""

from datetime import datetime
from pathlib import Path

from ..state import ParserState
from ..utils.docx_converter import (
    convert_docx_to_markdown,
    extract_meeting_id,
)


def preprocess_node(state: ParserState) -> dict:
    """전처리 노드 (python-docx 기반)

    입력:
        - state.input_path: .docx 파일 경로
        - state.output_dir: 출력 디렉토리

    출력:
        - markdown_content: 서식 마커 포함 Markdown
        - toc_raw: TOC 구조 리스트 (직접 추출)
        - meeting_id: 추출된 회의 ID
        - current_step: 현재 단계 업데이트

    에러 시:
        - errors: 에러 정보 추가
    """
    input_path = state["input_path"]
    output_dir = state.get("output_dir", "output/phase-2/langgraph-parser/results")

    errors = []
    warnings = []

    # 1. meeting_id 추출
    meeting_id = extract_meeting_id(input_path)
    if meeting_id == "unknown":
        warnings.append({
            "step": "role_0",
            "type": "meeting_id_extraction",
            "message": f"Could not extract meeting_id from path: {input_path}",
            "timestamp": datetime.now().isoformat(),
        })

    # 2. 출력 디렉토리 설정
    # output_dir: output/phase-2/langgraph-parser/results/{meeting_id}
    # converted_dir: output/phase-2/langgraph-parser/converted/{meeting_id}
    output_base = Path(output_dir)
    if output_base.name == meeting_id:
        # output_dir이 이미 meeting_id를 포함하는 경우
        # results/{meeting_id} → converted/{meeting_id}
        converted_dir = output_base.parent.parent / "converted" / meeting_id
    else:
        # output_dir이 results 폴더인 경우
        converted_dir = output_base.parent / "converted" / meeting_id

    # 3. docx → Markdown + TOC 변환 (python-docx)
    try:
        markdown_content, toc_raw = convert_docx_to_markdown(
            input_path=input_path,
            output_dir=converted_dir,
        )

    except FileNotFoundError as e:
        errors.append({
            "step": "role_0",
            "type": "file_not_found",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        })
        return {
            "current_step": "role_0_failed",
            "meeting_id": meeting_id,
            "errors": errors,
            "warnings": warnings,
        }

    except ImportError as e:
        errors.append({
            "step": "role_0",
            "type": "import_error",
            "message": f"python-docx not installed: {e}",
            "timestamp": datetime.now().isoformat(),
        })
        return {
            "current_step": "role_0_failed",
            "meeting_id": meeting_id,
            "errors": errors,
            "warnings": warnings,
        }

    except Exception as e:
        errors.append({
            "step": "role_0",
            "type": "conversion_error",
            "message": f"DOCX conversion failed: {e}",
            "timestamp": datetime.now().isoformat(),
        })
        return {
            "current_step": "role_0_failed",
            "meeting_id": meeting_id,
            "errors": errors,
            "warnings": warnings,
        }

    # 4. TOC 추출 확인
    if not toc_raw:
        warnings.append({
            "step": "role_0",
            "type": "toc_extraction",
            "message": "No TOC entries found in document (no TOC styles detected)",
            "timestamp": datetime.now().isoformat(),
        })

    # 성공 시 상태 업데이트
    result = {
        "markdown_content": markdown_content,
        "toc_raw": toc_raw,
        "meeting_id": meeting_id,
        "current_step": "role_0_completed",
    }

    if warnings:
        result["warnings"] = warnings

    return result
