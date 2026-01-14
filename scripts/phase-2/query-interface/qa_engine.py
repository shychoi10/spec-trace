"""
CQ 25개 자연어 QA 엔진
질문 → Cypher 생성 → 실행 → 자연어 답변 생성
"""

import json
from datetime import datetime
import config
from text_to_cypher import generate_cypher, execute_cypher
from graph_store import get_llm

# 답변 생성 프롬프트
ANSWER_PROMPT = """Based on the query results below, provide a natural language answer in Korean.

Question: {question}
Query Results: {results}

Instructions:
1. Answer in Korean naturally
2. If results are empty, say "해당하는 결과가 없습니다" and suggest why
3. Summarize key findings concisely
4. Include specific numbers and examples from the data
5. Keep the answer under 200 words

Answer:"""


def serialize_neo4j_result(obj):
    """Neo4j 결과 객체를 JSON 직렬화 가능한 형태로 변환"""
    if hasattr(obj, '__iter__') and not isinstance(obj, (str, dict)):
        return [serialize_neo4j_result(item) for item in obj]
    elif hasattr(obj, 'items'):  # dict-like
        return {k: serialize_neo4j_result(v) for k, v in obj.items()}
    elif hasattr(obj, '_properties'):  # Neo4j Node
        return dict(obj._properties)
    elif hasattr(obj, 'nodes') and hasattr(obj, 'relationships'):  # Neo4j Path
        return str(obj)
    else:
        return obj


def generate_answer(question: str, results: list) -> str:
    """쿼리 결과를 자연어 답변으로 변환"""
    llm = get_llm()

    # Neo4j 결과를 직렬화 가능한 형태로 변환
    serialized_results = [serialize_neo4j_result(r) for r in results[:10]]

    # 결과를 문자열로 변환 (최대 10개)
    try:
        results_str = json.dumps(serialized_results, ensure_ascii=False, indent=2)
    except TypeError as e:
        results_str = str(serialized_results)

    prompt = ANSWER_PROMPT.format(question=question, results=results_str)
    response = llm.complete(prompt)
    return response.text.strip()


def ask(question: str, verbose: bool = True) -> dict:
    """전체 QA 파이프라인: 질문 → Cypher → 실행 → 답변"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"📝 질문: {question}")
        print(f"{'='*60}")

    # 1. Cypher 생성
    cypher = generate_cypher(question)
    if verbose:
        print(f"\n🔧 생성된 Cypher:\n{cypher}")

    # 2. 쿼리 실행
    try:
        results = execute_cypher(cypher)
        success = True
        error = None
        if verbose:
            print(f"\n📊 결과: {len(results)}건")
    except Exception as e:
        results = []
        success = False
        error = str(e)
        if verbose:
            print(f"\n❌ 쿼리 오류: {e}")

    # 3. 자연어 답변 생성
    if verbose:
        print(f"\n💬 답변 생성 중...")

    answer = generate_answer(question, results)

    if verbose:
        print(f"\n{'='*60}")
        print(f"🗣️ 답변:\n{answer}")
        print(f"{'='*60}")

    return {
        "question": question,
        "cypher": cypher,
        "results": results,
        "result_count": len(results),
        "answer": answer,
        "success": success,
        "error": error
    }


# 확장된 CQ 목록 (카테고리별 10개 이상, 총 50+ 질문)
CQ_LIST = [
    # ============================================================
    # 카테고리 1: Tdoc 기본 검색 (12개)
    # ============================================================
    {"id": "CQ-01", "cat": "Tdoc 기본 검색", "q": "RAN1#120 회의에 제출된 Tdoc 총 개수는?"},
    {"id": "CQ-02", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 Agenda Item 8.1 관련 Tdoc 5개 보여줘"},
    {"id": "CQ-03", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 Huawei가 제출한 Tdoc 5개"},
    {"id": "CQ-04", "cat": "Tdoc 기본 검색", "q": "Rel-18 타겟 Tdoc 5개"},
    {"id": "CQ-05", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 approved 상태인 Tdoc 5개"},
    {"id": "CQ-06", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 noted 상태인 Tdoc 5개"},
    {"id": "CQ-07", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 withdrawn 상태인 Tdoc 3개"},
    {"id": "CQ-08", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 type이 'discussion'인 Tdoc 5개"},
    {"id": "CQ-09", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 type이 'CR'인 Tdoc 5개"},
    {"id": "CQ-10", "cat": "Tdoc 기본 검색", "q": "RAN1#120의 Agenda Item 목록 10개"},
    {"id": "CQ-11", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 for 필드가 'Approval'인 Tdoc 3개"},
    {"id": "CQ-12", "cat": "Tdoc 기본 검색", "q": "RAN1#120에서 for 필드가 'Decision'인 Tdoc 3개"},

    # ============================================================
    # 카테고리 2: Tdoc 속성 조회 (10개)
    # ============================================================
    {"id": "CQ-13", "cat": "Tdoc 속성 조회", "q": "R1-2400001의 title은?"},
    {"id": "CQ-14", "cat": "Tdoc 속성 조회", "q": "R1-2400001의 status는?"},
    {"id": "CQ-15", "cat": "Tdoc 속성 조회", "q": "R1-2400001의 type은?"},
    {"id": "CQ-16", "cat": "Tdoc 속성 조회", "q": "R1-2400001의 for 필드는?"},
    {"id": "CQ-17", "cat": "Tdoc 속성 조회", "q": "R1-2400001의 contact 정보는?"},
    {"id": "CQ-18", "cat": "Tdoc 속성 조회", "q": "R1-2400001이 제출된 회의는?"},
    {"id": "CQ-19", "cat": "Tdoc 속성 조회", "q": "R1-2400001을 제출한 회사는?"},
    {"id": "CQ-20", "cat": "Tdoc 속성 조회", "q": "R1-2400001이 속한 Agenda Item은?"},
    {"id": "CQ-21", "cat": "Tdoc 속성 조회", "q": "R1-2400001의 Target Release는?"},
    {"id": "CQ-22", "cat": "Tdoc 속성 조회", "q": "R1-2400001이 관련된 Work Item은?"},

    # ============================================================
    # 카테고리 3: Tdoc 관계 추적 (12개)
    # ============================================================
    {"id": "CQ-23", "cat": "Tdoc 관계 추적", "q": "R1-2400100의 revision 이전 문서는?"},
    {"id": "CQ-24", "cat": "Tdoc 관계 추적", "q": "R1-2400100의 revision 이후 문서는?"},
    {"id": "CQ-25", "cat": "Tdoc 관계 추적", "q": "type이 'LS in'인 Tdoc 5개"},
    {"id": "CQ-26", "cat": "Tdoc 관계 추적", "q": "type이 'LS out'인 Tdoc 5개"},
    {"id": "CQ-27", "cat": "Tdoc 관계 추적", "q": "LS 타입 Tdoc과 그 LS가 originated_from 관계로 연결된 WorkingGroup"},
    {"id": "CQ-28", "cat": "Tdoc 관계 추적", "q": "LS 타입 Tdoc과 그 LS가 sent_to 관계로 연결된 WorkingGroup 5개"},
    {"id": "CQ-29", "cat": "Tdoc 관계 추적", "q": "38.211 Spec을 수정하는 CR 5개"},
    {"id": "CQ-30", "cat": "Tdoc 관계 추적", "q": "38.213 Spec을 수정하는 CR 5개"},
    {"id": "CQ-31", "cat": "Tdoc 관계 추적", "q": "CR 타입 Tdoc과 그 CR이 수정하는 Spec 정보 5개"},
    {"id": "CQ-32", "cat": "Tdoc 관계 추적", "q": "RAN1#120에서 postponed 상태인 Tdoc 5개"},
    {"id": "CQ-33", "cat": "Tdoc 관계 추적", "q": "RAN1#120에서 revised 상태인 Tdoc 5개"},
    {"id": "CQ-34", "cat": "Tdoc 관계 추적", "q": "reply_to 관계가 있는 LS Tdoc 3개"},

    # ============================================================
    # 카테고리 4: 회사/기관 분석 (12개)
    # ============================================================
    {"id": "CQ-35", "cat": "회사 분석", "q": "RAN1#120에서 가장 많이 Tdoc을 제출한 회사 top 5"},
    {"id": "CQ-36", "cat": "회사 분석", "q": "Samsung이 RAN1#120에서 제출한 Tdoc 5개"},
    {"id": "CQ-37", "cat": "회사 분석", "q": "Huawei가 RAN1#120에서 제출한 Tdoc 5개"},
    {"id": "CQ-38", "cat": "회사 분석", "q": "Qualcomm이 RAN1#120에서 제출한 Tdoc 5개"},
    {"id": "CQ-39", "cat": "회사 분석", "q": "Ericsson이 RAN1#120에서 제출한 Tdoc 5개"},
    {"id": "CQ-40", "cat": "회사 분석", "q": "Nokia가 RAN1#120에서 제출한 Tdoc 5개"},
    {"id": "CQ-41", "cat": "회사 분석", "q": "Samsung Tdoc 중 approved 상태인 것 5개"},
    {"id": "CQ-42", "cat": "회사 분석", "q": "Samsung Tdoc 중 noted 상태인 것 5개"},
    {"id": "CQ-43", "cat": "회사 분석", "q": "Agenda 8.1에서 Samsung 외 다른 회사가 제출한 Tdoc 5개"},
    {"id": "CQ-44", "cat": "회사 분석", "q": "Samsung의 RAN1#120 Tdoc status별 개수"},
    {"id": "CQ-45", "cat": "회사 분석", "q": "Huawei의 RAN1#120 Tdoc status별 개수"},
    {"id": "CQ-46", "cat": "회사 분석", "q": "RAN1#120에서 CR 타입을 가장 많이 제출한 회사 top 5"},

    # ============================================================
    # 카테고리 5: 통계/집계 쿼리 (10개)
    # ============================================================
    {"id": "CQ-47", "cat": "통계 집계", "q": "RAN1#120의 Tdoc status별 개수"},
    {"id": "CQ-48", "cat": "통계 집계", "q": "RAN1#120의 Tdoc type별 개수"},
    {"id": "CQ-49", "cat": "통계 집계", "q": "RAN1#120의 Agenda Item별 Tdoc 개수 top 10"},
    {"id": "CQ-50", "cat": "통계 집계", "q": "RAN1#120의 Work Item별 Tdoc 개수 top 10"},
    {"id": "CQ-51", "cat": "통계 집계", "q": "RAN1#120의 Target Release별 Tdoc 개수"},
    {"id": "CQ-52", "cat": "통계 집계", "q": "전체 Meeting 목록과 각 Meeting별 Tdoc 개수"},
    {"id": "CQ-53", "cat": "통계 집계", "q": "전체 Company 목록과 각 Company별 Tdoc 개수 top 10"},
    {"id": "CQ-54", "cat": "통계 집계", "q": "전체 Spec 목록과 각 Spec을 수정하는 CR 개수"},
    {"id": "CQ-55", "cat": "통계 집계", "q": "전체 WorkingGroup 목록"},
    {"id": "CQ-56", "cat": "통계 집계", "q": "전체 Release 목록과 각 Release별 Tdoc 개수"},
]


def run_all_cq(output_path: str = None):
    """모든 CQ 실행 및 리포트 생성"""
    results = []

    for cq in CQ_LIST:
        print(f"\n{'#'*60}")
        print(f"# [{cq['id']}] {cq['cat']}")
        print(f"{'#'*60}")

        result = ask(cq['q'], verbose=True)
        result['id'] = cq['id']
        result['category'] = cq['cat']
        results.append(result)

    # 리포트 생성
    success_count = sum(1 for r in results if r['success'] and r['result_count'] > 0)

    md = f"""# CQ 25개 자연어 QA 검증 리포트

**생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**LLM**: google/gemini-2.5-flash (OpenRouter)

## 요약

| 항목 | 값 |
|------|-----|
| 총 CQ | {len(results)} |
| 성공 (결과 있음) | {success_count} |
| 성공률 | {100*success_count/len(results):.1f}% |

---

"""

    current_cat = None
    for r in results:
        if r['category'] != current_cat:
            current_cat = r['category']
            md += f"\n## {current_cat}\n\n"

        status = "✅" if r['success'] and r['result_count'] > 0 else "⚠️"

        md += f"""### {r['id']} {status}

**질문**: {r['question']}

**생성된 Cypher**:
```cypher
{r['cypher']}
```

**결과 수**: {r['result_count']}건

**🗣️ 답변**:
> {r['answer']}

---

"""

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"\n\n리포트 저장: {output_path}")

    return results


if __name__ == "__main__":
    # 전체 CQ 실행
    output_path = "/home/sihyeon/workspace/spec-trace/docs/phase-2/cq_qa_report.md"
    run_all_cq(output_path)
