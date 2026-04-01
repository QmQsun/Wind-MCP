"""
Wind API resilience layer — timeout, retry, and degradation.

Wraps Wind API calls with:
1. Timeout via executor Future.result(timeout=N)
2. Retry on transient errors with exponential backoff
3. Stale cache fallback when all retries exhausted
"""

import logging
import time
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Any, Callable

from .cache import get_cache
from .executor import run_wind_sync
from .parser import WindAPIError
from .session import WindSession

logger = logging.getLogger(__name__)

# Wind error codes that are transient (connection issues, server busy)
# These will trigger retry. Non-transient errors fail immediately.
# NOTE: This set should be expanded based on real-world observation.
TRANSIENT_ERRORS = {
    -40520001,  # Connection timeout
    -40520002,  # Server busy
    -40520003,  # Network error
    -40520004,  # Connection lost
    -40520005,  # Login timeout
    -40520007,  # Service unavailable
    -40521001,  # Data service timeout
    -40521002,  # Data request timeout
}


def wind_call_with_resilience(
    func: Callable,
    *args: Any,
    timeout: float = 30.0,
    retries: int = 2,
    backoff: float = 1.0,
    cache_category: str | None = None,
    cache_key_args: tuple = (),
    **kwargs: Any,
) -> Any:
    """
    Execute a Wind API call with timeout, retry, and stale-cache fallback.

    Args:
        func: The Wind API function (e.g., session.w.wss)
        *args: Positional args to pass to func
        timeout: Max seconds to wait for the call
        retries: Number of retry attempts for transient errors
        backoff: Base backoff time in seconds (doubles each retry)
        cache_category: Cache category for stale fallback (e.g., "snapshot")
        cache_key_args: Args used to build the cache key for stale fallback
        **kwargs: Keyword args to pass to func

    Returns:
        The Wind API result (raw WindData object, NOT parsed)

    Raises:
        WindAPIError: On non-transient Wind errors
        TimeoutError: If all retries time out
        ConnectionError: If Wind is disconnected and reconnect fails
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            # Ensure connection is alive
            session = WindSession.get()  # This triggers reconnect if needed

            # Execute through the serialized executor with timeout
            from concurrent.futures import ThreadPoolExecutor
            from .executor import _executor

            future = _executor.submit(func, *args, **kwargs)
            result = future.result(timeout=timeout)

            # Check Wind error code
            if hasattr(result, "ErrorCode") and result.ErrorCode != 0:
                error_code = result.ErrorCode
                error_msg = str(result.Data[0]) if result.Data and result.Data[0] else ""

                if error_code in TRANSIENT_ERRORS:
                    last_error = WindAPIError(error_code, error_msg)
                    logger.warning(
                        f"Transient Wind error {error_code} on attempt {attempt}/{retries}: {error_msg}"
                    )
                    if attempt < retries:
                        wait = backoff * (2 ** (attempt - 1))
                        time.sleep(wait)
                        continue
                else:
                    # Non-transient error — fail immediately
                    raise WindAPIError(error_code, error_msg)

            return result

        except FuturesTimeoutError:
            last_error = TimeoutError(f"Wind API call timed out after {timeout}s")
            logger.warning(f"Timeout on attempt {attempt}/{retries}")
            if attempt < retries:
                wait = backoff * (2 ** (attempt - 1))
                time.sleep(wait)
                continue

        except ConnectionError as e:
            last_error = e
            logger.warning(f"Connection error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                wait = backoff * (2 ** (attempt - 1))
                time.sleep(wait)
                continue

    # All retries exhausted — try stale cache fallback
    if cache_category and cache_key_args:
        cache = get_cache()
        stale = cache.stale_get(cache_category, *cache_key_args)
        if stale is not None:
            logger.warning(
                f"All retries exhausted. Returning stale cached data for {cache_category}"
            )
            # Mark data as stale
            if isinstance(stale, list):
                for row in stale:
                    if isinstance(row, dict):
                        row["_stale"] = True
            return stale

    # No fallback available — raise the last error
    if last_error:
        raise last_error
    raise RuntimeError("Wind API call failed with no error details")
