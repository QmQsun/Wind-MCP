"""
WindPy session singleton manager.

Usage:
    session = WindSession.get()
    result = session.w.wss("600030.SH", "close,pe_ttm")
"""

from WindPy import w
import logging
import atexit

logger = logging.getLogger(__name__)


class WindSession:
    """Singleton wrapper around WindPy connection."""

    _instance: "WindSession | None" = None
    _started: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get(cls) -> "WindSession":
        instance = cls()
        if not cls._started:
            logger.info("Starting Wind connection...")
            result = w.start()
            if result.ErrorCode != 0:
                raise ConnectionError(
                    f"Wind start failed with error code {result.ErrorCode}: {result.Data}"
                )
            cls._started = True
            atexit.register(cls._shutdown)
            logger.info("Wind connection established.")
        return instance

    @property
    def w(self):
        """Return the global WindPy `w` object."""
        return w

    @classmethod
    def _shutdown(cls):
        if cls._started:
            logger.info("Shutting down Wind connection...")
            w.stop()
            cls._started = False

    @classmethod
    def is_connected(cls) -> bool:
        return cls._started and w.isconnected()
