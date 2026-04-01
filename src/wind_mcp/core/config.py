"""
Centralized configuration for Wind MCP.

Load priority:
1. Environment variables WIND_MCP_* (highest)
2. wind_mcp.toml file (project root)
3. Code defaults (lowest)
"""

import logging
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WindMCPConfig:
    """All configurable parameters for Wind MCP server."""

    # --- Session ---
    connect_timeout: int = 30
    reconnect_retries: int = 3
    reconnect_backoff: float = 1.0

    # --- Cache TTL (seconds) ---
    cache_maxsize: int = 2000
    cache_ttl_realtime: int = 30
    cache_ttl_snapshot: int = 300
    cache_ttl_historical: int = 43200
    cache_ttl_minute_bars: int = 300
    cache_ttl_ticks: int = 60
    cache_ttl_dataset: int = 86400
    cache_ttl_macro: int = 86400
    cache_ttl_sector: int = 86400
    cache_ttl_screening: int = 600
    cache_ttl_estimates: int = 14400
    cache_ttl_holders: int = 86400
    cache_ttl_dates: int = 86400
    cache_ttl_portfolio: int = 300

    # --- Resilience ---
    api_timeout: float = 30.0
    api_retries: int = 2
    api_backoff: float = 1.0

    # --- Logging ---
    log_format: str = "text"  # "json" or "text"
    log_level: str = "INFO"

    def get_cache_ttl_map(self) -> dict[str, int]:
        """Build cache TTL dict from config fields."""
        return {
            "realtime": self.cache_ttl_realtime,
            "snapshot": self.cache_ttl_snapshot,
            "historical": self.cache_ttl_historical,
            "minute_bars": self.cache_ttl_minute_bars,
            "ticks": self.cache_ttl_ticks,
            "dataset": self.cache_ttl_dataset,
            "macro": self.cache_ttl_macro,
            "sector": self.cache_ttl_sector,
            "screening": self.cache_ttl_screening,
            "estimates": self.cache_ttl_estimates,
            "holders": self.cache_ttl_holders,
            "dates": self.cache_ttl_dates,
            "portfolio": self.cache_ttl_portfolio,
            "static": 86400,
        }


def _load_toml(path: Path) -> dict[str, Any]:
    """Load TOML config file if it exists."""
    if not path.exists():
        return {}
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            logger.warning("No TOML parser available. Install tomli for Python <3.11.")
            return {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        # Flatten nested sections: [cache] ttl_snapshot=300 → cache_ttl_snapshot=300
        flat = {}
        for section, values in data.items():
            if isinstance(values, dict):
                for k, v in values.items():
                    flat[f"{section}_{k}"] = v
            else:
                flat[section] = values
        return flat
    except Exception as e:
        logger.warning(f"Failed to parse {path}: {e}")
        return {}


def _load_env() -> dict[str, Any]:
    """Load config from environment variables WIND_MCP_*."""
    prefix = "WIND_MCP_"
    result = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            # Auto-cast
            if value.lower() in ("true", "false"):
                result[config_key] = value.lower() == "true"
            else:
                try:
                    result[config_key] = int(value)
                except ValueError:
                    try:
                        result[config_key] = float(value)
                    except ValueError:
                        result[config_key] = value
    return result


def load_config(toml_path: Path | None = None) -> WindMCPConfig:
    """
    Load config with priority: env vars > TOML file > defaults.

    Args:
        toml_path: Path to wind_mcp.toml. If None, searches project root.
    """
    config = WindMCPConfig()

    # Find TOML path
    if toml_path is None:
        # Search upward from this file for wind_mcp.toml
        search = Path(__file__).resolve().parent
        for _ in range(5):
            candidate = search / "wind_mcp.toml"
            if candidate.exists():
                toml_path = candidate
                break
            search = search.parent

    # Layer 1: TOML file
    if toml_path:
        toml_data = _load_toml(toml_path)
        valid_fields = {f.name for f in fields(config)}
        for k, v in toml_data.items():
            if k in valid_fields:
                setattr(config, k, v)

    # Layer 2: Environment variables (override TOML)
    env_data = _load_env()
    valid_fields = {f.name for f in fields(config)}
    for k, v in env_data.items():
        if k in valid_fields:
            setattr(config, k, v)

    return config


# Global singleton
_config: WindMCPConfig | None = None


def get_config() -> WindMCPConfig:
    """Get the global config singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
