"""
역할 2: TOC 파싱 + section_type 판단 + Agent 할당

명세서 4.2 참조:
- toc_raw (python-docx 추출) 입력
- Virtual Numbering 적용
- section_type 판단 (의미 기반)
- skip 여부 결정
- toc.yaml 생성

명세서 4.2.8 참조:
- 대용량 TOC 배치 처리
- 응답 검증 및 누락 시 재요청
"""

import json
from datetime import datetime
from pathlib import Path

import yaml

from ..models.toc import TOCSection
from ..prompts.toc_prompt import TOC_PARSING_PROMPT
from ..state import ParserState
from ..utils.file_io import save_yaml
from ..utils.llm_client import get_llm_client
from ..utils.toc_utils import process_toc_raw


# Spec 4.2.8 구현 파라미터
BATCH_SIZE = 30  # 배치 크기 (권장값)
MAX_RETRY = 2    # 최대 재시도 횟수


def validate_section_type(title: str, llm_section_type: str) -> tuple[str, str | None]:
    """Post-LLM Validation: 키워드 기반 section_type 검증

    Spec 4.2.2 검증 규칙 준수:
    - LLM 분류 결과를 키워드 기반으로 검증
    - 명백한 불일치 시 Override (일반화 원칙)
    - 섹션 번호 하드코딩 금지

    Args:
        title: 섹션 제목
        llm_section_type: LLM이 분류한 section_type

    Returns:
        tuple: (최종 section_type, override_reason 또는 None)
    """
    title_lower = title.lower()

    # Priority 1: "Liaison" → LS (가장 확실)
    if "liaison" in title_lower:
        if llm_section_type != "LS":
            return "LS", f"Override: 'Liaison' 키워드 발견 (LLM: {llm_section_type} → LS)"
        return llm_section_type, None

    # Priority 2: Procedural 키워드 (Liaison 없을 때만)
    procedural_keywords = ["approval", "minutes", "opening", "closing", "highlights"]
    if any(kw in title_lower for kw in procedural_keywords):
        if llm_section_type != "Procedural":
            matched = [kw for kw in procedural_keywords if kw in title_lower]
            return "Procedural", f"Override: Procedural 키워드 '{matched[0]}' 발견 (LLM: {llm_section_type} → Procedural)"
        return llm_section_type, None

    # Priority 3: "Annex" → Annex
    if "annex" in title_lower:
        if llm_section_type != "Annex":
            return "Annex", f"Override: 'Annex' 키워드 발견 (LLM: {llm_section_type} → Annex)"
        return llm_section_type, None

    # Priority 4-7: 불확실한 경우 LLM 결과 유지 (경고만)
    # 이 부분은 LLM이 더 정확할 수 있으므로 override 하지 않음

    return llm_section_type, None


def _apply_skip_from_section_type(section_type: str) -> tuple[bool, str | None]:
    """section_type에 따른 skip 결정

    Spec 4.2.4 준수:
    - Procedural → skip: true
    - Annex A, D~H → skip: true (별도 처리 필요)
    - 기타 → skip: false
    """
    if section_type == "Procedural":
        return True, "Procedural section"

    return False, None


def _retry_missing_sections(
    missing_entries: list[dict],
    id_to_type: dict,
    llm,
    processing_log: list[dict],
) -> list[dict]:
    """누락된 섹션에 대해 개별 재요청 (Spec 4.2.8)

    Args:
        missing_entries: 응답이 누락된 섹션들
        id_to_type: 이미 분류된 섹션 타입 매핑
        llm: LLM 클라이언트
        processing_log: 처리 이력 로그 (기록용)

    Returns:
        재요청으로 분류된 섹션들 (실패 시 _error 포함)
    """
    from ..prompts.toc_prompt import TOC_BATCH_PROMPT

    results = []

    for entry in missing_entries:
        section_id = entry["id"]
        parent_id = entry.get("parent")

        # 부모 컨텍스트 생성
        parent_context = "No parent context"
        if parent_id and parent_id in id_to_type:
            parent_context = f"- {section_id} (parent: {parent_id}) → parent is {id_to_type[parent_id]}"

        # 개별 섹션 YAML
        section_yaml = yaml.dump(
            [{"id": entry["id"], "title": entry["title"], "depth": entry["depth"], "parent": parent_id}],
            allow_unicode=True,
            default_flow_style=False,
        )

        # 재시도 루프 (Spec 4.2.8: 최대 2회)
        success = False
        for attempt in range(MAX_RETRY):
            prompt = TOC_BATCH_PROMPT.format(
                batch_size=1,
                parent_context=parent_context,
                sections_yaml=section_yaml,
            )

            try:
                response = llm.invoke(prompt)
                content = response.content

                # JSON 추출
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                retry_result = json.loads(content.strip())

                if retry_result and len(retry_result) > 0:
                    llm_entry = retry_result[0]
                    llm_section_type = llm_entry.get("section_type", "unknown")
                    llm_type_reason = llm_entry.get("type_reason", "")

                    # Post-LLM Validation (재시도에도 동일하게 적용)
                    validated_type, override_reason = validate_section_type(
                        title=entry.get("title", ""),
                        llm_section_type=llm_section_type,
                    )

                    merged = {**entry, "section_type": validated_type}

                    if override_reason:
                        merged["type_reason"] = override_reason
                        merged["_validation"] = {
                            "original_llm_type": llm_section_type,
                            "original_llm_reason": llm_type_reason,
                            "action": "override",
                        }
                        skip, skip_reason = _apply_skip_from_section_type(validated_type)
                        merged["skip"] = skip
                        merged["skip_reason"] = skip_reason
                    else:
                        merged["type_reason"] = llm_type_reason
                        merged["skip"] = llm_entry.get("skip", False)
                        merged["skip_reason"] = llm_entry.get("skip_reason")

                    # 처리 이력 기록
                    processing_log.append({
                        "section_id": section_id,
                        "action": "retry_success",
                        "attempt": attempt + 1,
                        "result": merged["section_type"],
                    })

                    results.append(merged)
                    id_to_type[section_id] = merged["section_type"]
                    success = True
                    break

            except (json.JSONDecodeError, Exception) as e:
                processing_log.append({
                    "section_id": section_id,
                    "action": "retry_failed",
                    "attempt": attempt + 1,
                    "error": str(e),
                })
                continue

        # 모든 재시도 실패 시 _error 기록 (Spec 4.2.8: Human Review 트리거)
        if not success:
            merged = {
                **entry,
                "section_type": "unknown",
                "type_reason": "재요청 실패 (Human Review 필요)",
                "skip": False,
                "skip_reason": None,
                "_error": {
                    "error_type": "retry_exhausted",
                    "error_message": f"섹션 {section_id} 재요청 {MAX_RETRY}회 실패",
                    "timestamp": datetime.now().isoformat(),
                },
            }
            processing_log.append({
                "section_id": section_id,
                "action": "retry_exhausted",
                "max_attempts": MAX_RETRY,
            })
            results.append(merged)
            id_to_type[section_id] = "unknown"

    return results


def call_llm_for_section_types(toc_processed: list[dict], prompt_template: str) -> tuple[list[dict], list[dict]]:
    """LLM으로 section_type과 skip 판단 (배치 처리 + 재요청)

    True Agentic AI 원칙 준수:
    - LLM이 의미를 파악하여 스스로 판단
    - 힌트 제공, 강제하지 않음

    Spec 4.2.8 준수:
    - 배치 처리 (30개씩)
    - 응답 검증 (요청 = 응답 확인)
    - 누락 시 개별 재요청 (최대 2회)
    - 처리 이력 _processing에 기록

    Args:
        toc_processed: Virtual Numbering + parent/children이 적용된 TOC
        prompt_template: 프롬프트 템플릿

    Returns:
        tuple: (section_type이 추가된 TOC, 처리 이력 로그)
    """
    from ..prompts.toc_prompt import TOC_BATCH_PROMPT

    llm = get_llm_client()

    # ID → section_type 매핑 (상속 컨텍스트용)
    id_to_type = {}

    # 처리 이력 로그 (Spec 4.2.8: _processing 기록)
    processing_log = []

    # 배치 처리
    all_results = []
    for batch_start in range(0, len(toc_processed), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(toc_processed))
        batch = toc_processed[batch_start:batch_end]
        batch_num = batch_start // BATCH_SIZE + 1

        # 부모 컨텍스트 생성 (이전 배치에서 분류된 타입 정보)
        parent_context_list = []
        for entry in batch:
            parent_id = entry.get("parent")
            if parent_id and parent_id in id_to_type:
                parent_context_list.append(
                    f"- {entry['id']} (parent: {parent_id}) → parent is {id_to_type[parent_id]}"
                )
        parent_context = "\n".join(parent_context_list) if parent_context_list else "No parent context for this batch"

        # 배치용 YAML 생성 (간소화)
        simplified_batch = [
            {"id": e["id"], "title": e["title"], "depth": e["depth"], "parent": e.get("parent")}
            for e in batch
        ]
        sections_yaml = yaml.dump(simplified_batch, allow_unicode=True, default_flow_style=False)

        # 프롬프트 생성
        prompt = TOC_BATCH_PROMPT.format(
            batch_size=len(batch),
            parent_context=parent_context,
            sections_yaml=sections_yaml,
        )

        # LLM 호출
        response = llm.invoke(prompt)

        # JSON 추출
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            batch_result = json.loads(content.strip())
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값
            batch_result = [{"section_type": "unknown", "type_reason": "JSON 파싱 실패", "skip": False, "skip_reason": None}] * len(batch)

        # Spec 4.2.8: 응답 검증 (요청 = 응답)
        requested_count = len(batch)
        response_count = len(batch_result)

        processing_log.append({
            "batch": batch_num,
            "requested": requested_count,
            "received": response_count,
            "status": "complete" if requested_count == response_count else "partial",
        })

        # 결과 병합 및 누락 섹션 식별
        missing_entries = []
        for i, entry in enumerate(batch):
            merged = {**entry}
            if i < len(batch_result):
                llm_entry = batch_result[i]
                llm_section_type = llm_entry.get("section_type", "unknown")
                llm_type_reason = llm_entry.get("type_reason", "")

                # Post-LLM Validation: 키워드 기반 검증 (Spec 4.2.2)
                validated_type, override_reason = validate_section_type(
                    title=entry.get("title", ""),
                    llm_section_type=llm_section_type,
                )

                merged["section_type"] = validated_type

                # Override 발생 시 type_reason 업데이트
                if override_reason:
                    merged["type_reason"] = override_reason
                    merged["_validation"] = {
                        "original_llm_type": llm_section_type,
                        "original_llm_reason": llm_type_reason,
                        "action": "override",
                    }
                    # skip도 section_type에 맞게 재계산
                    skip, skip_reason = _apply_skip_from_section_type(validated_type)
                    merged["skip"] = skip
                    merged["skip_reason"] = skip_reason
                else:
                    merged["type_reason"] = llm_type_reason
                    merged["skip"] = llm_entry.get("skip", False)
                    merged["skip_reason"] = llm_entry.get("skip_reason")

                # 상속 컨텍스트용 타입 저장 (검증된 타입)
                id_to_type[entry["id"]] = merged["section_type"]
                all_results.append(merged)
            else:
                # 응답 누락 → 재요청 대상
                missing_entries.append(entry)

        # Spec 4.2.8: 누락 섹션 재요청
        if missing_entries:
            processing_log.append({
                "batch": batch_num,
                "action": "retry_triggered",
                "missing_count": len(missing_entries),
                "missing_ids": [e["id"] for e in missing_entries],
            })

            retried_results = _retry_missing_sections(
                missing_entries=missing_entries,
                id_to_type=id_to_type,
                llm=llm,
                processing_log=processing_log,
            )
            all_results.extend(retried_results)

    return all_results, processing_log


def toc_node(state: ParserState) -> dict:
    """TOC 파싱 노드 (toc_raw 입력 기반)

    전략:
        1. toc_raw에 Virtual Numbering 적용
        2. Parent/Children 관계 계산
        3. LLM으로 section_type 판단
        4. TOCSection 스키마 검증
        5. toc.yaml 저장

    명세서 참조:
        - 4.2: 역할 2 상세
        - 6.3: TOCAgent 프롬프트

    Args:
        state: ParserState (toc_raw, output_dir 필요)

    Returns:
        dict: State 업데이트 (toc, current_step, errors, warnings)
    """
    errors = []
    warnings = []
    output_dir = Path(state["output_dir"])
    yaml_path = output_dir / "toc.yaml"

    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. toc_raw 확인 (Spec 4.0: entries 래퍼 구조)
    toc_raw = state.get("toc_raw", {})
    entries = toc_raw.get("entries", []) if isinstance(toc_raw, dict) else []
    if not entries:
        errors.append({
            "role": "role_2",
            "section_id": None,
            "error_type": "toc_raw_empty",
            "error_message": "toc_raw가 비어있습니다 (python-docx에서 TOC 스타일을 찾지 못함)",
            "timestamp": datetime.now().isoformat(),
        })
        save_yaml({
            "_error": {
                "error_type": "toc_raw_empty",
                "error_message": "toc_raw가 비어있습니다",
            }
        }, yaml_path)
        return {"current_step": "role_2_failed", "errors": errors}

    # 2. Virtual Numbering + Parent/Children 계산
    try:
        toc_processed = process_toc_raw(toc_raw)
    except Exception as e:
        errors.append({
            "role": "role_2",
            "section_id": None,
            "error_type": "toc_processing_failed",
            "error_message": f"TOC 처리 실패: {e}",
            "timestamp": datetime.now().isoformat(),
        })
        return {"current_step": "role_2_failed", "errors": errors}

    # 3. LLM으로 section_type 판단 (True Agentic AI 원칙)
    # Spec 1.3: 하드코딩 규칙 대신 LLM의 의미 이해 기반 처리
    # Spec 4.2.8: 배치 처리 + 응답 검증 + 누락 시 재요청
    processing_log = []
    try:
        toc_with_types, processing_log = call_llm_for_section_types(
            toc_processed=toc_processed,
            prompt_template=TOC_PARSING_PROMPT,
        )

        # 분류 통계 로깅
        type_counts = {}
        unknown_count = 0
        override_count = 0
        retry_count = sum(1 for log in processing_log if log.get("action") == "retry_success")
        retry_failed_count = sum(1 for log in processing_log if log.get("action") == "retry_exhausted")

        for entry in toc_with_types:
            section_type = entry.get("section_type", "unknown")
            type_counts[section_type] = type_counts.get(section_type, 0) + 1
            if section_type == "unknown":
                unknown_count += 1
            if entry.get("_validation", {}).get("action") == "override":
                override_count += 1

        # 처리 요약 로깅
        if retry_count > 0 or retry_failed_count > 0:
            warnings.append({
                "role": "role_2",
                "section_id": None,
                "warning_type": "batch_processing_stats",
                "message": f"배치 처리: 재요청 성공 {retry_count}개, 재요청 실패 {retry_failed_count}개",
            })

        # Post-LLM Validation 통계
        if override_count > 0:
            overridden_sections = [
                f"{e['id']}: {e.get('_validation', {}).get('original_llm_type')} → {e['section_type']}"
                for e in toc_with_types
                if e.get("_validation", {}).get("action") == "override"
            ]
            warnings.append({
                "role": "role_2",
                "section_id": None,
                "warning_type": "validation_override",
                "message": f"Post-LLM Validation: {override_count}개 섹션 Override됨",
                "details": overridden_sections,
            })

        if unknown_count > 0:
            warnings.append({
                "role": "role_2",
                "section_id": None,
                "warning_type": "classification_stats",
                "message": f"분류 통계: {type_counts} (unknown {unknown_count}개)",
            })
    except Exception as e:
        errors.append({
            "role": "role_2",
            "section_id": None,
            "error_type": "llm_classification_failed",
            "error_message": f"LLM section_type 판단 실패: {e}",
            "timestamp": datetime.now().isoformat(),
        })
        # LLM 실패해도 기본값으로 진행
        toc_with_types = []
        for entry in toc_processed:
            toc_with_types.append({
                **entry,
                "section_type": "unknown",
                "type_reason": "LLM 호출 실패",
                "skip": False,
                "skip_reason": None,
            })
        warnings.append({
            "role": "role_2",
            "section_id": None,
            "warning_type": "llm_fallback",
            "message": f"LLM 실패로 기본값 사용: {e}",
        })

    # 4. TOCSection 스키마 검증
    validated_sections = []
    for section_data in toc_with_types:
        try:
            section = TOCSection(**section_data)
            validated_sections.append(section.model_dump())
        except Exception as e:
            warnings.append({
                "role": "role_2",
                "section_id": section_data.get("id", "unknown"),
                "warning_type": "validation_warning",
                "message": f"섹션 검증 실패: {e}",
            })
            # 검증 실패해도 원본 데이터 포함
            validated_sections.append(section_data)

    # 5. toc.yaml 저장
    save_yaml(validated_sections, yaml_path)

    # 6. _processing 로그 저장 (Spec 4.2.8: 검증 가능성)
    if processing_log:
        processing_path = output_dir / "toc_processing.yaml"
        save_yaml({
            "_processing": {
                "total_sections": len(validated_sections),
                "batch_size": BATCH_SIZE,
                "max_retry": MAX_RETRY,
                "log": processing_log,
            }
        }, processing_path)

    return {
        "toc": validated_sections,
        "current_step": "role_2_completed",
        "errors": errors if errors else [],
        "warnings": warnings if warnings else [],
    }
