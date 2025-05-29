from __future__ import annotations
import time
import inspect
import asyncio
from logging import Logger
from functools import wraps
try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # For Python < 3.10
from typing import Awaitable, Callable, TypeVar, Type, Union, Optional, overload



P = ParamSpec('P')
R = TypeVar('R')
E = TypeVar('E', bound=Exception)


def _log_retry(attempt: int, e: Exception, logger: Optional[Logger]) -> None:
    msg = f"[retry] Attempt {attempt} failed: {type(e).__name__}({e})"
    (logger.warning if logger else print)(msg)

def _log_failure(max_attempts: int, e: Exception, logger: Optional[Logger]) -> None:
    msg = f"[retry] All {max_attempts} attempts failed"
    (logger.error if logger else print)(msg)

def _log_success(attempt: int, logger: Optional[Logger]) -> None:
    if attempt > 1:
        msg = f"[retry] Succeeded after {attempt} attempts"
        (logger.info if logger else print)(msg)

def _calc_delay(base: float, attempt: int) -> float:
    return base * (2 ** (attempt - 1))

@overload
def retry(
    tries: int = ...,
    delay: float = ...,
    catch_errors: Union[Type[E], tuple[Type[E], ...]] = ...,
    throw_error: Optional[Exception] = ...,
    logger: Optional[Logger] = ...
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

@overload
def retry(
    tries: int = ...,
    delay: float = ...,
    catch_errors: Union[Type[E], tuple[Type[E], ...]] = ...,
    throw_error: Optional[Exception] = ...,
    logger: Optional[Logger] = ...
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]: ...

def retry(
    tries: int = 3,
    delay: float = 1,
    catch_errors: Union[Type[E], tuple[Type[E], ...]] = Exception,
    throw_error: Optional[Exception] = None,
    logger: Optional[Logger] = None
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Configurable retry decorator with exponential backoff and logging."""
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        is_async = inspect.iscoroutinefunction(func)
        sleep_fn = asyncio.sleep if is_async else time.sleep
        
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc = None
            for attempt in range(1, tries+1):
                try:
                    result = func(*args, **kwargs)
                    _log_success(attempt, logger)
                    return result
                except catch_errors as e:
                    last_exc = e
                    _log_retry(attempt, e, logger)
                    if attempt < tries:
                        time.sleep(_calc_delay(delay, attempt))
            _log_failure(tries, last_exc, logger)
            raise throw_error or last_exc or RuntimeError("Retry failed")
        
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc = None
            for attempt in range(1, tries+1):
                try:
                    result = await func(*args, **kwargs)
                    _log_success(attempt, logger)
                    return result
                except catch_errors as e:
                    last_exc = e
                    _log_retry(attempt, e, logger)
                    if attempt < tries:
                        await sleep_fn(_calc_delay(delay, attempt))
            _log_failure(tries, last_exc, logger)
            raise throw_error or last_exc or RuntimeError("Retry failed")
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator