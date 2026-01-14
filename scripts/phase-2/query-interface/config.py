"""
Step-3 Query Interface Configuration
Neo4j + LlamaIndex + OpenRouter 설정
"""

import os
import urllib3
import httpx
from dotenv import load_dotenv

load_dotenv()

# SSL 경고 비활성화 및 SSL 검증 우회 (WSL 환경 대응)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# httpx SSL 검증 비활성화 패치 (LlamaIndex가 httpx 사용)
_original_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

_original_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init

# Neo4j 설정 (Step-2에서 구축한 DB)
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7688",
    "username": "neo4j",
    "password": "password123",
}

# OpenRouter 설정
OPENROUTER_CONFIG = {
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model": "google/gemini-2.5-flash",
    "api_base": "https://openrouter.ai/api/v1",
}

# Neo4j 스키마 정보 (TextToCypherRetriever 정확도 향상용)
SCHEMA_INFO = """
Node Labels: Tdoc, CR, LS, Meeting, Company, Contact, WorkItem, AgendaItem, Release, Spec, WorkingGroup

Relationships:
- (Tdoc)-[:PRESENTED_AT]->(Meeting)
- (Tdoc)-[:SUBMITTED_BY]->(Company)
- (Tdoc)-[:HAS_CONTACT]->(Contact)
- (Tdoc)-[:BELONGS_TO]->(AgendaItem)
- (Tdoc)-[:RELATED_TO]->(WorkItem)
- (Tdoc)-[:TARGET_RELEASE]->(Release)
- (Tdoc)-[:IS_REVISION_OF]->(Tdoc)
- (Tdoc)-[:REVISED_TO]->(Tdoc)
- (CR)-[:MODIFIES]->(Spec)
- (LS)-[:SENT_TO]->(WorkingGroup)
- (LS)-[:CC_TO]->(WorkingGroup)
- (LS)-[:ORIGINATED_FROM]->(WorkingGroup)
- (LS)-[:REPLY_TO]->(Tdoc)

Key Properties:
- Tdoc: tdocNumber, title, type, status, for
- Company: companyName, aliases
- Meeting: meetingNumber
- WorkItem: workItemCode
- AgendaItem: agendaNumber, description
"""
