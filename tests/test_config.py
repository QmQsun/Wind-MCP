"""Tests for configuration loading."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wind_mcp.core.config import WindMCPConfig, load_config, _load_env


def test_config_defaults():
    config = WindMCPConfig()
    assert config.connect_timeout == 30
    assert config.cache_maxsize == 2000
    assert config.cache_ttl_realtime == 30
    assert config.cache_ttl_snapshot == 300
    assert config.api_timeout == 30.0
    assert config.api_retries == 2
    assert config.log_level == "INFO"


def test_config_cache_ttl_map():
    config = WindMCPConfig()
    ttl_map = config.get_cache_ttl_map()
    assert ttl_map["realtime"] == 30
    assert ttl_map["snapshot"] == 300
    assert ttl_map["historical"] == 43200
    assert ttl_map["static"] == 86400
    assert "portfolio" in ttl_map


def test_config_load_from_toml(tmp_path):
    toml_file = tmp_path / "wind_mcp.toml"
    toml_file.write_text(
        '[cache]\nmaxsize = 5000\nttl_realtime = 10\n\n[api]\ntimeout = 60.0\n'
    )
    config = load_config(toml_path=toml_file)
    assert config.cache_maxsize == 5000
    assert config.cache_ttl_realtime == 10
    assert config.api_timeout == 60.0


def test_config_env_override(monkeypatch):
    monkeypatch.setenv("WIND_MCP_CACHE_MAXSIZE", "9999")
    monkeypatch.setenv("WIND_MCP_API_TIMEOUT", "45.0")
    env = _load_env()
    assert env["cache_maxsize"] == 9999
    assert env["api_timeout"] == 45.0


def test_config_env_bool_cast(monkeypatch):
    monkeypatch.setenv("WIND_MCP_LOG_FORMAT", "json")
    env = _load_env()
    assert env["log_format"] == "json"
