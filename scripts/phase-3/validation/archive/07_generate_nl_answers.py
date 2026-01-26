#!/usr/bin/env python3
"""
Generate Natural Language Answers for CQ Test Cases.

Uses OpenRouter API (Gemini) to generate human-readable answers
from query results.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import httpx

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
PARSED_DIR = BASE_DIR / "ontology" / "output" / "parsed_reports" / "v2"
CQ_RESULTS = BASE_DIR / "logs" / "phase-3" / "cq_validation_results_100.json"
OUTPUT_DIR = BASE_DIR / "logs" / "phase-3"

# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(prompt: str) -> str:
    """Call OpenRouter API to generate answer."""
    if not OPENROUTER_API_KEY:
        return "[LLM API key not configured]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.3
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Error: {str(e)}]"


def generate_answer_prompt(question: str, result: dict) -> str:
    """Generate prompt for LLM to create natural language answer."""
    sample_data = json.dumps(result.get("sample", []), ensure_ascii=False, indent=2)
    count = result.get("result_count", 0)

    return f"""다음 질문에 대한 쿼리 결과를 바탕으로 자연어 답변을 생성해주세요.

질문: {question}

쿼리 결과:
- 총 {count}개의 결과가 있습니다.
- 샘플 데이터:
{sample_data}

요구사항:
1. 한국어로 답변
2. 2-4문장으로 간결하게
3. 구체적인 숫자와 예시 포함
4. 전문적이고 객관적인 톤

답변:"""


def main():
    print("=" * 70)
    print("GENERATING NATURAL LANGUAGE ANSWERS")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")

    # Check API key
    if not OPENROUTER_API_KEY:
        print("\n❌ OPENROUTER_API_KEY not set. Using template answers.")

    # Load validation results
    print("\n[1/3] Loading validation results...")
    with open(CQ_RESULTS) as f:
        data = json.load(f)
    results = data["results"]
    print(f"  Loaded {len(results)} test cases")

    # Generate answers for ALL 100 test cases
    print("\n[2/3] Generating natural language answers...")
    nl_results = []
    total = len(results)

    for i, r in enumerate(results):
        print(f"  Processing {i+1}/{total}: {r['test_case_id']}...", end=" ")

        if OPENROUTER_API_KEY and r["status"] in ["PASS", "WARN"]:
            prompt = generate_answer_prompt(r["question"], r)
            answer = call_llm(prompt)
        else:
            # Generate template answer without LLM
            answer = generate_template_answer(r)

        nl_results.append({
            "test_case_id": r["test_case_id"],
            "cq_type": r["cq_type"],
            "question": r["question"],
            "status": r["status"],
            "result_count": r["result_count"],
            "sample": r.get("sample", [])[:3],
            "natural_language_answer": answer
        })
        print("✓")

    # Save results
    print("\n[3/3] Saving results...")
    output_file = OUTPUT_DIR / "cq_nl_answers_100.json"
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_cases": len(nl_results),
        "results": nl_results
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: {output_file}")

    # Print samples
    print("\n" + "=" * 70)
    print("SAMPLE Q&A PAIRS")
    print("=" * 70)

    for r in nl_results[:5]:
        print(f"\n[{r['test_case_id']}] {r['cq_type']}")
        print(f"Q: {r['question']}")
        print(f"A: {r['natural_language_answer']}")

    return nl_results


def generate_template_answer(r: dict) -> str:
    """Generate template-based answer without LLM."""
    cq_type = r["cq_type"]
    count = r["result_count"]
    sample = r.get("sample", [])
    question = r["question"]

    if r["status"] == "FAIL":
        return f"해당 조건에 맞는 데이터가 없습니다."

    if "CQ1-1" in cq_type:
        meeting = question.split("회의")[0].split()[-1] if "회의" in question else ""
        if sample:
            first = sample[0]
            return f"{meeting} 회의에서 총 {count}개의 Agreement가 합의되었습니다. 예를 들어, '{first.get('id', '')}'는 \"{first.get('content', '')[:80]}...\"입니다."
        return f"{meeting} 회의에서 총 {count}개의 Agreement가 합의되었습니다."

    elif "CQ1-2" in cq_type:
        meeting = question.split("회의")[0].split()[-1] if "회의" in question else ""
        return f"{meeting} 회의에서 총 {count}개의 Conclusion이 도출되었습니다."

    elif "CQ1-3" in cq_type:
        meeting = question.split("회의")[0].split()[-1] if "회의" in question else ""
        return f"{meeting} 회의에서 총 {count}개의 Working Assumption이 설정되었습니다."

    elif "CQ1-4" in cq_type:
        return f"해당 Agenda Item에서 총 {count}개의 Resolution이 있습니다. Agreement, Conclusion, Working Assumption 유형이 포함됩니다."

    elif "CQ1-5" in cq_type:
        keyword = question.split("'")[1] if "'" in question else "해당 키워드"
        return f"'{keyword}' 관련 Resolution이 총 {count}개 발견되었습니다."

    elif "CQ2-1" in cq_type:
        if sample:
            return f"해당 Resolution이 참조한 Tdoc은 총 {count}개입니다."
        return f"Resolution의 Tdoc 참조 정보가 {count}건 있습니다."

    elif "CQ2-2" in cq_type:
        if sample:
            top = sample[0]
            return f"Tdoc 참조가 가장 많은 Resolution Top {count}입니다. 1위는 {top.get('id', '')}로 {top.get('tdoc_count', 0)}개의 Tdoc을 참조합니다."
        return f"총 {count}개의 Resolution이 Tdoc을 참조하고 있습니다."

    elif "CQ3-1" in cq_type:
        company = question.split("가 ")[0].split()[-1] if "가 " in question else "해당 회사"
        return f"{company}가 작성한 FL Summary는 총 {count}개입니다."

    elif "CQ3-2" in cq_type:
        if sample:
            top = sample[0]
            return f"회사별 Moderator 담당 횟수 Top {min(count, 10)}입니다. 1위는 {top.get('company', '')}로 {top.get('count', 0)}회입니다."
        return f"총 {count}개 회사의 Moderator 담당 현황이 있습니다."

    elif "CQ3-3" in cq_type:
        if len(sample) >= 2:
            c1, c2 = sample[0], sample[1]
            return f"비교 결과: {c1.get('company', '')}는 {c1.get('count', 0)}회, {c2.get('company', '')}는 {c2.get('count', 0)}회입니다."
        return f"두 회사 간 비교 결과가 {count}건 있습니다."

    elif "CQ4-1" in cq_type:
        meeting = question.split("회의")[0].split()[-1] if "회의" in question else ""
        return f"{meeting} 회의의 Session Notes는 총 {count}개입니다."

    elif "CQ4-2" in cq_type:
        meeting = question.split("회의")[0].split()[-1] if "회의" in question else ""
        return f"{meeting} 회의의 FL Summary는 총 {count}개입니다."

    elif "CQ4-3" in cq_type:
        meeting = question.split("회의")[0].split()[-1] if "회의" in question else ""
        return f"{meeting} 회의의 Moderator Summary는 총 {count}개입니다."

    elif "CQ4-4" in cq_type:
        if count == 0:
            return "해당 회의에서 Ad-hoc Chair 정보가 기록되지 않았습니다."
        return f"해당 회의의 Ad-hoc Session Chair 정보가 {count}건 있습니다."

    elif "CQ6-1" in cq_type:
        if sample:
            return f"회의별 Resolution 수 추이입니다. 총 {count}개 회의 데이터가 있으며, 예: {sample[0].get('meeting', '')}회의 {sample[0].get('resolutions', 0)}개."
        return f"총 {count}개 회의의 Resolution 추이 데이터가 있습니다."

    elif "CQ6-2" in cq_type:
        if sample:
            return f"Resolution 유형별 분포: Agreement {sample[0].get('count', 0)}개 ({sample[0].get('percentage', 0)}%), Conclusion, Working Assumption 순입니다."
        return f"Resolution 유형별 분포 데이터입니다."

    elif "CQ6-3" in cq_type:
        if sample:
            s = sample[0]
            return f"회의당 평균 Resolution 수는 {s.get('avg', 0)}개입니다. 최소 {s.get('min', 0)}개, 최대 {s.get('max', 0)}개입니다."
        return f"회의당 Resolution 통계입니다."

    return f"총 {count}개의 결과가 있습니다."


if __name__ == "__main__":
    main()
