"""
Step-3 Sub-step 3-2: Neo4j + LlamaIndex 연동
Neo4j PropertyGraphStore 래퍼 및 연결 테스트
"""

# config를 먼저 import하여 SSL 패치 적용
import config

from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.openrouter import OpenRouter
from neo4j import GraphDatabase


def get_graph_store() -> Neo4jPropertyGraphStore:
    """Neo4j PropertyGraphStore 인스턴스 반환"""
    return Neo4jPropertyGraphStore(
        username=config.NEO4J_CONFIG["username"],
        password=config.NEO4J_CONFIG["password"],
        url=config.NEO4J_CONFIG["uri"],
    )


def get_llm() -> OpenRouter:
    """OpenRouter LLM 인스턴스 반환"""
    return OpenRouter(
        model=config.OPENROUTER_CONFIG["model"],
        api_key=config.OPENROUTER_CONFIG["api_key"],
    )


def get_neo4j_driver():
    """Neo4j 드라이버 직접 접근"""
    return GraphDatabase.driver(
        config.NEO4J_CONFIG["uri"],
        auth=(config.NEO4J_CONFIG["username"], config.NEO4J_CONFIG["password"])
    )


def test_connection():
    """Neo4j 연결 및 기본 통계 테스트"""
    print("=" * 60)
    print("Neo4j + LlamaIndex 연결 테스트")
    print("=" * 60)

    # 1. Neo4j 직접 연결 테스트
    print("\n[1] Neo4j 연결 테스트...")
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # 노드 수
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            print(f"   - 총 노드: {node_count:,}개")

            # 관계 수
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()["count"]
            print(f"   - 총 관계: {rel_count:,}개")

            # 라벨별 노드 수
            result = session.run("""
                MATCH (n)
                WITH labels(n) as labels, count(*) as count
                UNWIND labels as label
                RETURN label, sum(count) as count
                ORDER BY count DESC
                LIMIT 5
            """)
            print("   - 주요 라벨:")
            for record in result:
                print(f"     · {record['label']}: {record['count']:,}개")

        driver.close()
        print("✅ Neo4j 연결 성공")
    except Exception as e:
        print(f"❌ Neo4j 연결 실패: {e}")
        return False

    # 2. LlamaIndex GraphStore 테스트
    print("\n[2] LlamaIndex Neo4jPropertyGraphStore 테스트...")
    try:
        graph_store = get_graph_store()
        print("✅ LlamaIndex GraphStore 생성 성공")
    except Exception as e:
        print(f"❌ LlamaIndex GraphStore 실패: {e}")
        return False

    # 3. OpenRouter LLM 테스트
    print("\n[3] OpenRouter LLM 테스트...")
    print(f"   - 모델: {config.OPENROUTER_CONFIG['model']}")
    try:
        llm = get_llm()
        response = llm.complete("Say 'Hello, 3GPP!' only.")
        print(f"   - 응답: {response.text.strip()}")
        print("✅ OpenRouter 연결 성공")
    except Exception as e:
        print(f"❌ OpenRouter 연결 실패: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 모든 연결 테스트 통과!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    test_connection()
