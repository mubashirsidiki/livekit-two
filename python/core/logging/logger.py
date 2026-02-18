import logging
from typing import Any, Dict
from config import CONFIG
from logging.config import dictConfig


class LoggerManager:
    def __init__(self):
        self._log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "core.logging.handler.JsonFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                CONFIG.app_name: {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
        self._setup_logging()

    def _setup_logging(self):
        dictConfig(self._log_config)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(CONFIG.app_name)


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        extra = self.extra.copy()
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = extra
        return msg, kwargs


_logger_manager = LoggerManager()
LOG = _logger_manager.logger


def get_logger(**context) -> ContextLoggerAdapter:
    return ContextLoggerAdapter(LOG, context)


LOG.info(f"{CONFIG.app_name} logger initialized")
