from __future__ import annotations
import random
import time
import inspect
import asyncio
from logging import Logger
from functools import wraps
try:
    from typing import ParamSpec  # Python 3.10+
except ImportError:
    from typing_extensions import ParamSpec  # For Python < 3.10
from typing import Awaitable, Callable, TypeVar, Type, Union, Optional



P = ParamSpec('P')
R = TypeVar('R')
E = TypeVar('E', bound=Exception)


LogHandler = Optional[Union[Logger, Callable[[str], None]]]
Retry = Callable[[Callable[P, R]], Callable[P, R]]
AsyncRetry = Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]
RetryDecorator = Union[Retry, AsyncRetry]


def _log_retry(attempt: int, e: Exception, logger: LogHandler) -> None:
    if logger is None:
        return
    msg = f"[retry] Attempt {attempt} failed: {type(e).__name__}({e})"
    (logger.warning if isinstance(logger, Logger) else logger)(msg)

def _log_failure(max_attempts: int, e: Exception, logger: LogHandler) -> None:
    if logger is None:
        return
    msg = f"[retry] All {max_attempts} attempts failed"
    (logger.error if isinstance(logger, Logger) else logger)(msg)

def _log_success(attempt: int, logger: LogHandler) -> None:
    if logger is None:
        return
    if attempt > 1:
        msg = f"[retry] Succeeded after {attempt} attempts"
        (logger.info if isinstance(logger, Logger) else logger)(msg)

def _calc_delay(base: float, attempt: int, jitter: Union[bool, float]) -> float:
    delay = base * (2 ** (attempt - 1))
    if jitter is True:
        return random.uniform(0, delay)  # Full jitter
    elif isinstance(jitter, (int, float)) and jitter > 0:
        return delay + random.uniform(0, jitter)  # Additive jitter
    return delay




def retry(
    catch_errors: Union[Type[E], tuple[Type[E], ...]],
    tries: int = 3,
    delay: float = 1,
    throw_error: Optional[Exception] = None,
    logger: LogHandler = None,
    jitter: Union[bool, float] = False
) -> RetryDecorator:
    """
    Retry decorator with configurable backoff strategy for sync and async functions.

    Retries the decorated function upon catching specified exceptions, with optional
    exponential backoff, jitter, and logging. Supports both synchronous and asynchronous
    functions transparently.

    Args:
        catch_errors (Type[Exception] or tuple[Type[Exception], ...]):
            Exception type(s) to catch and retry on.
        tries (int): 
            Total number of attempts (initial call + retries). Default is 3.
        delay (float): 
            Initial delay in seconds before retrying. Backoff is exponential. Default is 1.
        throw_error (Exception, optional): 
            If provided, this exception will be raised after final failure instead of the last one caught.
        logger (Logger or Callable[[str], None], optional): 
            Logger instance or callable to receive retry logs. Supports `logging.Logger` or `print`-style functions.
        jitter (bool or float): 
            Controls randomness in retry delays.
            - `False` (default): No jitter.
            - `True`: Full jitter. Delay is `random.uniform(0, backoff)`.
            - `float`: Additive jitter. Delay is `backoff + random.uniform(0, jitter)`.

    Returns:
        Callable: A decorated function that will be retried upon specified exceptions.

    Raises:
        Exception: The last caught exception, or `throw_error` if provided.
    """
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        is_async = inspect.iscoroutinefunction(func)
        
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
                        time.sleep(_calc_delay(delay, attempt, jitter))
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
                        await asyncio.sleep(_calc_delay(delay, attempt, jitter))
            _log_failure(tries, last_exc, logger)
            raise throw_error or last_exc or RuntimeError("Retry failed")
        
        return async_wrapper if is_async else sync_wrapper
    
    return decorator