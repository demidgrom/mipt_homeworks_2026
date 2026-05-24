import os
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import yaml

from gigavibemiptcode.models import AppConfig


class ConfigError(Exception):
    """Raised when application configuration is missing or invalid."""


_ENV_TO_KEY: dict[str, str] = {
    'API_KEY': 'api_key',
    'API_HOST': 'api_host',
    'MODEL': 'model',
    'LIMIT_MESSAGE': 'limit_message',
    'LIMIT_MESSAGES': 'limit_messages',
    'LIMIT_CHARS': 'limit_chars',
    'TEMPERATURE': 'temperature',
    'STREAM': 'stream',
}


def _read_yaml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}

    try:
        raw: object = yaml.safe_load(path.read_text(encoding='utf-8'))
    except OSError as exc:
        raise ConfigError(f'Cannot read config file {path}: {exc}') from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f'Invalid YAML in {path}: {exc}') from exc

    if raw is None:
        return {}

    if not isinstance(raw, Mapping):
        raise ConfigError('config.yaml must contain a mapping at top level')

    return {str(key): cast(object, value) for key, value in raw.items()}


def _env_overrides() -> dict[str, object]:
    result: dict[str, object] = {}

    for env_name, key in _ENV_TO_KEY.items():
        value = os.environ.get(env_name)

        if value is not None:
            result[key] = value

    return result


def _optional_positive_int(value: object, name: str) -> int | None:
    if value is None or value == '':
        return None

    if isinstance(value, bool):
        raise ConfigError(f'{name} must be an integer')

    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ConfigError(f'{name} must be an integer') from exc
    else:
        raise ConfigError(f'{name} must be an integer')

    if parsed <= 0:
        raise ConfigError(f'{name} must be positive')

    return parsed


def _temperature(value: object) -> float:
    if value is None or value == '':
        return 0.2

    if isinstance(value, bool):
        raise ConfigError('temperature must be a float')

    if isinstance(value, int | float):
        parsed = float(value)

    elif isinstance(value, str):
        try:
            parsed = float(value.strip())
        except ValueError as exc:
            raise ConfigError('temperature must be a float') from exc
    else:
        raise ConfigError('temperature must be a float')

    if not 0 <= parsed <= 1:
        raise ConfigError('temperature must be from 0 to 1')

    return parsed


def _bool(value: object, default: bool) -> bool:
    if value is None or value == '':
        return default

    if isinstance(value, bool):
        return value

    lowered = str(value).strip().lower()

    if lowered in {'1', 'true', 'yes', 'y', 'on'}:
        return True

    if lowered in {'0', 'false', 'no', 'n', 'off'}:
        return False

    raise ConfigError('stream must be boolean')


def _required_string(data: dict[str, object], key: str) -> str:
    value = str(data.get(key, '')).strip()

    if not value:
        raise ConfigError(f'{key} is required')

    return value


def _optional_string(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def load_config(path: str | Path = 'config.yaml') -> AppConfig:
    data = _read_yaml(Path(path))
    data.update(_env_overrides())

    if not data:
        raise ConfigError(
            'No configuration found. Create config.yaml or set environment variables.'
        )

    return AppConfig(
        api_key=_required_string(data, 'api_key'),
        api_host=_required_string(data, 'api_host'),
        model=_required_string(data, 'model'),
        limit_messages=_optional_positive_int(
            data.get('limit_messages', data.get('limit_message')),
            'limit_messages',
        ),
        limit_chars=_optional_positive_int(
            data.get('limit_chars'),
            'limit_chars',
        ),
        temperature=_temperature(data.get('temperature')),
        system_prompt=_optional_string(data, 'system_prompt'),
        stream=_bool(data.get('stream'), default=True),
    )
