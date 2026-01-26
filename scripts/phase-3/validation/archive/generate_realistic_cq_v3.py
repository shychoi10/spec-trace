#!/usr/bin/env python3
"""
CQ Test Dataset Generator v3.0 - Realistic Questions for Both Target Users

Target Users (from Spec):
1. 전략/기획 담당자: 회의 결과 파악, 기술 트렌드 분석, 경쟁사 동향
2. IP/특허 담당자: 기고의 표준 반영 여부, 기여 증거 확보

Design Principles:
- Natural language questions that real practitioners would ask
- Context-rich questions with specific technology/company focus
- Both strategic and IP perspectives balanced
- Stay within CQ type scope
"""

import json
from datetime import datetime
from pathlib import Path

# Output path
OUTPUT_PATH = Path(__file__).parent.parent.parent.parent / "logs" / "phase-3" / "cq_test_dataset_100.json"

# CQ Type definitions with realistic question patterns
# Each CQ type gets questions from BOTH user perspectives

test_cases = []

# =============================================================================
# CQ1: Resolution 조회 (Agreement, Conclusion, Working Assumption)
# =============================================================================

# CQ1-1: Agreement 조회 (5 cases) - 전략 + IP 균형
cq1_1_cases = [
    # 전략 관점
    {
        "id": "TC-001",
        "cq_type": "CQ1-1",
        "perspective": "전략",
        "question": "RAN1#112 회의에서 합의된 주요 기술 결정사항들을 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 회의에서 도출된 Agreement 목록",
        "parameters": {"meeting": "RAN1#112"}
    },
    {
        "id": "TC-002",
        "cq_type": "CQ1-1",
        "perspective": "전략",
        "question": "최근 RAN1#118 회의에서 어떤 기술 합의가 이루어졌어?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 회의의 Agreement 목록",
        "parameters": {"meeting": "RAN1#118"}
    },
    # IP 관점
    {
        "id": "TC-003",
        "cq_type": "CQ1-1",
        "perspective": "IP",
        "question": "RAN1#110 회의에서 표준으로 채택된 기술 명세는 무엇인지 확인하고 싶어",
        "expected_result_type": "list",
        "expected_answer": "RAN1#110 회의의 Agreement 목록 (표준 반영 기술)",
        "parameters": {"meeting": "RAN1#110"}
    },
    {
        "id": "TC-004",
        "cq_type": "CQ1-1",
        "perspective": "IP",
        "question": "초기 NR 표준화 RAN1#88 회의의 Agreement 내용을 특허 검토를 위해 확인하려고 해",
        "expected_result_type": "list",
        "expected_answer": "RAN1#88 회의의 Agreement 목록",
        "parameters": {"meeting": "RAN1#88"}
    },
    {
        "id": "TC-005",
        "cq_type": "CQ1-1",
        "perspective": "전략",
        "question": "Rel-17 핵심 회의인 RAN1#103에서 결정된 사항들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#103 회의의 Agreement 목록",
        "parameters": {"meeting": "RAN1#103"}
    },
]

# CQ1-2: Conclusion 조회 (5 cases)
cq1_2_cases = [
    # 전략 관점
    {
        "id": "TC-006",
        "cq_type": "CQ1-2",
        "perspective": "전략",
        "question": "RAN1#115 회의에서 기술 검토 결론이 어떻게 났어?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#115 회의의 Conclusion 목록",
        "parameters": {"meeting": "RAN1#115"}
    },
    {
        "id": "TC-007",
        "cq_type": "CQ1-2",
        "perspective": "전략",
        "question": "RAN1#120 회의의 기술 토론 결론을 정리해줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#120 회의의 Conclusion 목록",
        "parameters": {"meeting": "RAN1#120"}
    },
    # IP 관점
    {
        "id": "TC-008",
        "cq_type": "CQ1-2",
        "perspective": "IP",
        "question": "RAN1#109 회의 Conclusion 중 기술 방향성 결정 내용을 확인하고 싶어",
        "expected_result_type": "list",
        "expected_answer": "RAN1#109 회의의 Conclusion 목록",
        "parameters": {"meeting": "RAN1#109"}
    },
    {
        "id": "TC-009",
        "cq_type": "CQ1-2",
        "perspective": "IP",
        "question": "RAN1#99 회의에서 어떤 기술적 결론이 내려졌는지 특허 출원 근거로 확인할래",
        "expected_result_type": "list",
        "expected_answer": "RAN1#99 회의의 Conclusion 목록",
        "parameters": {"meeting": "RAN1#99"}
    },
    {
        "id": "TC-010",
        "cq_type": "CQ1-2",
        "perspective": "전략",
        "question": "최근 RAN1#122b 회의에서 나온 Conclusion들 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#122b 회의의 Conclusion 목록",
        "parameters": {"meeting": "RAN1#122b"}
    },
]

# CQ1-3: Working Assumption 조회 (5 cases)
cq1_3_cases = [
    # 전략 관점
    {
        "id": "TC-011",
        "cq_type": "CQ1-3",
        "perspective": "전략",
        "question": "RAN1#112 회의에서 설정된 Working Assumption이 뭐야? 향후 표준화 방향을 파악하고 싶어",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 회의의 Working Assumption 목록",
        "parameters": {"meeting": "RAN1#112"}
    },
    {
        "id": "TC-012",
        "cq_type": "CQ1-3",
        "perspective": "전략",
        "question": "RAN1#106 회의에서 잠정 합의된 기술 가정들을 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#106 회의의 Working Assumption 목록",
        "parameters": {"meeting": "RAN1#106"}
    },
    # IP 관점
    {
        "id": "TC-013",
        "cq_type": "CQ1-3",
        "perspective": "IP",
        "question": "RAN1#100 회의의 Working Assumption 중 특허와 관련될 수 있는 기술 가정이 있는지 확인해줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#100 회의의 Working Assumption 목록",
        "parameters": {"meeting": "RAN1#100"}
    },
    {
        "id": "TC-014",
        "cq_type": "CQ1-3",
        "perspective": "IP",
        "question": "RAN1#94 회의에서 설정된 기술 가정 목록을 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#94 회의의 Working Assumption 목록",
        "parameters": {"meeting": "RAN1#94"}
    },
    {
        "id": "TC-015",
        "cq_type": "CQ1-3",
        "perspective": "전략",
        "question": "RAN1#118 회의에서 향후 표준화를 위해 설정된 Working Assumption들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 회의의 Working Assumption 목록",
        "parameters": {"meeting": "RAN1#118"}
    },
]

# CQ1-4: Agenda별 Resolution 조회 (5 cases)
cq1_4_cases = [
    # 전략 관점 - 특정 기술 주제에 대한 결정사항
    {
        "id": "TC-016",
        "cq_type": "CQ1-4",
        "perspective": "전략",
        "question": "RAN1#112 회의 Agenda 8.1 MIMO 관련 기술 결정사항들을 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 Agenda 8.1의 Resolution 목록",
        "parameters": {"meeting": "RAN1#112", "agenda_pattern": "8.1"}
    },
    {
        "id": "TC-017",
        "cq_type": "CQ1-4",
        "perspective": "전략",
        "question": "RAN1#118 회의에서 beam management 관련 아젠다의 결정 내용이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 Agenda 9.1 관련 Resolution 목록",
        "parameters": {"meeting": "RAN1#118", "agenda_pattern": "9.1"}
    },
    # IP 관점 - 특정 아젠다에서 채택된 기술
    {
        "id": "TC-018",
        "cq_type": "CQ1-4",
        "perspective": "IP",
        "question": "RAN1#103 회의 positioning 관련 아젠다에서 합의된 내용을 특허 검토용으로 확인하려고 해",
        "expected_result_type": "list",
        "expected_answer": "RAN1#103 positioning 관련 Agenda Resolution",
        "parameters": {"meeting": "RAN1#103", "agenda_pattern": "8.5"}
    },
    {
        "id": "TC-019",
        "cq_type": "CQ1-4",
        "perspective": "IP",
        "question": "RAN1#88 회의 Agenda 7.2에서 어떤 기술이 표준으로 채택됐어?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#88 Agenda 7.2 Resolution 목록",
        "parameters": {"meeting": "RAN1#88", "agenda_pattern": "7.2"}
    },
    {
        "id": "TC-020",
        "cq_type": "CQ1-4",
        "perspective": "전략",
        "question": "RAN1#110 회의 maintenance 관련 아젠다 결정사항 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#110 maintenance Agenda Resolution",
        "parameters": {"meeting": "RAN1#110", "agenda_pattern": "8"}
    },
]

# CQ1-5: 키워드별 Resolution 조회 (5 cases)
cq1_5_cases = [
    # 전략 관점 - 기술 트렌드 파악
    {
        "id": "TC-021",
        "cq_type": "CQ1-5",
        "perspective": "전략",
        "question": "URLLC 관련 표준 결정사항들 중에서 주요 내용을 알려줘",
        "expected_result_type": "list",
        "expected_answer": "URLLC 관련 Resolution 목록",
        "parameters": {"keyword": "URLLC"}
    },
    {
        "id": "TC-022",
        "cq_type": "CQ1-5",
        "perspective": "전략",
        "question": "sidelink 기술 관련해서 어떤 결정들이 내려졌어?",
        "expected_result_type": "list",
        "expected_answer": "sidelink 관련 Resolution 목록",
        "parameters": {"keyword": "sidelink"}
    },
    # IP 관점 - 특정 기술 특허 검토
    {
        "id": "TC-023",
        "cq_type": "CQ1-5",
        "perspective": "IP",
        "question": "DCI 관련 표준 결정사항을 특허 분석을 위해 확인하고 싶어",
        "expected_result_type": "list",
        "expected_answer": "DCI 관련 Resolution 목록",
        "parameters": {"keyword": "DCI"}
    },
    {
        "id": "TC-024",
        "cq_type": "CQ1-5",
        "perspective": "IP",
        "question": "HARQ 관련 Agreement 내용 중 기술 특허와 연관될 수 있는 것들 보여줘",
        "expected_result_type": "list",
        "expected_answer": "HARQ 관련 Resolution 목록",
        "parameters": {"keyword": "HARQ"}
    },
    {
        "id": "TC-025",
        "cq_type": "CQ1-5",
        "perspective": "전략",
        "question": "CSI feedback 관련 표준 결정들이 어떻게 됐어?",
        "expected_result_type": "list",
        "expected_answer": "CSI 관련 Resolution 목록",
        "parameters": {"keyword": "CSI"}
    },
]

# =============================================================================
# CQ2: Tdoc ↔ Resolution 추적
# =============================================================================

# CQ2-1: Resolution이 참조한 Tdoc 조회 (10 cases)
cq2_1_cases = [
    # IP 관점 - 기여 증거 확보
    {
        "id": "TC-026",
        "cq_type": "CQ2-1",
        "perspective": "IP",
        "question": "Agreement AGR-87-7.1.3.2-011이 참조한 기고서 목록을 확인하고 싶어. 우리 회사 기고가 포함됐는지 확인해야 해",
        "expected_result_type": "list",
        "expected_answer": "AGR-87-7.1.3.2-011이 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-87-7.1.3.2-011"}
    },
    {
        "id": "TC-027",
        "cq_type": "CQ2-1",
        "perspective": "IP",
        "question": "이 Agreement AGR-122b-11.1-003에 반영된 기고서들이 뭐야? 기여 증거로 확보해야 해",
        "expected_result_type": "list",
        "expected_answer": "AGR-122b-11.1-003이 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-122b-11.1-003"}
    },
    {
        "id": "TC-028",
        "cq_type": "CQ2-1",
        "perspective": "IP",
        "question": "AGR-86b-8.1.4.4-008 결정에 우리 기고가 반영됐는지 확인하려고 해. 참조된 Tdoc 보여줘",
        "expected_result_type": "list",
        "expected_answer": "AGR-86b-8.1.4.4-008이 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-86b-8.1.4.4-008"}
    },
    # 전략 관점 - 경쟁사 기여 분석
    {
        "id": "TC-029",
        "cq_type": "CQ2-1",
        "perspective": "전략",
        "question": "AGR-88-8.1.10-008 결정에 어떤 회사들의 기고가 반영됐는지 파악하고 싶어",
        "expected_result_type": "list",
        "expected_answer": "AGR-88-8.1.10-008이 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-88-8.1.10-008"}
    },
    {
        "id": "TC-030",
        "cq_type": "CQ2-1",
        "perspective": "전략",
        "question": "AGR-122b-11.3.1-004 합의에 기여한 기고서들 목록을 줘",
        "expected_result_type": "list",
        "expected_answer": "AGR-122b-11.3.1-004가 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-122b-11.3.1-004"}
    },
    {
        "id": "TC-031",
        "cq_type": "CQ2-1",
        "perspective": "IP",
        "question": "AGR-89-7.1.3.3.5-004 결정문에 참조된 Tdoc들 보여줘",
        "expected_result_type": "list",
        "expected_answer": "AGR-89-7.1.3.3.5-004가 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-89-7.1.3.3.5-004"}
    },
    {
        "id": "TC-032",
        "cq_type": "CQ2-1",
        "perspective": "전략",
        "question": "AGR-122b-10.3.2-029에 반영된 기고들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "AGR-122b-10.3.2-029가 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-122b-10.3.2-029"}
    },
    {
        "id": "TC-033",
        "cq_type": "CQ2-1",
        "perspective": "IP",
        "question": "AGR-122b-11.5-012 결정에서 참조된 기고서 목록 확인해줘",
        "expected_result_type": "list",
        "expected_answer": "AGR-122b-11.5-012가 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-122b-11.5-012"}
    },
    {
        "id": "TC-034",
        "cq_type": "CQ2-1",
        "perspective": "전략",
        "question": "AGR-86b-8.1.4.2-010 합의 도출에 기여한 Tdoc들 알려줘",
        "expected_result_type": "list",
        "expected_answer": "AGR-86b-8.1.4.2-010가 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-86b-8.1.4.2-010"}
    },
    {
        "id": "TC-035",
        "cq_type": "CQ2-1",
        "perspective": "IP",
        "question": "AGR-122b-11.3.2-004에서 인용된 기고서들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "AGR-122b-11.3.2-004가 참조한 Tdoc 목록",
        "parameters": {"resolution_id": "AGR-122b-11.3.2-004"}
    },
]

# CQ2-2: 특정 조건의 Resolution 조회 (10 cases)
cq2_2_cases = [
    # 전략 관점 - 중요 결정 파악
    {
        "id": "TC-036",
        "cq_type": "CQ2-2",
        "perspective": "전략",
        "question": "가장 많은 기고서가 반영된 중요한 표준 결정들 Top 10 알려줘",
        "expected_result_type": "ranked_list",
        "expected_answer": "Tdoc 참조가 많은 Resolution Top 10",
        "parameters": {"min_refs": 30}
    },
    {
        "id": "TC-037",
        "cq_type": "CQ2-2",
        "perspective": "전략",
        "question": "RAN1#88 회의에서 논의가 가장 활발했던 (기고서 참조가 많은) 결정들이 뭐야?",
        "expected_result_type": "ranked_list",
        "expected_answer": "RAN1#88 회의에서 Tdoc 참조가 많은 Resolution",
        "parameters": {"meeting": "RAN1#88", "min_refs": 20}
    },
    # IP 관점 - 핵심 표준 결정 파악
    {
        "id": "TC-038",
        "cq_type": "CQ2-2",
        "perspective": "IP",
        "question": "50개 이상의 기고가 반영된 핵심 표준 결정들 보여줘. 특허 분석 대상이야",
        "expected_result_type": "ranked_list",
        "expected_answer": "50개 이상 Tdoc 참조 Resolution",
        "parameters": {"min_refs": 50}
    },
    {
        "id": "TC-039",
        "cq_type": "CQ2-2",
        "perspective": "IP",
        "question": "RAN1#122b 회의에서 많은 기고가 반영된 결정들 목록 줘",
        "expected_result_type": "ranked_list",
        "expected_answer": "RAN1#122b 회의 다참조 Resolution",
        "parameters": {"meeting": "RAN1#122b", "min_refs": 30}
    },
    {
        "id": "TC-040",
        "cq_type": "CQ2-2",
        "perspective": "전략",
        "question": "RAN1#86b 회의에서 활발한 논의 끝에 도출된 주요 결정들이 뭐야?",
        "expected_result_type": "ranked_list",
        "expected_answer": "RAN1#86b 회의 다참조 Resolution",
        "parameters": {"meeting": "RAN1#86b", "min_refs": 30}
    },
    {
        "id": "TC-041",
        "cq_type": "CQ2-2",
        "perspective": "전략",
        "question": "기고서 20개 이상 참조된 중요 결정들 순위대로 보여줘",
        "expected_result_type": "ranked_list",
        "expected_answer": "Tdoc 20개 이상 참조 Resolution 순위",
        "parameters": {"min_refs": 20}
    },
    {
        "id": "TC-042",
        "cq_type": "CQ2-2",
        "perspective": "IP",
        "question": "RAN1#87 회의에서 가장 논쟁이 많았던 (기고가 많이 참조된) 결정 알려줘",
        "expected_result_type": "ranked_list",
        "expected_answer": "RAN1#87 회의 다참조 Resolution",
        "parameters": {"meeting": "RAN1#87", "min_refs": 40}
    },
    {
        "id": "TC-043",
        "cq_type": "CQ2-2",
        "perspective": "전략",
        "question": "전체 회의 통틀어 기고서 참조가 많은 Resolution Top 5는?",
        "expected_result_type": "ranked_list",
        "expected_answer": "전체 Resolution 중 다참조 Top 5",
        "parameters": {"min_refs": 50, "limit": 5}
    },
    {
        "id": "TC-044",
        "cq_type": "CQ2-2",
        "perspective": "IP",
        "question": "RAN1#89 회의 결정 중 기고 참조가 40개 넘는 것들 있어?",
        "expected_result_type": "ranked_list",
        "expected_answer": "RAN1#89 회의 40+ 참조 Resolution",
        "parameters": {"meeting": "RAN1#89", "min_refs": 40}
    },
    {
        "id": "TC-045",
        "cq_type": "CQ2-2",
        "perspective": "전략",
        "question": "기고가 10개 이상 반영된 결정들 순위로 보여줘",
        "expected_result_type": "ranked_list",
        "expected_answer": "10+ Tdoc 참조 Resolution 순위",
        "parameters": {"min_refs": 10}
    },
]

# =============================================================================
# CQ3: 회사별 기여도 분석
# =============================================================================

# CQ3-1: 회사별 Summary 조회 (10 cases)
cq3_1_cases = [
    # 전략 관점 - 경쟁사 활동 파악
    {
        "id": "TC-046",
        "cq_type": "CQ3-1",
        "perspective": "전략",
        "question": "Huawei가 어떤 기술 주제에서 FL로 활동했는지 알려줘",
        "expected_result_type": "list",
        "expected_answer": "Huawei의 FL Summary 목록",
        "parameters": {"company": "Huawei", "role": "FL"}
    },
    {
        "id": "TC-047",
        "cq_type": "CQ3-1",
        "perspective": "전략",
        "question": "Ericsson이 Moderator로 주도한 기술 토론들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "Ericsson의 Summary 목록",
        "parameters": {"company": "Ericsson", "role": "Moderator"}
    },
    {
        "id": "TC-048",
        "cq_type": "CQ3-1",
        "perspective": "전략",
        "question": "Samsung이 Feature Lead로 참여한 기술 분야 알려줘",
        "expected_result_type": "list",
        "expected_answer": "Samsung의 FL Summary 목록",
        "parameters": {"company": "Samsung", "role": "FL"}
    },
    # IP 관점 - 우리 회사 기여 증거
    {
        "id": "TC-049",
        "cq_type": "CQ3-1",
        "perspective": "IP",
        "question": "Qualcomm이 표준 논의를 주도한 기록들 보여줘. 기여 증거로 활용하려고",
        "expected_result_type": "list",
        "expected_answer": "Qualcomm의 Summary 목록",
        "parameters": {"company": "Qualcomm"}
    },
    {
        "id": "TC-050",
        "cq_type": "CQ3-1",
        "perspective": "IP",
        "question": "Nokia가 FL Summary 작성한 목록 줘",
        "expected_result_type": "list",
        "expected_answer": "Nokia의 FL Summary 목록",
        "parameters": {"company": "Nokia", "role": "FL"}
    },
    {
        "id": "TC-051",
        "cq_type": "CQ3-1",
        "perspective": "전략",
        "question": "ZTE가 어떤 기술 논의에서 Moderator 역할을 했어?",
        "expected_result_type": "list",
        "expected_answer": "ZTE의 Moderator Summary 목록",
        "parameters": {"company": "ZTE", "role": "Moderator"}
    },
    {
        "id": "TC-052",
        "cq_type": "CQ3-1",
        "perspective": "IP",
        "question": "CATT가 주도한 기술 토론 Summary 목록 확인해줘",
        "expected_result_type": "list",
        "expected_answer": "CATT의 Summary 목록",
        "parameters": {"company": "CATT"}
    },
    {
        "id": "TC-053",
        "cq_type": "CQ3-1",
        "perspective": "전략",
        "question": "vivo가 Feature Lead로 작성한 Summary들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "vivo의 FL Summary 목록",
        "parameters": {"company": "vivo", "role": "FL"}
    },
    {
        "id": "TC-054",
        "cq_type": "CQ3-1",
        "perspective": "IP",
        "question": "MediaTek이 표준 논의에서 담당한 Summary들 보여줘",
        "expected_result_type": "list",
        "expected_answer": "MediaTek의 Summary 목록",
        "parameters": {"company": "MediaTek"}
    },
    {
        "id": "TC-055",
        "cq_type": "CQ3-1",
        "perspective": "전략",
        "question": "OPPO가 FL 역할을 수행한 기술 분야들 알려줘",
        "expected_result_type": "list",
        "expected_answer": "OPPO의 FL Summary 목록",
        "parameters": {"company": "OPPO", "role": "FL"}
    },
]

# CQ3-2: 회사별 기여도 순위 (5 cases)
cq3_2_cases = [
    # 전략 관점 - 경쟁사 동향
    {
        "id": "TC-056",
        "cq_type": "CQ3-2",
        "perspective": "전략",
        "question": "FL Summary를 가장 많이 작성한 회사 Top 10 알려줘. 표준화 리더십 파악하려고",
        "expected_result_type": "ranked_list",
        "expected_answer": "FL Summary 작성 Top 10 회사",
        "parameters": {"limit": 10}
    },
    {
        "id": "TC-057",
        "cq_type": "CQ3-2",
        "perspective": "전략",
        "question": "표준화 논의를 가장 활발하게 주도한 회사 순위가 어떻게 돼?",
        "expected_result_type": "ranked_list",
        "expected_answer": "Summary 작성 회사 순위",
        "parameters": {"limit": 15}
    },
    {
        "id": "TC-058",
        "cq_type": "CQ3-2",
        "perspective": "IP",
        "question": "Moderator Summary 작성 회사 순위 보여줘. 핵심 기여사 파악하려고",
        "expected_result_type": "ranked_list",
        "expected_answer": "Moderator Summary 작성 회사 순위",
        "parameters": {"type": "Moderator", "limit": 10}
    },
    {
        "id": "TC-059",
        "cq_type": "CQ3-2",
        "perspective": "전략",
        "question": "전체 Summary 기준 표준화 기여도 Top 5 회사는?",
        "expected_result_type": "ranked_list",
        "expected_answer": "전체 Summary Top 5 회사",
        "parameters": {"limit": 5}
    },
    {
        "id": "TC-060",
        "cq_type": "CQ3-2",
        "perspective": "IP",
        "question": "Feature Lead 활동이 많은 회사 Top 20 알려줘",
        "expected_result_type": "ranked_list",
        "expected_answer": "FL Summary Top 20 회사",
        "parameters": {"type": "FL", "limit": 20}
    },
]

# CQ3-3: 회사간 비교 (5 cases)
cq3_3_cases = [
    # 전략 관점 - 경쟁사 비교
    {
        "id": "TC-061",
        "cq_type": "CQ3-3",
        "perspective": "전략",
        "question": "Huawei와 Ericsson의 표준화 기여도 비교해줘",
        "expected_result_type": "comparison",
        "expected_answer": "Huawei vs Ericsson Summary 비교",
        "parameters": {"company1": "Huawei", "company2": "Ericsson"}
    },
    {
        "id": "TC-062",
        "cq_type": "CQ3-3",
        "perspective": "전략",
        "question": "Samsung과 Qualcomm 중 누가 더 활발하게 표준 논의를 주도했어?",
        "expected_result_type": "comparison",
        "expected_answer": "Samsung vs Qualcomm Summary 비교",
        "parameters": {"company1": "Samsung", "company2": "Qualcomm"}
    },
    {
        "id": "TC-063",
        "cq_type": "CQ3-3",
        "perspective": "IP",
        "question": "Nokia와 ZTE의 FL Summary 작성 횟수 비교해줘",
        "expected_result_type": "comparison",
        "expected_answer": "Nokia vs ZTE FL Summary 비교",
        "parameters": {"company1": "Nokia", "company2": "ZTE"}
    },
    {
        "id": "TC-064",
        "cq_type": "CQ3-3",
        "perspective": "전략",
        "question": "vivo와 OPPO 중 어느 회사가 표준화에 더 많이 기여했어?",
        "expected_result_type": "comparison",
        "expected_answer": "vivo vs OPPO Summary 비교",
        "parameters": {"company1": "vivo", "company2": "OPPO"}
    },
    {
        "id": "TC-065",
        "cq_type": "CQ3-3",
        "perspective": "IP",
        "question": "CATT와 MediaTek의 표준 기여 비교 분석해줘",
        "expected_result_type": "comparison",
        "expected_answer": "CATT vs MediaTek Summary 비교",
        "parameters": {"company1": "CATT", "company2": "MediaTek"}
    },
]

# =============================================================================
# CQ4: 역할 분석 (Session Notes, Summary)
# =============================================================================

# CQ4-1: Session Notes 조회 (5 cases)
cq4_1_cases = [
    # 전략 관점 - 회의 세션 파악
    {
        "id": "TC-066",
        "cq_type": "CQ4-1",
        "perspective": "전략",
        "question": "RAN1#112 회의에서 어떤 Ad-hoc 세션들이 있었어?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 Session Notes 목록",
        "parameters": {"meeting": "RAN1#112"}
    },
    {
        "id": "TC-067",
        "cq_type": "CQ4-1",
        "perspective": "전략",
        "question": "RAN1#118 회의의 Session Notes 목록 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 Session Notes 목록",
        "parameters": {"meeting": "RAN1#118"}
    },
    # IP 관점 - 세션별 논의 확인
    {
        "id": "TC-068",
        "cq_type": "CQ4-1",
        "perspective": "IP",
        "question": "RAN1#115 회의 Session Notes 확인해줘. 세션별 논의 내용 파악하려고",
        "expected_result_type": "list",
        "expected_answer": "RAN1#115 Session Notes 목록",
        "parameters": {"meeting": "RAN1#115"}
    },
    {
        "id": "TC-069",
        "cq_type": "CQ4-1",
        "perspective": "IP",
        "question": "RAN1#110 회의에서 진행된 세션들 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#110 Session Notes 목록",
        "parameters": {"meeting": "RAN1#110"}
    },
    {
        "id": "TC-070",
        "cq_type": "CQ4-1",
        "perspective": "전략",
        "question": "RAN1#120 회의의 Ad-hoc 세션 노트들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#120 Session Notes 목록",
        "parameters": {"meeting": "RAN1#120"}
    },
]

# CQ4-2: FL Summary 조회 (5 cases)
cq4_2_cases = [
    # 전략 관점 - 기술별 논의 파악
    {
        "id": "TC-071",
        "cq_type": "CQ4-2",
        "perspective": "전략",
        "question": "RAN1#112 회의에서 작성된 FL Summary 목록 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 FL Summary 목록",
        "parameters": {"meeting": "RAN1#112", "type": "FL"}
    },
    {
        "id": "TC-072",
        "cq_type": "CQ4-2",
        "perspective": "전략",
        "question": "RAN1#118 회의의 Feature Lead Summary들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 FL Summary 목록",
        "parameters": {"meeting": "RAN1#118", "type": "FL"}
    },
    # IP 관점 - 기술 논의 기록 확보
    {
        "id": "TC-073",
        "cq_type": "CQ4-2",
        "perspective": "IP",
        "question": "RAN1#103 회의 FL Summary 목록 확인해줘. 기술 논의 흐름 파악하려고",
        "expected_result_type": "list",
        "expected_answer": "RAN1#103 FL Summary 목록",
        "parameters": {"meeting": "RAN1#103", "type": "FL"}
    },
    {
        "id": "TC-074",
        "cq_type": "CQ4-2",
        "perspective": "IP",
        "question": "RAN1#109 회의에서 Feature Lead가 정리한 Summary들 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#109 FL Summary 목록",
        "parameters": {"meeting": "RAN1#109", "type": "FL"}
    },
    {
        "id": "TC-075",
        "cq_type": "CQ4-2",
        "perspective": "전략",
        "question": "RAN1#114 회의의 FL Summary 목록은?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#114 FL Summary 목록",
        "parameters": {"meeting": "RAN1#114", "type": "FL"}
    },
]

# CQ4-3: Moderator Summary 조회 (5 cases)
cq4_3_cases = [
    # 전략 관점
    {
        "id": "TC-076",
        "cq_type": "CQ4-3",
        "perspective": "전략",
        "question": "RAN1#112 회의에서 Moderator가 정리한 Summary들 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 Moderator Summary 목록",
        "parameters": {"meeting": "RAN1#112", "type": "Moderator"}
    },
    {
        "id": "TC-077",
        "cq_type": "CQ4-3",
        "perspective": "전략",
        "question": "RAN1#118 회의의 Moderator Summary 목록 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 Moderator Summary 목록",
        "parameters": {"meeting": "RAN1#118", "type": "Moderator"}
    },
    # IP 관점
    {
        "id": "TC-078",
        "cq_type": "CQ4-3",
        "perspective": "IP",
        "question": "RAN1#100 회의 Moderator Summary 확인해줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#100 Moderator Summary 목록",
        "parameters": {"meeting": "RAN1#100", "type": "Moderator"}
    },
    {
        "id": "TC-079",
        "cq_type": "CQ4-3",
        "perspective": "IP",
        "question": "RAN1#106 회의에서 Moderator가 작성한 Summary들이 뭐야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#106 Moderator Summary 목록",
        "parameters": {"meeting": "RAN1#106", "type": "Moderator"}
    },
    {
        "id": "TC-080",
        "cq_type": "CQ4-3",
        "perspective": "전략",
        "question": "RAN1#110 회의 Moderator Summary 목록은?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#110 Moderator Summary 목록",
        "parameters": {"meeting": "RAN1#110", "type": "Moderator"}
    },
]

# CQ4-4: Ad-hoc Chair 회사 조회 (5 cases)
cq4_4_cases = [
    # 전략 관점 - 세션 주관 회사 파악
    {
        "id": "TC-081",
        "cq_type": "CQ4-4",
        "perspective": "전략",
        "question": "RAN1#112 회의 Ad-hoc 세션을 어떤 회사들이 주관했어?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#112 Ad-hoc Chair 회사 목록",
        "parameters": {"meeting": "RAN1#112"}
    },
    {
        "id": "TC-082",
        "cq_type": "CQ4-4",
        "perspective": "전략",
        "question": "RAN1#118 회의에서 Ad-hoc Chair 역할을 맡은 회사들 알려줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#118 Ad-hoc Chair 회사 목록",
        "parameters": {"meeting": "RAN1#118"}
    },
    # IP 관점 - 기여 증거
    {
        "id": "TC-083",
        "cq_type": "CQ4-4",
        "perspective": "IP",
        "question": "RAN1#110 회의 세션 주관 회사들 확인해줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#110 Ad-hoc Chair 회사 목록",
        "parameters": {"meeting": "RAN1#110"}
    },
    {
        "id": "TC-084",
        "cq_type": "CQ4-4",
        "perspective": "IP",
        "question": "RAN1#100 회의에서 Ad-hoc Session을 주관한 회사가 어디야?",
        "expected_result_type": "list",
        "expected_answer": "RAN1#100 Ad-hoc Chair 회사 목록",
        "parameters": {"meeting": "RAN1#100"}
    },
    {
        "id": "TC-085",
        "cq_type": "CQ4-4",
        "perspective": "전략",
        "question": "RAN1#103 회의 Ad-hoc Chair 회사 목록 보여줘",
        "expected_result_type": "list",
        "expected_answer": "RAN1#103 Ad-hoc Chair 회사 목록",
        "parameters": {"meeting": "RAN1#103"}
    },
]

# =============================================================================
# CQ6: 트렌드/비교 분석
# =============================================================================

# CQ6-1: 회의별 Resolution 추이 (5 cases)
cq6_1_cases = [
    # 전략 관점 - 표준화 활동 추이
    {
        "id": "TC-086",
        "cq_type": "CQ6-1",
        "perspective": "전략",
        "question": "최근 회의들의 Resolution 수 추이가 어떻게 돼? 표준화 활동량 파악하려고",
        "expected_result_type": "trend",
        "expected_answer": "최근 회의별 Resolution 수 추이",
        "parameters": {"period": "recent"}
    },
    {
        "id": "TC-087",
        "cq_type": "CQ6-1",
        "perspective": "전략",
        "question": "Rel-17 시기 회의들의 Resolution 수 변화 추이 알려줘",
        "expected_result_type": "trend",
        "expected_answer": "Rel-17 시기 Resolution 추이",
        "parameters": {"period": "rel17"}
    },
    {
        "id": "TC-088",
        "cq_type": "CQ6-1",
        "perspective": "IP",
        "question": "초기 NR 표준화 시기 회의별 Decision 수 추이 보여줘",
        "expected_result_type": "trend",
        "expected_answer": "초기 NR 표준화 Resolution 추이",
        "parameters": {"period": "early_nr"}
    },
    {
        "id": "TC-089",
        "cq_type": "CQ6-1",
        "perspective": "전략",
        "question": "전체 회의 기간 동안 표준 결정 수 추이가 어떻게 변했어?",
        "expected_result_type": "trend",
        "expected_answer": "전체 기간 Resolution 추이",
        "parameters": {"period": "all"}
    },
    {
        "id": "TC-090",
        "cq_type": "CQ6-1",
        "perspective": "IP",
        "question": "RAN1#100부터 RAN1#110까지 회의별 Resolution 수 보여줘",
        "expected_result_type": "trend",
        "expected_answer": "RAN1#100~110 Resolution 추이",
        "parameters": {"start": "RAN1#100", "end": "RAN1#110"}
    },
]

# CQ6-2: Resolution 유형별 분포 (5 cases)
cq6_2_cases = [
    # 전략 관점 - 결정 유형 분석
    {
        "id": "TC-091",
        "cq_type": "CQ6-2",
        "perspective": "전략",
        "question": "전체 Resolution 중 Agreement, Conclusion, WA 비율이 어떻게 돼?",
        "expected_result_type": "distribution",
        "expected_answer": "전체 Resolution 유형별 분포",
        "parameters": {"scope": "all"}
    },
    {
        "id": "TC-092",
        "cq_type": "CQ6-2",
        "perspective": "전략",
        "question": "RAN1#112 회의 Resolution 유형별 분포 알려줘",
        "expected_result_type": "distribution",
        "expected_answer": "RAN1#112 Resolution 유형 분포",
        "parameters": {"meeting": "RAN1#112"}
    },
    {
        "id": "TC-093",
        "cq_type": "CQ6-2",
        "perspective": "IP",
        "question": "RAN1#118 회의에서 Agreement vs Conclusion 비율이 어떻게 돼?",
        "expected_result_type": "distribution",
        "expected_answer": "RAN1#118 Resolution 유형 분포",
        "parameters": {"meeting": "RAN1#118"}
    },
    {
        "id": "TC-094",
        "cq_type": "CQ6-2",
        "perspective": "IP",
        "question": "RAN1#100 회의 결정 유형별 분포 확인해줘",
        "expected_result_type": "distribution",
        "expected_answer": "RAN1#100 Resolution 유형 분포",
        "parameters": {"meeting": "RAN1#100"}
    },
    {
        "id": "TC-095",
        "cq_type": "CQ6-2",
        "perspective": "전략",
        "question": "RAN1#103 회의에서 Agreement가 몇 퍼센트야?",
        "expected_result_type": "distribution",
        "expected_answer": "RAN1#103 Resolution 유형 분포",
        "parameters": {"meeting": "RAN1#103"}
    },
]

# CQ6-3: 통계 분석 (5 cases)
cq6_3_cases = [
    # 전략 관점 - 전체 통계
    {
        "id": "TC-096",
        "cq_type": "CQ6-3",
        "perspective": "전략",
        "question": "회의당 평균 Resolution 수가 어떻게 돼?",
        "expected_result_type": "statistics",
        "expected_answer": "회의당 평균 Resolution 수",
        "parameters": {"stat_type": "avg"}
    },
    {
        "id": "TC-097",
        "cq_type": "CQ6-3",
        "perspective": "전략",
        "question": "가장 많은 결정이 나온 회의가 어디야?",
        "expected_result_type": "statistics",
        "expected_answer": "Resolution 최다 회의",
        "parameters": {"stat_type": "max"}
    },
    {
        "id": "TC-098",
        "cq_type": "CQ6-3",
        "perspective": "IP",
        "question": "Resolution 수가 가장 적었던 회의는?",
        "expected_result_type": "statistics",
        "expected_answer": "Resolution 최소 회의",
        "parameters": {"stat_type": "min"}
    },
    {
        "id": "TC-099",
        "cq_type": "CQ6-3",
        "perspective": "IP",
        "question": "Agreement와 Conclusion의 전체 비율은?",
        "expected_result_type": "statistics",
        "expected_answer": "Agreement vs Conclusion 비율",
        "parameters": {"stat_type": "ratio"}
    },
    {
        "id": "TC-100",
        "cq_type": "CQ6-3",
        "perspective": "전략",
        "question": "Tdoc을 참조하는 Resolution 비율이 어떻게 돼?",
        "expected_result_type": "statistics",
        "expected_answer": "Tdoc 참조 Resolution 비율",
        "parameters": {"stat_type": "ref_ratio"}
    },
]

# Combine all test cases
all_cases = (
    cq1_1_cases + cq1_2_cases + cq1_3_cases + cq1_4_cases + cq1_5_cases +
    cq2_1_cases + cq2_2_cases +
    cq3_1_cases + cq3_2_cases + cq3_3_cases +
    cq4_1_cases + cq4_2_cases + cq4_3_cases + cq4_4_cases +
    cq6_1_cases + cq6_2_cases + cq6_3_cases
)

# Calculate perspective distribution
strategy_count = sum(1 for c in all_cases if c.get("perspective") == "전략")
ip_count = sum(1 for c in all_cases if c.get("perspective") == "IP")

# Calculate CQ type distribution
cq_distribution = {}
for case in all_cases:
    cq_type = case["cq_type"]
    cq_distribution[cq_type] = cq_distribution.get(cq_type, 0) + 1

# Generate output
output = {
    "generated_at": datetime.now().isoformat(),
    "version": "3.0-realistic-dual-perspective",
    "design_principles": [
        "Spec 정의 Target User 준수: 전략/기획 + IP/특허",
        "자연어 질문: 실제 담당자가 할 만한 질문",
        "Context-rich: 구체적 기술/회사/회의 언급",
        "CQ Type Scope 준수: Spec 정의 범위 내 질문"
    ],
    "target_users": {
        "전략/기획": {
            "count": strategy_count,
            "focus": ["회의 결과 파악", "기술 트렌드 분석", "경쟁사 동향"]
        },
        "IP/특허": {
            "count": ip_count,
            "focus": ["기고의 표준 반영 여부", "기여 증거 확보"]
        }
    },
    "total_cases": len(all_cases),
    "cq_type_distribution": cq_distribution,
    "test_cases": all_cases
}

# Save
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Generated {len(all_cases)} test cases")
print(f"  - 전략/기획 관점: {strategy_count} cases ({strategy_count/len(all_cases)*100:.1f}%)")
print(f"  - IP/특허 관점: {ip_count} cases ({ip_count/len(all_cases)*100:.1f}%)")
print(f"\nCQ Type Distribution:")
for cq_type, count in sorted(cq_distribution.items()):
    print(f"  {cq_type}: {count}")
print(f"\nSaved to: {OUTPUT_PATH}")
