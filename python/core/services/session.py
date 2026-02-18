from datetime import datetime
from core.logging.logger import LOG
from typing import Any, Dict, Optional
from core.clients.backend import BackendClient
from core.models import SessionRequest, SessionRequestDict
from pydantic import ValidationError as PydanticValidationError
from core.clients import backend_client


class SessionService:
    async def _fetch_agent_config(
        self, access_token: str, agent_id: Optional[str] = None
    ) -> SessionRequestDict:
        LOG.info("Fetching agent configuration")

        if not access_token:
            LOG.error("access_token is required")
            raise ValueError("access_token is required")

        if not agent_id:
            LOG.error("agent_id is required")
            raise ValueError("agent_id is required")

        try:
            config_data = await backend_client.fetch_agent_config_for_web(
                agent_id=agent_id, access_token=access_token
            )
            validated = SessionRequest(**config_data)
            LOG.info("Agent configuration validated successfully")
            return validated.model_dump()

        except PydanticValidationError as e:
            LOG.error(f"Agent configuration validation failed: {e}")
            raise ValueError(f"Invalid agent configuration: {e}") from e
        except Exception as e:
            LOG.error(f"Error fetching agent configuration: {e}")
            raise

    def _format_calendar_events_for_prompt(self, events: list[dict]) -> str:
        if not events:
            return ""

        lines = ["## Upcoming Bookings (do not double-book these times):", ""]
        for e in events:
            title = e.get("title", "Unknown Event")
            start = e.get("start_time", e.get("start", "TBD"))
            end = e.get("end_time", e.get("end", "TBD"))
            provider = e.get("provider", "Unknown")
            lines.append(f"- {title} | {start} - {end} | {provider}")
        lines.append("")
        return "\n".join(lines)

    async def _process_instructions_config(
        self, config: Dict[str, Any], access_token: str
    ) -> SessionRequestDict:
        instructions = config.get("instructions", "")

        if isinstance(instructions, list):
            filtered_instructions = [
                str(item) for item in instructions if item is not None
            ]
            instructions = (
                "\n".join(filtered_instructions) if filtered_instructions else ""
            )
        elif not isinstance(instructions, str):
            instructions = str(instructions)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        instructions = f"Current date and time: {current_time}\n\n{instructions}"

        if access_token:
            try:
                events = await backend_client.fetch_calendar_events(access_token)
                if events:
                    calendar_section = self._format_calendar_events_for_prompt(events)
                    instructions = f"{calendar_section}\n\n{instructions}"
            except Exception:
                pass

        config["instructions"] = instructions
        LOG.info("Instructions processed - ready for Livekit")
        return config

    async def setup_session(self, access_token: str, agent_id: Optional[str] = None):
        config = await self._fetch_agent_config(
            agent_id=agent_id, access_token=access_token
        )

        if not config:
            raise ValueError("Invalid configuration")

        config = await self._process_instructions_config(
            config, access_token=access_token
        )

        return config


session_service = SessionService()
