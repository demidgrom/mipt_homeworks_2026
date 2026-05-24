from dataclasses import dataclass
from typing import Literal, TypedDict

Role = Literal['system', 'user', 'assistant']


class ChatMessage(TypedDict):
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    api_key: str
    api_host: str
    model: str
    limit_messages: int | None
    limit_chars: int | None
    temperature: float
    system_prompt: str | None
    stream: bool
