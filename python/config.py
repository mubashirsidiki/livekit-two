from os import getenv
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv('.env.local')


class ConfigClass(BaseModel):
    openai_api_key: Optional[str] = None
    openai_embedding_model: str = "text-embedding-3-small"
    backend_url: Optional[str] = None
    backend_api_prefix: str = "/api"
    knowledge_base_default_limit: int = 5
    knowledge_base_search_limit: int = 3
    app_name: str = "livekit-agent"


class ConfigManager:
    def __init__(self):
        self._config = self._load_config()

    def _get_int_env(self, key: str, default: Optional[int] = None) -> Optional[int]:
        value = getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _load_config(self) -> ConfigClass:
        return ConfigClass(
            openai_api_key=getenv("OPENAI_API_KEY"),
            openai_embedding_model=getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            backend_url=getenv("BACKEND_URL", "https://dev.veraai.solutions"),
            backend_api_prefix=getenv("BACKEND_API_PREFIX", "/api"),
            knowledge_base_default_limit=self._get_int_env(
                "KNOWLEDGE_BASE_DEFAULT_LIMIT", 5
            )
            or 5,
            knowledge_base_search_limit=self._get_int_env(
                "KNOWLEDGE_BASE_SEARCH_LIMIT", 3
            )
            or 3,
        )

    @property
    def config(self) -> ConfigClass:
        return self._config


CONFIG_MANAGER = ConfigManager()
CONFIG = CONFIG_MANAGER.config