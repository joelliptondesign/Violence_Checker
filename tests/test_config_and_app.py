import importlib


def _disable_local_env(monkeypatch, config):
    monkeypatch.setattr(config, "load_dotenv", lambda path: False)

def test_config_imports_without_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    config = importlib.import_module("src.config")

    _disable_local_env(monkeypatch, config)
    loaded = config.load_config(streamlit_secrets={})

    assert loaded.openai_api_key is None
    assert "streamlit" not in config.__dict__


def test_production_config_loads_repository_env_when_enabled(monkeypatch):
    config = importlib.import_module("src.config")
    loaded_paths = []

    def record_load_dotenv(path):
        loaded_paths.append(path)
        return False

    monkeypatch.delenv("PYTHON_DOTENV_DISABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "load_dotenv", record_load_dotenv)

    config.load_config(streamlit_secrets={})

    assert loaded_paths == [config.ROOT_DIR / ".env"]


def test_streamlit_secrets_take_precedence_over_environment(monkeypatch):
    config = importlib.import_module("src.config")
    _disable_local_env(monkeypatch, config)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")
    monkeypatch.setenv("OPENAI_MODEL", "environment-model")
    monkeypatch.setenv("OPENAI_COMMUNICATION_MODEL", "environment-communication-model")

    loaded = config.load_config(
        streamlit_secrets={
            "OPENAI_API_KEY": "streamlit-key",
            "OPENAI_MODEL": "streamlit-model",
            "OPENAI_COMMUNICATION_MODEL": "streamlit-communication-model",
        }
    )

    assert loaded.openai_api_key == "streamlit-key"
    assert loaded.openai_model == "streamlit-model"
    assert loaded.openai_communication_model == "streamlit-communication-model"


def test_environment_fallback_is_used_when_streamlit_secrets_are_absent(monkeypatch):
    config = importlib.import_module("src.config")
    _disable_local_env(monkeypatch, config)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")
    monkeypatch.setenv("OPENAI_MODEL", "environment-model")
    monkeypatch.setenv("OPENAI_COMMUNICATION_MODEL", "environment-communication-model")

    loaded = config.load_config(streamlit_secrets={})

    assert loaded.openai_api_key == "environment-key"
    assert loaded.openai_model == "environment-model"
    assert loaded.openai_communication_model == "environment-communication-model"


def test_local_dotenv_is_lowest_precedence_fallback(monkeypatch):
    config = importlib.import_module("src.config")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_COMMUNICATION_MODEL", raising=False)

    def simulated_local_dotenv(path):
        monkeypatch.setenv("OPENAI_API_KEY", "local-development-key")
        monkeypatch.setenv("OPENAI_MODEL", "local-development-model")
        monkeypatch.setenv("OPENAI_COMMUNICATION_MODEL", "local-communication-model")
        return True

    monkeypatch.setattr(config, "load_dotenv", simulated_local_dotenv)
    loaded = config.load_config(streamlit_secrets={})

    assert loaded.openai_api_key == "local-development-key"
    assert loaded.openai_model == "local-development-model"
    assert loaded.openai_communication_model == "local-communication-model"


def test_communication_model_has_separate_deterministic_default(monkeypatch):
    config = importlib.import_module("src.config")
    _disable_local_env(monkeypatch, config)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_COMMUNICATION_MODEL", raising=False)

    loaded = config.load_config(streamlit_secrets={})

    assert loaded.openai_model == config.DEFAULT_OPENAI_MODEL
    assert loaded.openai_communication_model == config.DEFAULT_OPENAI_COMMUNICATION_MODEL


def test_guarded_streamlit_secret_loader_is_used_without_exposing_values(monkeypatch):
    config = importlib.import_module("src.config")
    _disable_local_env(monkeypatch, config)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        config,
        "_load_streamlit_secrets",
        lambda: {"OPENAI_API_KEY": "deployment-secret"},
    )

    loaded = config.load_config()

    assert loaded.openai_api_key == "deployment-secret"


def test_app_imports_without_openai_api_call(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    app = importlib.import_module("app")

    assert hasattr(app, "main")
