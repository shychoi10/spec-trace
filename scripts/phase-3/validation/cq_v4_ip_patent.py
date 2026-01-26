#!/usr/bin/env python3
"""
CQ v4.0: IP/특허 담당자 실무 관점 100개 질문 검증
- 직접 Cypher 쿼리로 Neo4j 검증
- 상세 답변 포함 리포트 생성
"""

import json
from datetime import datetime
from neo4j import GraphDatabase
from pathlib import Path

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password123")

# CQ 100개 정의: (id, category, question, cypher_query)
CQ_DATASET = [
    # ============================================================
    # Category 1: SSB/PSS/SSS/PBCH (1-20)
    # ============================================================
    ("CQ001", "SSB", "SSB 관련 합의된 내용 중 OFDM symbol 관련 내용을 알려줘",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'symbol' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ002", "SSB", "SSB burst set 관련 합의 내용을 보여줘",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'burst' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ003", "SSB", "PSS sequence 관련 결정 사항을 알려줘",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PSS' AND a.content CONTAINS 'sequence' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ004", "SSB", "SSS sequence length 관련 합의가 있어?",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSS' AND (a.content CONTAINS 'length' OR a.content CONTAINS 'sequence') RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ005", "SSB", "PBCH payload 관련 합의 내용을 알려줘",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PBCH' AND a.content CONTAINS 'payload' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ006", "SSB", "PBCH DMRS 관련 결정 사항이 있어?",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PBCH' AND a.content CONTAINS 'DMRS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ007", "SSB", "SSB periodicity 관련 합의를 보여줘",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'periodicity' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ008", "SSB", "SSB time domain 위치 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'time' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ009", "SSB", "SSB frequency domain 위치 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'frequency' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ010", "SSB", "SSB subcarrier spacing 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND (a.content CONTAINS 'SCS' OR a.content CONTAINS 'subcarrier spacing') RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ011", "SSB", "MIB content 관련 합의 내용",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'MIB' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ012", "SSB", "SSB index 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'index' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ013", "SSB", "Cell ID 결정 방식 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'cell' AND a.content CONTAINS 'ID' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ014", "SSB", "SSB beam sweeping 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'beam' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ015", "SSB", "Initial access 절차 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'initial access' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ016", "SSB", "SSB와 CORESET 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'CORESET' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ017", "SSB", "Half frame 관련 SSB 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'half frame' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ018", "SSB", "RMSI scheduling 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'RMSI' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ019", "SSB", "SSB measurement 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'measurement' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ020", "SSB", "FR1과 FR2에서 SSB 관련 차이점",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SSB' AND (a.content CONTAINS 'FR1' OR a.content CONTAINS 'FR2') RETURN a.resolutionId, a.content LIMIT 10"),
    
    # ============================================================
    # Category 2: MIMO/Beamforming (21-35)
    # ============================================================
    ("CQ021", "MIMO", "Massive MIMO 관련 합의 내용",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'MIMO' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ022", "MIMO", "Codebook 기반 precoding 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'codebook' AND a.content CONTAINS 'precoding' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ023", "MIMO", "Non-codebook 기반 전송 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'non-codebook' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ024", "MIMO", "CSI reporting 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'CSI' AND a.content CONTAINS 'report' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ025", "MIMO", "CSI-RS 설계 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'CSI-RS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ026", "MIMO", "SRS 설계 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'SRS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ027", "MIMO", "Beam management 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'beam management' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ028", "MIMO", "TCI state 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'TCI' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ029", "MIMO", "Beam failure recovery 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'beam failure' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ030", "MIMO", "Multi-panel 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'panel' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ031", "MIMO", "Layer 수 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'layer' AND a.content CONTAINS 'MIMO' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ032", "MIMO", "Antenna port 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'antenna port' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ033", "MIMO", "Rank indicator 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'rank' OR a.content CONTAINS 'RI' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ034", "MIMO", "PMI 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PMI' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ035", "MIMO", "CQI 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'CQI' RETURN a.resolutionId, a.content LIMIT 10"),
    
    # ============================================================
    # Category 3: Channel Coding/Modulation (36-50)
    # ============================================================
    ("CQ036", "Coding", "LDPC 코드 관련 합의 내용",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'LDPC' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ037", "Coding", "Polar 코드 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'Polar' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ038", "Coding", "Rate matching 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'rate matching' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ039", "Coding", "Interleaving 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'interleav' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ040", "Coding", "Code block segmentation 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'code block' OR a.content CONTAINS 'CB' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ041", "Coding", "QAM modulation order 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'QAM' OR a.content CONTAINS 'modulation order' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ042", "Coding", "MCS table 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'MCS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ043", "Coding", "Transport block 크기 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'transport block' OR a.content CONTAINS 'TBS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ044", "Coding", "CRC 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'CRC' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ045", "Coding", "Scrambling 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'scrambl' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ046", "Coding", "DMRS sequence 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'DMRS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ047", "Coding", "PTRS 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PTRS' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ048", "Coding", "Reference signal pattern 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'reference signal' AND a.content CONTAINS 'pattern' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ049", "Coding", "Repetition 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'repetition' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ050", "Coding", "HARQ 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'HARQ' RETURN a.resolutionId, a.content LIMIT 10"),
    
    # ============================================================
    # Category 4: Physical Channel Design (51-65)
    # ============================================================
    ("CQ051", "Channel", "PDSCH resource allocation 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PDSCH' AND a.content CONTAINS 'resource' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ052", "Channel", "PUSCH resource allocation 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PUSCH' AND a.content CONTAINS 'resource' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ053", "Channel", "PUCCH format 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PUCCH' AND a.content CONTAINS 'format' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ054", "Channel", "PRACH preamble 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PRACH' AND a.content CONTAINS 'preamble' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ055", "Channel", "PDCCH search space 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'PDCCH' AND a.content CONTAINS 'search space' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ056", "Channel", "DCI format 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'DCI' AND a.content CONTAINS 'format' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ057", "Channel", "UCI multiplexing 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'UCI' AND a.content CONTAINS 'multiplex' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ058", "Channel", "Slot structure 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'slot' AND a.content CONTAINS 'structure' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ059", "Channel", "Mini-slot 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'mini-slot' OR a.content CONTAINS 'non-slot' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ060", "Channel", "BWP 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'BWP' OR a.content CONTAINS 'bandwidth part' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ061", "Channel", "Power control 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'power control' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ062", "Channel", "Timing advance 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'timing advance' OR a.content CONTAINS 'TA' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ063", "Channel", "Processing time 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'processing time' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ064", "Channel", "Gap 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'gap' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ065", "Channel", "CORESET 설계 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'CORESET' RETURN a.resolutionId, a.content LIMIT 10"),
    
    # ============================================================
    # Category 5: Meeting/Decision Tracking (66-80)
    # ============================================================
    ("CQ066", "Meeting", "RAN1#91 회의에서 가장 많이 결정된 주제는?",
     "MATCH (a:Agreement)-[:MADEAT]->(m:Meeting) WHERE m.meetingNumber = 'RAN1#91' RETURN a.resolutionId, a.content LIMIT 15"),
    
    ("CQ067", "Meeting", "RAN1#112 회의의 주요 결정 사항",
     "MATCH (a:Agreement)-[:MADEAT]->(m:Meeting) WHERE m.meetingNumber = 'RAN1#112' RETURN a.resolutionId, a.content LIMIT 15"),
    
    ("CQ068", "Meeting", "RAN1#120 회의에서 MIMO 관련 결정",
     "MATCH (a:Agreement)-[:MADEAT]->(m:Meeting) WHERE m.meetingNumber = 'RAN1#120' AND a.content CONTAINS 'MIMO' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ069", "Meeting", "FFS로 남아있는 이슈들",
     "MATCH (a:Agreement) WHERE a.hasFFS = true RETURN a.resolutionId, a.content LIMIT 15"),
    
    ("CQ070", "Meeting", "TBD로 표시된 미결 사항들",
     "MATCH (a:Agreement) WHERE a.hasTBD = true RETURN a.resolutionId, a.content LIMIT 15"),
    
    ("CQ071", "Meeting", "Working Assumption 중 아직 Agreement로 승격 안된 것",
     "MATCH (wa:WorkingAssumption) RETURN wa.resolutionId, wa.content LIMIT 15"),
    
    ("CQ072", "Meeting", "특정 Agenda 9.1 관련 결정들",
     "MATCH (a:Agreement)-[:RESOLUTIONBELONGSTO]->(ag:AgendaItem) WHERE ag.agendaNumber STARTS WITH '9.1' RETURN a.resolutionId, a.content, ag.agendaNumber LIMIT 10"),
    
    ("CQ073", "Meeting", "2020년 이후 e-meeting에서의 결정 (COVID 시기)",
     "MATCH (a:Agreement)-[:MADEAT]->(m:Meeting) WHERE m.meetingNumber CONTAINS '-e' RETURN m.meetingNumber, count(a) AS cnt ORDER BY cnt DESC LIMIT 10"),
    
    ("CQ074", "Meeting", "Conclusion 유형의 결정들",
     "MATCH (c:Conclusion) RETURN c.resolutionId, c.content LIMIT 15"),
    
    ("CQ075", "Meeting", "가장 최근 회의(RAN1#122)의 주요 결정",
     "MATCH (a:Agreement)-[:MADEAT]->(m:Meeting) WHERE m.meetingNumber STARTS WITH 'RAN1#122' RETURN a.resolutionId, a.content LIMIT 15"),
    
    ("CQ076", "Meeting", "Rel-16 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'Rel-16' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ077", "Meeting", "Rel-17 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'Rel-17' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ078", "Meeting", "Rel-18 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'Rel-18' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ079", "Meeting", "eMBB 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'eMBB' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ080", "Meeting", "URLLC 관련 결정 사항",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'URLLC' RETURN a.resolutionId, a.content LIMIT 10"),
    
    # ============================================================
    # Category 6: LTE vs NR Comparison (81-90)
    # ============================================================
    ("CQ081", "Compare", "NR에서 새로 도입된 개념 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'NR' AND a.content CONTAINS 'new' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ082", "Compare", "LTE와 다른 NR 설계 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'LTE' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ083", "Compare", "Numerology 관련 결정 (LTE와 차이점)",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'numerology' OR a.content CONTAINS 'subcarrier spacing' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ084", "Compare", "Flexible slot 구조 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'flexible' AND a.content CONTAINS 'slot' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ085", "Compare", "mmWave 지원 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'mmWave' OR a.content CONTAINS 'FR2' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ086", "Compare", "Wideband carrier 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'carrier' AND (a.content CONTAINS 'wide' OR a.content CONTAINS '100 MHz') RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ087", "Compare", "Dynamic TDD 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'TDD' AND a.content CONTAINS 'dynamic' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ088", "Compare", "Self-contained slot 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'self-contained' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ089", "Compare", "Lean carrier 관련 결정",
     "MATCH (a:Agreement) WHERE a.content CONTAINS 'lean' OR a.content CONTAINS 'always-on' RETURN a.resolutionId, a.content LIMIT 10"),
    
    ("CQ090", "Compare", "5G 특화 기능 관련 합의",
     "MATCH (a:Agreement) WHERE a.content CONTAINS '5G' OR a.content CONTAINS 'New Radio' RETURN a.resolutionId, a.content LIMIT 10"),
    
    # ============================================================
    # Category 7: Company/Contributor Tracking (91-100)
    # ============================================================
    ("CQ091", "Company", "Samsung이 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'Samsung' RETURN count(t) AS total"),
    
    ("CQ092", "Company", "Qualcomm이 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'Qualcomm' RETURN count(t) AS total"),
    
    ("CQ093", "Company", "Huawei가 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'Huawei' RETURN count(t) AS total"),
    
    ("CQ094", "Company", "Ericsson이 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'Ericsson' RETURN count(t) AS total"),
    
    ("CQ095", "Company", "Nokia가 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'Nokia' RETURN count(t) AS total"),
    
    ("CQ096", "Company", "가장 많이 Tdoc을 제출한 회사 Top 10",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10"),
    
    ("CQ097", "Company", "Intel이 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'Intel' RETURN count(t) AS total"),
    
    ("CQ098", "Company", "LG Electronics가 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'LG' RETURN count(t) AS total"),
    
    ("CQ099", "Company", "ZTE가 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'ZTE' RETURN count(t) AS total"),
    
    ("CQ100", "Company", "CATT가 제출한 Tdoc 수",
     "MATCH (t:Tdoc)-[:SUBMITTEDBY]->(c:Company) WHERE c.companyName CONTAINS 'CATT' RETURN count(t) AS total"),
]


def run_validation():
    """CQ 100개 검증 실행"""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    results = []
    
    print("=" * 80)
    print("CQ v4.0: IP/특허 담당자 실무 관점 100개 질문 검증")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    pass_count = 0
    no_data_count = 0
    fail_count = 0
    
    with driver.session() as session:
        for cq_id, category, question, query in CQ_DATASET:
            try:
                result = session.run(query)
                records = list(result)
                
                if len(records) > 0:
                    status = "PASS"
                    pass_count += 1
                else:
                    status = "NO_DATA"
                    no_data_count += 1
                
                # 결과 저장
                answer_data = []
                for rec in records[:5]:  # 최대 5개만 저장
                    rec_dict = dict(rec)
                    answer_data.append(rec_dict)
                
                results.append({
                    "id": cq_id,
                    "category": category,
                    "question": question,
                    "query": query,
                    "status": status,
                    "result_count": len(records),
                    "sample_answers": answer_data
                })
                
                print(f"[{cq_id}] {status} ({len(records)}건) - {category}: {question[:50]}...")
                
            except Exception as e:
                fail_count += 1
                results.append({
                    "id": cq_id,
                    "category": category,
                    "question": question,
                    "query": query,
                    "status": "FAIL",
                    "error": str(e),
                    "result_count": 0,
                    "sample_answers": []
                })
                print(f"[{cq_id}] FAIL - {str(e)[:50]}")
    
    driver.close()
    
    # 요약 출력
    print()
    print("=" * 80)
    print("검증 결과 요약")
    print("=" * 80)
    print(f"PASS: {pass_count}개 ({pass_count}%)")
    print(f"NO_DATA: {no_data_count}개 ({no_data_count}%)")
    print(f"FAIL: {fail_count}개 ({fail_count}%)")
    print(f"쿼리 성공률: {(pass_count + no_data_count)}%")
    
    # 카테고리별 결과
    print()
    print("카테고리별 결과:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"pass": 0, "no_data": 0, "fail": 0}
        if r["status"] == "PASS":
            categories[cat]["pass"] += 1
        elif r["status"] == "NO_DATA":
            categories[cat]["no_data"] += 1
        else:
            categories[cat]["fail"] += 1
    
    for cat, counts in categories.items():
        total = counts["pass"] + counts["no_data"] + counts["fail"]
        print(f"  {cat}: PASS {counts['pass']}/{total}, NO_DATA {counts['no_data']}, FAIL {counts['fail']}")
    
    # 결과 저장
    output_path = Path("/home/sihyeon/workspace/spec-trace/logs/phase-3/cq_v4_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "version": "4.0",
                "date": datetime.now().isoformat(),
                "total": 100,
                "pass": pass_count,
                "no_data": no_data_count,
                "fail": fail_count
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과 저장: {output_path}")
    
    return results


if __name__ == "__main__":
    run_validation()
