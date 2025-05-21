import os
import json
from document_processor import DocumentProcessor


def test_env_default_kb_precedence(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    processed_dir = tmp_path / "processed"
    uploads_dir = tmp_path / "uploads"

    config_dir.mkdir()
    processed_dir.mkdir()
    uploads_dir.mkdir()

    # create config file with some other kb id
    config_file = config_dir / "kb_default_config.json"
    config_file.write_text(json.dumps({"default_kb_id": "00000000-0000-0000-0000-000000000000"}))

    env_id = "11111111-1111-1111-1111-111111111111"

    monkeypatch.setenv("CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("PROCESSED_DIR", str(processed_dir))
    monkeypatch.setenv("UPLOADS_DIR", str(uploads_dir))
    monkeypatch.setenv("NEO4J_PASSWORD", "dummy")
    monkeypatch.setenv("DEFAULT_KB_ID", env_id)

    dp = DocumentProcessor()

    assert dp.default_kb_id == env_id
