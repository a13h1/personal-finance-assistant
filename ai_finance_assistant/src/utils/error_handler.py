import logging
import functools
from typing import Any, Callable

logging.basicConfig(level=logging.INFO)
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
