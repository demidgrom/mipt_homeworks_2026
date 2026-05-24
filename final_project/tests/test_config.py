from pathlib import Path

import pytest

from gigavibemiptcode.config import ConfigError, load_config


def test_load_config_from_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('API_KEY', raising=False)
    path = tmp_path / 'config.yaml'
    path.write_text(
        '\n'.join(
            [
                'api_key: ollama',
                'api_host: http://localhost:11434/v1/',
                'model: gemma3:270m',
                'limit_messages: 2',
                'limit_chars: 100',
                'temperature: 0.3',
                'stream: true',
            ]
        ),
        encoding='utf-8',
    )

    config = load_config(path)

    assert config.api_key == 'ollama'
    assert config.limit_messages == 2
    assert config.limit_chars == 100
    assert config.temperature == 0.3
    assert config.stream is True


def test_env_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / 'config.yaml'
    path.write_text(
        'api_key: old\napi_host: old\nmodel: old\nlimit_chars: 100\n',
        encoding='utf-8',
    )
    monkeypatch.setenv('API_KEY', 'new')
    monkeypatch.setenv('API_HOST', 'http://localhost:11434/v1/')
    monkeypatch.setenv('MODEL', 'gemma3:270m')

    config = load_config(path)

    assert config.api_key == 'new'
    assert config.api_host == 'http://localhost:11434/v1/'
    assert config.model == 'gemma3:270m'


def test_missing_config_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ['API_KEY', 'API_HOST', 'MODEL']:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ConfigError):
        load_config(tmp_path / 'absent.yaml')
