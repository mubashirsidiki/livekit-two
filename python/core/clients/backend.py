from pprint import pprint
import aiohttp
from config import CONFIG
from core.logging.logger import LOG
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from core.models.models import CallMetadata


class BackendClient:
    def __init__(self):
        self._base_url = CONFIG.backend_url
        self._api_prefix = CONFIG.backend_api_prefix

        self._ensure_configured()

    def _ensure_configured(self):
        if not self._base_url:
            LOG.error("BACKEND_URL is not configured")
            raise ValueError("BACKEND_URL is not configured")
        
    
    async def send_call_analytics(
        self, 
        access_token: str, 
        metadata: CallMetadata
    ) -> bool:
        import aiohttp

        url = f"{self._base_url}{self._api_prefix}/call-analytics/create"
        headers = {"x-token": access_token, "Content-Type": "application/json"}

        body = metadata.model_dump(mode='json', by_alias=True)
        pprint(body)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=body,
                ) as resp:
                    resp.raise_for_status()
                    LOG.info("Call metadata sent successfully")
                    return True
        except Exception as e:
            LOG.error(f"Failed to send call metadata: {e}")
            return False

    async def vector_search(
        self,
        access_token: str,
        query_embedding: list[float],
        agent_id: int,
        limit: int = 5,
    ) -> Dict[str, Any]:
        self._ensure_configured()

        url = f"{self._base_url}{self._api_prefix}/agents/documents/chunks/vector-search/by-token"
        headers = {"x-token": access_token}
        body = {
            "queryEmbedding": query_embedding,
            "limit": limit,
            "agentId": agent_id,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, json=body) as response:
                    response.raise_for_status()
                    data = await response.json()
                    LOG.info("Chunks fetched successfully")
                    return data
        except aiohttp.ClientError as e:
            LOG.error(f"Error fetching chunks: {e}")
            raise
        except Exception as e:
            LOG.error(f"Unexpected error vector search: {e}", exc_info=True)
            raise

    async def fetch_agent_config(self, access_token: str) -> Dict[str, Any]:
        url = f"{self._base_url}{self._api_prefix}/agents/by-token"
        headers = {"x-token": access_token}

        LOG.info("Fetching agent config from backend")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    LOG.info("Agent config fetched successfully")
                    return data
        except aiohttp.ClientError as e:
            LOG.error(f"Error fetching agent config: {e}")
            raise
        except Exception as e:
            LOG.error(f"Unexpected error fetching agent config: {e}", exc_info=True)
            raise

    async def fetch_agent_config_for_web(
        self, access_token: str, agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if agent_id is None:
            url = f"{self._base_url}{self._api_prefix}/agents/by-token"
        else:
            url = f"{self._base_url}{self._api_prefix}/agents/by-token/{agent_id}"
        headers = {"x-token": access_token}

        LOG.info(f"Fetching agent config for web agent (agent_id={agent_id})")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    LOG.info("Agent config fetched successfully for web agent")
                    return data
        except aiohttp.ClientError as e:
            LOG.error(f"Error fetching agent config for web agent: {e}")
            raise
        except Exception as e:
            LOG.error(
                f"Unexpected error fetching agent config for web agent: {e}",
                exc_info=True,
            )
            raise

    async def fetch_calendar_events(
        self,
        access_token: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[dict]:
        if not self._base_url:
            return []

        if not from_date:
            from_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        if not to_date:
            to_date = (datetime.now() + timedelta(days=60)).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

        url = f"{self._base_url}{self._api_prefix}/calendar-events/by-token"
        headers = {"x-token": access_token}
        params = {"from": from_date, "to": to_date}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception:
            return []


backend_client = BackendClient()
