import logging
import os
import functools
from typing import Any, Callable

log_level_name = os.environ.get("LANGFUSE_LOG_LEVEL", os.environ.get("LOG_LEVEL", "INFO")).upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def with_fallback(fallback_message: str = "I'm sorry, I encountered an error. Please try again."):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return fallback_message
        return wrapper
    return decorator
