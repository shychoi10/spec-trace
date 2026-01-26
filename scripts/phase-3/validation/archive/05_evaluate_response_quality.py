#!/usr/bin/env python3
"""
Phase-3 CQ Validation: 응답 품질 평가 스크립트

PASS로 표시된 응답의 신뢰도를 다각도로 평가:
1. Factual Accuracy (사실 정확성): 응답의 resolutionId가 실제 DB에 존재하는지
2. Query Relevance (쿼리 관련성): Cypher 쿼리가 질문 의도를 정확히 반영하는지
3. Answer Completeness (답변 완전성): 반환된 데이터를 적절히 요약했는지
4. Hallucination Detection (환각 탐지): 존재하지 않는 정보를 생성했는지
"""

import json
import re
import os
from pathlib import Path
from neo4j import GraphDatabase
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
RESULTS_FILE = BASE_DIR / "logs" / "phase-3" / "cq_llamaindex_results.json"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


def extract_resolution_ids(text: str) -> list:
    """응답에서 resolutionId 패턴 추출"""
    # AGR-99-7.2.9.3-001, CON-100-8.5-002 등의 패턴
    pattern = r'(AGR|CON|WA)-\d+[a-z]?-[\d\.]+(-\d+)?'
    return re.findall(pattern, text, re.IGNORECASE)


def extract_full_resolution_ids(text: str) -> list:
    """전체 resolutionId 추출 (prefix 포함)"""
    pattern = r'(AGR-\d+[a-z]?-[\d\.]+-\d+|CON-\d+[a-z]?-[\d\.]+-\d+|WA-\d+[a-z]?-[\d\.]+-\d+)'
    return re.findall(pattern, text, re.IGNORECASE)


def verify_resolution_ids(driver, resolution_ids: list) -> dict:
    """resolutionId가 실제 DB에 존재하는지 확인"""
    result = {
        "total": len(resolution_ids),
        "verified": 0,
        "missing": [],
        "verified_ids": []
    }

    with driver.session() as session:
        for rid in resolution_ids:
            query = """
            MATCH (r:Resolution)
            WHERE r.resolutionId = $rid
            RETURN count(r) as cnt
            """
            res = session.run(query, rid=rid)
            cnt = res.single()['cnt']
            if cnt > 0:
                result["verified"] += 1
                result["verified_ids"].append(rid)
            else:
                result["missing"].append(rid)

    return result


def evaluate_query_relevance(question: str, cypher: str) -> dict:
    """Cypher 쿼리가 질문 의도를 반영하는지 평가"""
    score = 0
    issues = []

    # 1. 질문의 핵심 키워드가 쿼리에 포함되는지
    question_lower = question.lower()
    cypher_lower = cypher.lower() if cypher else ""

    # 기술 키워드 매핑
    tech_keywords = {
        'mimo': 'MIMO',
        'ntn': 'NTN',
        'positioning': 'positioning',
        'ai/ml': ['AI', 'ML'],
        'urllc': 'URLLC',
        'sidelink': 'sidelink',
        'beam': 'beam',
        'power saving': 'power',
        'redcap': 'RedCap',
        'csi': 'CSI',
        'ffs': ['FFS', 'hasFFS'],
        'tbd': ['TBD', 'hasTBD'],
    }

    keyword_found = False
    for q_key, c_key in tech_keywords.items():
        if q_key in question_lower:
            if isinstance(c_key, list):
                if any(k.lower() in cypher_lower for k in c_key):
                    keyword_found = True
                    score += 30
                    break
            else:
                if c_key.lower() in cypher_lower:
                    keyword_found = True
                    score += 30
                    break

    if not keyword_found and cypher:
        # 일반적인 키워드 매칭 시도
        words = re.findall(r'\b[가-힣a-zA-Z]+\b', question)
        for word in words:
            if len(word) > 2 and word.lower() in cypher_lower:
                score += 20
                keyword_found = True
                break

    if not keyword_found:
        issues.append("질문 키워드가 쿼리에 미반영")

    # 2. 적절한 노드 타입 사용
    if 'agreement' in question_lower or '합의' in question_lower:
        if 'agreement' in cypher_lower:
            score += 20
        else:
            issues.append("Agreement 노드 미사용")

    if 'conclusion' in question_lower or '결론' in question_lower:
        if 'conclusion' in cypher_lower:
            score += 20
        else:
            issues.append("Conclusion 노드 미사용")

    if 'working assumption' in question_lower or 'wa' in question_lower:
        if 'workingassumption' in cypher_lower:
            score += 20
        else:
            issues.append("WorkingAssumption 노드 미사용")

    # 3. RETURN 절 적절성
    if cypher and 'return' in cypher_lower:
        if 'content' in cypher_lower or 'resolutionid' in cypher_lower:
            score += 20
        else:
            issues.append("RETURN에 핵심 필드 누락")

    # 최대 100점으로 정규화
    score = min(score, 100)

    return {
        "score": score,
        "issues": issues,
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
    }


def evaluate_answer_completeness(question: str, response: str, result_count: int) -> dict:
    """답변 완전성 평가"""
    score = 0
    issues = []

    if not response:
        return {"score": 0, "issues": ["응답 없음"], "grade": "F"}

    # 1. 결과 개수 언급
    if str(result_count) in response or f"{result_count}개" in response or f"{result_count}건" in response:
        score += 20
    else:
        issues.append("결과 개수 미언급")

    # 2. 구체적인 예시 포함
    resolution_ids = extract_full_resolution_ids(response)
    if resolution_ids:
        score += 30
        if len(resolution_ids) >= 3:
            score += 10  # 충분한 예시
    else:
        issues.append("구체적 resolutionId 미포함")

    # 3. 응답 길이 적절성 (너무 짧거나 길지 않음)
    response_len = len(response)
    if 100 <= response_len <= 500:
        score += 20
    elif 50 <= response_len < 100 or 500 < response_len <= 800:
        score += 10
    else:
        issues.append("응답 길이 부적절")

    # 4. 질문 키워드 재등장 (관련성)
    question_words = set(re.findall(r'\b[가-힣a-zA-Z]{2,}\b', question.lower()))
    response_words = set(re.findall(r'\b[가-힣a-zA-Z]{2,}\b', response.lower()))
    overlap = question_words & response_words
    if len(overlap) >= 2:
        score += 20
    elif len(overlap) >= 1:
        score += 10
    else:
        issues.append("질문-응답 키워드 연관성 낮음")

    return {
        "score": min(score, 100),
        "issues": issues,
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
    }


def detect_hallucination(driver, response: str) -> dict:
    """환각(hallucination) 탐지"""
    issues = []

    # 1. 응답에서 언급된 resolutionId 추출
    resolution_ids = extract_full_resolution_ids(response)

    if not resolution_ids:
        return {
            "hallucination_detected": False,
            "verified_ratio": None,
            "issues": ["resolutionId 언급 없어 검증 불가"]
        }

    # 2. 실제 DB 존재 여부 확인
    verification = verify_resolution_ids(driver, resolution_ids)

    verified_ratio = verification["verified"] / verification["total"] if verification["total"] > 0 else 0

    hallucination_detected = verified_ratio < 0.8  # 80% 미만이면 환각 의심

    if verification["missing"]:
        issues.append(f"DB에 없는 ID: {verification['missing'][:3]}")  # 최대 3개만 표시

    return {
        "hallucination_detected": hallucination_detected,
        "verified_ratio": round(verified_ratio * 100, 1),
        "total_ids": verification["total"],
        "verified_ids": verification["verified"],
        "missing_ids": verification["missing"],
        "issues": issues
    }


def main():
    print("=" * 70)
    print("Phase-3 CQ Validation: 응답 품질 평가")
    print("=" * 70)

    # Load results
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pass_cases = [r for r in data['results'] if r['status'] == 'PASS']
    print(f"\n총 PASS 케이스: {len(pass_cases)}개\n")

    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    evaluations = []

    for i, case in enumerate(pass_cases):
        print(f"[{i+1}/{len(pass_cases)}] {case['test_case_id']} 평가 중...")

        # 1. Query Relevance
        query_eval = evaluate_query_relevance(case['question'], case.get('cypher', ''))

        # 2. Answer Completeness
        answer_eval = evaluate_answer_completeness(
            case['question'],
            case.get('response', ''),
            case.get('result_count', 0)
        )

        # 3. Hallucination Detection
        halluc_eval = detect_hallucination(driver, case.get('response', ''))

        # 종합 점수 계산
        composite_score = (
            query_eval['score'] * 0.3 +
            answer_eval['score'] * 0.3 +
            (halluc_eval['verified_ratio'] if halluc_eval['verified_ratio'] is not None else 50) * 0.4
        )

        evaluation = {
            "test_case_id": case['test_case_id'],
            "cq_type": case['cq_type'],
            "question": case['question'],
            "query_relevance": query_eval,
            "answer_completeness": answer_eval,
            "hallucination_check": halluc_eval,
            "composite_score": round(composite_score, 1),
            "reliability_grade": "HIGH" if composite_score >= 70 else "MEDIUM" if composite_score >= 50 else "LOW"
        }

        evaluations.append(evaluation)

    driver.close()

    # 통계 계산
    high_reliability = len([e for e in evaluations if e['reliability_grade'] == 'HIGH'])
    medium_reliability = len([e for e in evaluations if e['reliability_grade'] == 'MEDIUM'])
    low_reliability = len([e for e in evaluations if e['reliability_grade'] == 'LOW'])

    avg_score = sum(e['composite_score'] for e in evaluations) / len(evaluations)

    # 환각 탐지 통계
    halluc_cases = [e for e in evaluations if e['hallucination_check'].get('hallucination_detected', False)]

    # 결과 저장
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_evaluated": len(evaluations),
        "summary": {
            "average_composite_score": round(avg_score, 1),
            "reliability_distribution": {
                "HIGH": high_reliability,
                "MEDIUM": medium_reliability,
                "LOW": low_reliability
            },
            "hallucination_suspected": len(halluc_cases),
            "high_reliability_rate": round(100 * high_reliability / len(evaluations), 1)
        },
        "evaluations": evaluations
    }

    output_file = OUTPUT_DIR / "cq_quality_evaluation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n" + "=" * 70)
    print("품질 평가 결과 요약")
    print("=" * 70)
    print(f"  총 평가 케이스: {len(evaluations)}개")
    print(f"  평균 종합 점수: {round(avg_score, 1)}점")
    print(f"\n  신뢰도 분포:")
    print(f"    HIGH (≥70):   {high_reliability}개 ({round(100*high_reliability/len(evaluations), 1)}%)")
    print(f"    MEDIUM (50-69): {medium_reliability}개 ({round(100*medium_reliability/len(evaluations), 1)}%)")
    print(f"    LOW (<50):    {low_reliability}개 ({round(100*low_reliability/len(evaluations), 1)}%)")
    print(f"\n  환각 의심 케이스: {len(halluc_cases)}개")
    print(f"\n  결과 저장: {output_file}")

    # LOW reliability cases 출력
    if low_reliability > 0:
        print("\n" + "-" * 70)
        print("LOW 신뢰도 케이스:")
        for e in evaluations:
            if e['reliability_grade'] == 'LOW':
                print(f"  - {e['test_case_id']}: {e['question'][:40]}... (점수: {e['composite_score']})")


if __name__ == "__main__":
    main()
