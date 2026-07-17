import importlib

def test_config_imports_without_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    config = importlib.import_module("src.config")

    loaded = config.load_config()

    assert loaded.openai_api_key is None


def test_production_config_loads_repository_env_when_enabled(monkeypatch):
    config = importlib.import_module("src.config")
    loaded_paths = []

    def record_load_dotenv(path):
        loaded_paths.append(path)
        return False

    monkeypatch.delenv("PYTHON_DOTENV_DISABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "load_dotenv", record_load_dotenv)

    config.load_config()

    assert loaded_paths == [config.ROOT_DIR / ".env"]


def test_app_imports_without_openai_api_call(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    app = importlib.import_module("app")

    assert hasattr(app, "main")
