# Phase-2 Step-2: Multi-Section Expansion

## Overview

Final Minutes 문서의 모든 Section을 처리하는 범용 Multi-Agent 아키텍처.

**Status**: 🔄 In Progress

**목표**: 단일 워크플로우가 동일 유형의 모든 Section을 처리 (Section 번호 무관)

## 제1 원칙 (First Principles)

> 이 원칙들은 모든 구현에서 반드시 준수해야 합니다.

### 1. True Agentic AI (LLM 전용)
**모든 텍스트 분석, 분류, 추출은 반드시 LLM이 수행**

| ❌ 금지 | ✅ 허용 |
|--------|--------|
| Regex 패턴 매칭 | LLM 프롬프트 |
| 하드코딩된 if-else | JSON 파싱 (LLM 응답) |
| 키워드 매칭 분류 | 타입 변환 (str→enum) |

### 2. General Design (범용 설계)
**특정 Section에 종속되지 않는 범용 구조**

| ❌ 금지 | ✅ 허용 |
|--------|--------|
| `MaintenanceRel18Agent` 각각 구현 | 단일 `MaintenanceWorkflow` |
| Section 번호 하드코딩 | 콘텐츠 기반 감지 |
| 미팅별 분기 로직 | 파라미터화된 워크플로우 |

### 3. 기존 코드 보호
**Step-1 IncomingLS 워크플로우 영향 금지**

| ❌ 수정 금지 | ✅ 허용 |
|-------------|--------|
| `incoming_ls_workflow.py` | 새 파일 추가 |
| `sub_agents/*` 로직 변경 | 기존 컴포넌트 import 재사용 |

## Architecture

### 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    DocumentParser                           │
│           (DOCX → All Heading 1 Sections 추출)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MetaSectionAgent                         │
│     (LLM 기반 Section 타입 분류 - NO REGEX!)                │
│                                                             │
│  Input: Section Title + Preview Content                     │
│  Output: {                                                  │
│    "type": "incoming_ls" | "maintenance" | "release" | ...  │
│    "release": "Rel-18" | "Pre-Rel-18" | null,               │
│    "technology": "NR" | "E-UTRA" | null                     │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │IncomingLS   │ │Maintenance  │ │Other        │
    │Workflow     │ │Workflow     │ │(Skip/Future)│
    │(Step-1)     │ │(Step-2 NEW) │ │             │
    └─────────────┘ └─────────────┘ └─────────────┘
            │               │
            ▼               ▼
    ┌─────────────────────────────────────────┐
    │         Output per Section              │
    │  - RAN1_120_incoming_ls.md              │
    │  - RAN1_120_maintenance_rel18.md        │
    │  - RAN1_120_maintenance_pre_rel18_nr.md │
    └─────────────────────────────────────────┘
```

### Target Sections (RAN1 #120 기준)

| Section Title | Type | Workflow |
|---------------|------|----------|
| Incoming Liaison Statements | `incoming_ls` | IncomingLSWorkflow (Step-1) |
| Pre-Rel-18 E-UTRA Maintenance | `maintenance` | MaintenanceWorkflow (Step-2) |
| Pre-Rel-18 NR Maintenance | `maintenance` | MaintenanceWorkflow (Step-2) |
| Maintenance on Release 18 | `maintenance` | MaintenanceWorkflow (Step-2) |

## Implementation Plan

### Sub-step 2-0: 문서 정리 ✅
- `docs/phase-2/README.md` 업데이트
- `docs/phase-2/step2_multi-section-expansion.md` 생성 (이 문서)
- `CLAUDE.md` 제1 원칙 강화

### Sub-step 2-1: Meta Layer 구현
1. `src/agents/meta_section_agent.py` - LLM 기반 Section 분류
2. `src/models/section_types.py` - SectionType enum, SectionMetadata

### Sub-step 2-2: Maintenance Workflow 구현
1. `src/workflows/maintenance_workflow.py` - 범용 워크플로우
2. `src/models/maintenance_item.py` - MaintenanceItem 모델

### Sub-step 2-3: 통합 및 출력
1. `src/orchestrator.py` - 전체 파이프라인 조율
2. 출력 파일 네이밍 표준화

### Sub-step 2-4: 테스트 및 검증
1. RAN1 #120 전체 파이프라인 테스트
2. 기존 IncomingLS 영향 없음 확인

## File Structure

### 신규 생성 파일

```
scripts/phase-2/langgraph-system/src/
├── agents/
│   └── meta_section_agent.py      # Section 타입 분류 (LLM 기반)
├── models/
│   ├── section_types.py           # SectionType, SectionClassification
│   └── maintenance_item.py        # MaintenanceItem (범용)
├── workflows/
│   └── maintenance_workflow.py    # 범용 Maintenance 워크플로우
└── orchestrator.py                # 전체 파이프라인 조율
```

### 절대 수정 금지 파일

```
src/workflows/incoming_ls_workflow.py   # Step-1 동작 유지
src/agents/sub_agents/*                 # 기존 로직 유지
```

## Reusable Components (from Step-1)

| Component | Reuse Strategy |
|-----------|---------------|
| `BaseAgent` | 100% import |
| `LLMManager` | 100% import |
| `TdocLinkerAgent` | 100% import |
| `SummaryGeneratorAgent` | 100% import |
| `BoundaryDetectorAgent` | 프롬프트만 변경 |
| `DecisionClassifierAgent` | Decision 타입 확장 |

## Output Format

### Maintenance Section Output Example

```markdown
# Maintenance on Release 18 (RAN1 #120)

## Section Overview
Release 18 유지보수 항목을 다루는 섹션입니다...

**Statistics:**
- Total Items: 45
- Topics: 12
- Agreements: 30
- CRs Approved: 25

---

### MIMO

#### Item 1: R1-2500123
**Source**: ZTE Corporation
**Decision Type**: Agreement
**Summary**: MIMO 관련 CR 승인...
**CR Information**:
- CR ID: CR0656
- Spec: 38.214
- Release: Rel-18
- Category: Cat F

---
```

## Validation Checklist

구현 완료 시 확인 사항:

- [ ] MetaSectionAgent가 regex 없이 LLM만으로 분류하는가?
- [ ] MaintenanceWorkflow가 3개 Section 모두 처리하는가?
- [ ] 기존 IncomingLS 파일을 수정하지 않았는가?
- [ ] Section 번호 하드코딩이 없는가?
- [ ] 출력 파일이 콘텐츠 기반으로 명명되는가?

---

**Last Updated**: 2025-12-03
