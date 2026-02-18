import asyncio
from openai import OpenAI
from pydantic import BaseModel
from config import CONFIG
from core.logging.logger import LOG
from typing import List, Optional, TypeVar

T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    def __init__(self):
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not CONFIG.openai_api_key:
                LOG.error("OPENAI_API_KEY is not configured")
                raise ValueError("OPENAI_API_KEY is not configured")
            self._client = OpenAI(api_key=CONFIG.openai_api_key)
            LOG.debug("OpenAI client initialized")

        return self._client

    async def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            LOG.error("Cannot generate embedding for empty text")
            raise ValueError("Text cannot be empty")

        LOG.debug(f"Generating embedding for text ({len(text)} chars)")

        try:
            client = self._get_client()

            loop = asyncio.get_event_loop()

            def create_embedding():
                return client.embeddings.create(
                    input=text, model=CONFIG.openai_embedding_model
                )

            response = await loop.run_in_executor(None, create_embedding)

            embedding = response.data[0].embedding
            LOG.debug(f"Embedding generated ({len(embedding)} dimensions)")

            return embedding

        except Exception as e:
            LOG.error(f"Error generating embedding: {e}", exc_info=True)
            raise


openai_client = OpenAIClient()
