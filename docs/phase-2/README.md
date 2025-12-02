# Phase-2: LangGraph Multi-Agent System

## 목표
정답지와 동일한 출력 생성 (90%+ 일치)

## 핵심 설계 원칙

### 1. Content-Based Agent Selection
- ❌ "Section 5 Agent" (번호 기반)
- ✅ "Incoming LS Agent" (내용 패턴 기반)

**패턴 예시**:
- "LS on", "Reply LS" → Incoming LS Agent
- "Agreement", "Working assumption" → Study Item Agent
- 기타 → General Agent

### 2. LangGraph Workflow

```
Input (Final Minutes)
    ↓
[Meta Orchestrator]
    ↓ (내용 분석)
[Agent Selection]
    ↓
[Selected Agent Processing]
    ↓
[Output Generation]
    ↓
[Validation vs Ground Truth]
    ↓
[Iterative Improvement]
```

### 3. 점진적 개선 전략 (Stage 1~4)

**Stage 1**: Section 5 MVP (목표: Ground Truth 90%)
- DOCX Parser + TOC Builder
- LSAgent (Section 5 전용)
- 기본 Validation (Layer 1-2)
- Ground Truth 비교

**Stage 2**: Multi-Section (목표: 전체 문서 80%)
- MaintenanceAgent (Section 7, 8)
- WorkItemAgent (Section 9)
- ActionItemAgent (Annex F)
- Document-level Validation

**Stage 3**: Production Features
- HITL (interrupt 기반)
- Checkpointing (SQLite)
- Cost Management
- EVRIRL 사이클 완성

**Stage 4**: Learning & Generalization
- Learn v1.0 (패턴 로깅)
- 다른 Meeting 테스트
- Learn v2.0 (Semi-Auto) 준비

## 프로젝트 구조

```
scripts/phase-2/langgraph-system/
├── agents/
│   ├── base_agent.py           # BaseAgent 추상 클래스
│   ├── incoming_ls_agent.py    # Incoming LS 전문 Agent
│   └── meta_orchestrator.py    # Agent 선택자
├── prompts/
│   └── incoming_ls_prompt.md   # Incoming LS Agent 프롬프트
├── utils/
│   ├── llm_manager.py          # LLM 관리
│   └── validator.py            # Ground Truth 검증
├── workflows/
│   └── main_workflow.py        # LangGraph workflow
└── main.py                     # 실행 스크립트

output/phase-2/langgraph-system/
├── results/                    # 생성 결과
└── ground_truth/              # 정답지

logs/phase-2/langgraph-system/  # 실행 로그
```

## 실행 방법

```bash
cd scripts/phase-2/langgraph-system
python main.py
```

## 현재 상태

- [x] 프로젝트 구조 설계
- [ ] Stage 1: Section 5 MVP (90%)
- [ ] Stage 2: Multi-Section (80%)
- [ ] Stage 3: Production Features
- [ ] Stage 4: Learning & Generalization

---
**Last Updated**: 2025-11-28
**Status**: 설계 완료, Stage 1 구현 시작
