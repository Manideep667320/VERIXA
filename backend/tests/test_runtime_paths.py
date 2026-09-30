from pathlib import Path

from app.core import config, database


def test_env_file_is_anchored_to_repository_root():
    configured_env = Path(config.Settings.model_config["env_file"]).resolve()
    expected_env = Path(config.__file__).resolve().parents[3] / ".env"

    assert configured_env == expected_env


def test_relative_database_path_is_independent_of_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    resolved = database.resolve_database_path("sqlite:///./data/evidence_to_action.db")
    expected = Path(database.__file__).resolve().parents[2] / "data" / "evidence_to_action.db"

    assert resolved == expected.resolve()
