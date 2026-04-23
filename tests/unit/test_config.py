import os
from unittest.mock import patch

import pytest

from simple_agent.config import AgentConfig, AgentConfigError


def test_from_env_reads_all_values():
    env = {
        "ANTHROPIC_BASE_URL": "https://test.api",
        "ANTHROPIC_AUTH_TOKEN": "test-key",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "test-model",
        "AGENT_MAX_STEPS": "10",
        "AGENT_LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env, clear=False):
        config = AgentConfig.from_env()
    assert config.base_url == "https://test.api"
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.max_steps == 10
    assert config.log_level == "DEBUG"


def test_missing_api_key_raises():
    with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": ""}, clear=False):
        with pytest.raises(AgentConfigError, match="ANTHROPIC_AUTH_TOKEN"):
            AgentConfig.from_env()


def test_defaults():
    env = {"ANTHROPIC_AUTH_TOKEN": "key"}
    with patch.dict(os.environ, env, clear=False):
        config = AgentConfig.from_env()
    assert config.max_steps == 5
    assert config.log_level == "INFO"
