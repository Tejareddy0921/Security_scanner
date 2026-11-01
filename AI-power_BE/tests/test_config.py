import asyncio
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import BACKEND_ENV_FILE, Settings
from app.core.database import create_groq_client


def test_default_env_file_is_anchored_to_backend_directory():
    expected_path = Path(__file__).resolve().parents[1] / ".env"

    assert BACKEND_ENV_FILE == expected_path
    assert BACKEND_ENV_FILE.is_absolute()
    assert Settings.model_config["env_file"] == expected_path


def test_production_requires_explicit_secret_and_restricts_jwt_algorithm():
    with pytest.raises(ValidationError):
        Settings(environment="production", _env_file=None)
    assert Settings(environment="production", secret_key="a" * 40, _env_file=None).secret_key == "a" * 40
    with pytest.raises(ValidationError):
        Settings(algorithm="none", _env_file=None)


def test_groq_settings_use_secure_optional_key_and_configured_default_model():
    settings = Settings(secret_key="a" * 40, groq_api_key="", _env_file=None)
    assert settings.groq_api_key is None
    assert settings.groq_model == "openai/gpt-oss-20b"
    representation = repr(Settings(secret_key="a" * 40, groq_api_key="private-value", _env_file=None))
    assert "private-value" not in representation
    assert "groq_api_key=SecretStr('**********')" in representation


def test_groq_client_requires_a_key_and_uses_configured_timeout():
    assert create_groq_client(Settings(_env_file=None)) is None

    client = create_groq_client(
        Settings(groq_api_key="test-groq-key", groq_timeout_seconds=17, _env_file=None)
    )
    try:
        assert client is not None
        assert client.api_key == "test-groq-key"
        assert client.timeout == 17
        assert client.max_retries == 0
    finally:
        if client is not None:
            asyncio.run(client.close())


def test_settings_respect_existing_mongodb_and_client_url_names(monkeypatch):
    monkeypatch.setenv("MONGODB_DATABASE", "existing_scam_db")
    monkeypatch.setenv("CLIENT_URL", "https://scamguard.example")

    settings = Settings(_env_file=None)

    assert settings.database_name == "existing_scam_db"
    assert settings.allowed_origins[0] == "https://scamguard.example"
