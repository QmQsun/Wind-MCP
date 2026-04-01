"""
WindPy session singleton manager.

Usage:
    session = WindSession.get()
    result = session.w.wss("600030.SH", "close,pe_ttm")

Thread safety: All Wind API calls should go through core.executor.run_wind()
to ensure serialized access. The Lock here is a belt-and-suspenders safeguard.
"""

from WindPy import w
import logging
import atexit
import threading
import time

logger = logging.getLogger(__name__)


class WindSession:
    """Singleton wrapper around WindPy connection."""

    _instance: "WindSession | None" = None
    _started: bool = False
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get(cls) -> "WindSession":
        """Get the WindSession singleton, starting connection if needed."""
        instance = cls()
        with cls._lock:
            if not cls._started:
                cls._start()
            elif not cls.is_connected():
                logger.warning("Wind connection lost. Attempting reconnect...")
                cls.reconnect()
        return instance

    @classmethod
    def _start(cls):
        """Start Wind connection (must be called under _lock)."""
        logger.info("Starting Wind connection...")
        result = w.start()
        if result.ErrorCode != 0:
            raise ConnectionError(
                f"Wind start failed with error code {result.ErrorCode}: {result.Data}"
            )
        cls._started = True
        atexit.register(cls._shutdown)
        logger.info("Wind connection established.")

    @classmethod
    def reconnect(cls, max_retries: int = 3, base_backoff: float = 1.0):
        """
        Reconnect to Wind with exponential backoff.
        Must be called under _lock or from a serialized context.
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Reconnect attempt {attempt}/{max_retries}...")
                try:
                    w.stop()
                except Exception:
                    pass  # stop() may fail if already disconnected
                result = w.start()
                if result.ErrorCode == 0:
                    cls._started = True
                    logger.info("Wind reconnection successful.")
                    return
                logger.warning(f"Reconnect attempt {attempt} failed: ErrorCode={result.ErrorCode}")
            except Exception as e:
                logger.warning(f"Reconnect attempt {attempt} exception: {e}")

            if attempt < max_retries:
                backoff = base_backoff * (2 ** (attempt - 1))
                logger.info(f"Waiting {backoff:.1f}s before next attempt...")
                time.sleep(backoff)

        cls._started = False
        raise ConnectionError(
            f"Wind reconnection failed after {max_retries} attempts"
        )

    @classmethod
    def health_check(cls) -> dict:
        """Return connection health status."""
        connected = cls.is_connected()
        return {
            "connected": connected,
            "started": cls._started,
        }

    @property
    def w(self):
        """Return the global WindPy `w` object."""
        return w

    @classmethod
    def _shutdown(cls):
        if cls._started:
            logger.info("Shutting down Wind connection...")
            try:
                w.stop()
            except Exception as e:
                logger.warning(f"Error during Wind shutdown: {e}")
            cls._started = False

    @classmethod
    def is_connected(cls) -> bool:
        """Check if Wind is currently connected."""
        try:
            return cls._started and w.isconnected()
        except Exception:
            return False
