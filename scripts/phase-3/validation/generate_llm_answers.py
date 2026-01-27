#!/usr/bin/env python3
"""
CQ 답변 리포트 생성기 - Google Gemini API 기반 자연어 요약 + 출처 명시
100개 CQ에 대해 Neo4j 쿼리 결과를 LLM으로 자연어 한국어 답변으로 변환
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase
import google.generativeai as genai
import time

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# 설정
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CQ_FILE = PROJECT_ROOT / "logs/phase-3/cq_test_dataset.json"
OUTPUT_FILE = PROJECT_ROOT / "logs/phase-3/cq_answers_report_llm.md"

# Google Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


def extract_resolution_ids(cypher_result: list) -> list:
    """쿼리 결과에서 resolution ID들을 추출"""
    resolution_ids = set()

    for record in cypher_result:
        for key, value in record.items():
            if isinstance(value, str):
                # resolutionId 패턴 매칭 (AGR-xxx, CON-xxx, WA-xxx)
                # (?:...) = non-capturing group으로 전체 ID 반환
                matches = re.findall(r'(?:AGR|CON|WA)-\d+-[\d\.]+-\d+', value)
                resolution_ids.update(matches)

                # URI에서 추출
                if 'resolution/' in value:
                    match = re.search(r'resolution/((?:AGR|CON|WA)-[\d\-\.]+)', value)
                    if match:
                        resolution_ids.add(match.group(1))

    return list(resolution_ids)


def get_source_info(driver, resolution_ids: list) -> dict:
    """resolution ID들의 출처 정보(회의번호, TDoc) 조회"""
    if not resolution_ids:
        return {}

    source_info = {}

    # Resolution별 출처 조회
    query = """
    MATCH (r)-[:MADE_AT]->(m)
    WHERE r.resolutionId IN $ids
    OPTIONAL MATCH (r)-[:REFERENCES]->(t:Tdoc)
    RETURN r.resolutionId AS id, m.canonicalMeetingNumber AS meetingNum, collect(DISTINCT t.tdocNumber) AS tdocNums
    """

    try:
        with driver.session() as session:
            result = session.run(query, ids=resolution_ids)
            for record in result:
                rid = record['id']

                # 회의번호 직접 사용 (canonicalMeetingNumber: RAN1#103)
                meeting = record['meetingNum'] or ""

                # TDoc 번호 직접 사용 (tdocNumber 배열의 첫 번째 요소)
                tdocs = []
                for tdoc_nums in record['tdocNums']:
                    if tdoc_nums:
                        # tdocNumber는 배열일 수 있음 ['R1-2009571']
                        if isinstance(tdoc_nums, list):
                            tdocs.extend(tdoc_nums[:3])
                        else:
                            tdocs.append(tdoc_nums)

                source_info[rid] = {
                    'meeting': meeting,
                    'tdocs': tdocs[:3]  # 최대 3개
                }
    except Exception as e:
        print(f"출처 조회 오류: {e}")

    return source_info


def format_sources(source_info: dict) -> str:
    """출처 정보를 마크다운 테이블로 포맷 (회의 번호 DESC 정렬)"""
    if not source_info:
        return ""

    lines = ["\n\n**출처:**", "| ID | 회의 | 관련 TDoc |", "|:---|:-----|:----------|"]

    # 회의 번호 기준 내림차순 정렬 (최신 회의 먼저)
    def get_meeting_sort_key(item):
        rid, info = item
        meeting = info.get('meeting', '')
        # RAN1#99, RAN1#98b 등에서 숫자 추출
        match = re.search(r'#(\d+)', meeting)
        if match:
            return -int(match.group(1))  # 내림차순을 위해 음수
        return 0

    for rid, info in sorted(source_info.items(), key=get_meeting_sort_key):
        meeting = info.get('meeting', '-')
        tdocs = ', '.join(info.get('tdocs', [])) or '-'
        lines.append(f"| {rid} | {meeting} | {tdocs} |")

    return '\n'.join(lines)


def call_llm(question: str, cypher_result: list, source_info: dict, max_tokens: int = 1200) -> str:
    """Google Gemini API를 통해 LLM 호출 (출처 정보 포함)"""
    if not GOOGLE_API_KEY:
        return "[오류: GOOGLE_API_KEY가 설정되지 않음]"

    # 결과를 문자열로 변환 (최대 4500자)
    result_str = json.dumps(cypher_result, ensure_ascii=False, indent=2)
    if len(result_str) > 4500:
        result_str = result_str[:4500] + "\n... (truncated)"

    # 출처 정보 문자열
    source_str = json.dumps(source_info, ensure_ascii=False, indent=2) if source_info else "{}"

    prompt = f"""당신은 3GPP RAN1 표준화 전문가입니다. 아래 질문에 대한 Neo4j 데이터베이스 쿼리 결과를 바탕으로 자연스러운 한국어로 상세하게 답변해주세요.

## 질문
{question}

## 데이터베이스 쿼리 결과
```json
{result_str}
```

## 출처 정보 (회의번호, 관련 TDoc)
```json
{source_str}
```

## 답변 작성 지침
1. 데이터를 분석하여 핵심 인사이트를 도출하세요
2. 구체적인 수치, 회사명, 기술명을 포함하세요
3. 자연스러운 한국어 문장으로 작성하세요 (JSON이나 코드 형식 사용 금지)
4. 가능하면 결과의 의미나 시사점도 설명하세요
5. 답변은 3-10문장 정도로 충분히 상세하게 작성하세요
6. **중요**: 답변 본문에서 Agreement/Conclusion/Working Assumption ID를 언급할 때는 괄호 안에 회의번호를 함께 표기하세요
   - 예: "AGR-106-8.8.3-005 (RAN1#106)에 따르면..."

## 한국어 답변:"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"[LLM 오류: {str(e)[:150]}]"


def run_cypher(driver, cypher: str) -> list:
    """Neo4j Cypher 쿼리 실행"""
    try:
        with driver.session() as session:
            result = session.run(cypher)
            return [dict(record) for record in result]
    except Exception as e:
        return [{"error": str(e)}]


def main():
    print(f"=== CQ LLM 답변 리포트 생성 (출처 포함) ===")
    print(f"API Key 설정: {'✓' if GOOGLE_API_KEY else '✗'}")

    # CQ 데이터 로드
    with open(CQ_FILE, 'r', encoding='utf-8') as f:
        cq_data = json.load(f)

    questions = cq_data['questions']
    print(f"질문 수: {len(questions)}")

    # Neo4j 연결
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # 리포트 생성
    report_lines = [
        "# CQ 답변 리포트 (LLM 기반)",
        f"\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n총 질문 수: {len(questions)}개",
        "\n> 각 답변에는 출처 정보(Agreement/Conclusion ID, 회의번호, 관련 TDoc)가 포함되어 있습니다.",
        "\n---\n"
    ]

    # 카테고리별 그룹화
    categories = {}
    for q in questions:
        cat = q['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(q)

    success_count = 0
    error_count = 0

    for cat_name, cat_questions in categories.items():
        report_lines.append(f"\n## {cat_name}\n")

        for q in cat_questions:
            qid = q['id']
            question = q['question']
            cypher = q['cypher']

            print(f"처리 중: {qid} - {question[:40]}...", end=" ", flush=True)

            # Cypher 실행
            result = run_cypher(driver, cypher)

            if not result or (len(result) == 1 and 'error' in result[0]):
                answer = f"데이터 없음 또는 쿼리 오류: {result[0].get('error', 'No data')[:100] if result else 'Empty'}"
                error_count += 1
                print("❌")
                report_lines.append(f"### {qid}. {question}\n")
                report_lines.append(f"{answer}\n")
                report_lines.append("")
            else:
                # 출처 정보 조회
                resolution_ids = extract_resolution_ids(result)
                source_info = get_source_info(driver, resolution_ids)

                # LLM으로 답변 생성
                answer = call_llm(question, result, source_info)

                if answer.startswith("["):  # 오류 메시지
                    error_count += 1
                    print("⚠️")
                else:
                    success_count += 1
                    print("✓")

                # 답변 + 출처 테이블 추가
                report_lines.append(f"### {qid}. {question}\n")
                report_lines.append(f"{answer}")

                # 출처 테이블 추가
                if source_info:
                    report_lines.append(format_sources(source_info))

                report_lines.append("\n")

                # Rate limit 방지 (Gemini free tier)
                time.sleep(1)

    driver.close()

    # 요약 추가
    summary = f"""
---

## 요약

- 총 질문: {len(questions)}개
- 성공: {success_count}개 ({100*success_count/len(questions):.1f}%)
- 오류/데이터 없음: {error_count}개
- 출처 형식: Agreement/Conclusion ID + 회의번호 + 관련 TDoc
"""
    report_lines.append(summary)

    # 파일 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n=== 완료 ===")
    print(f"성공: {success_count}/{len(questions)}")
    print(f"저장: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
