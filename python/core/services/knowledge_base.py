from config import CONFIG
from typing import Any, Dict, List
from core.logging.logger import LOG
from core.clients import openai_client, backend_client


class KnowledgeBaseService:
    async def search(
        self, access_token: str, query: str, agent_id: int, limit: int = None
    ) -> List[Dict[str, Any]]:
        if limit is None:
            limit = CONFIG.knowledge_base_default_limit

        LOG.info(f"Knowledge base search: query='{query[:50]}...' agent_id={agent_id}")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if agent_id <= 0:
            raise ValueError("Invalid agent_id")

        try:
            query_embedding = await openai_client.generate_embedding(query)
            LOG.debug(f"Generated embedding ({len(query_embedding)} dimensions)")

            chunks = await backend_client.vector_search(
                access_token=access_token,
                query_embedding=query_embedding,
                agent_id=agent_id,
                limit=limit,
            )

            if not chunks:
                raise LookupError("No matching knowledge base entries")

            LOG.info(f"Search returned {len(chunks)} results")
            return chunks

        except (ValueError, LookupError):
            raise
        except Exception as e:
            LOG.error(f"Knowledge base search failed: {e}", exc_info=True)
            raise RuntimeError(f"OpenAI Embedding Service: {e}") from e


knowledge_base_service = KnowledgeBaseService()
