from collections.abc import Iterable
from typing import Protocol, cast

import httpx
from openai import OpenAI, OpenAIError
from openai.types.chat import (
    ChatCompletionChunk,
    ChatCompletionMessageParam,
)

from gigavibemiptcode.models import AppConfig, ChatMessage


class LlmError(Exception):
    """Raised when an LLM server request fails."""


class LlmClient(Protocol):
    def stream_chat(self, messages: list[ChatMessage]) -> Iterable[str]: ...

    def chat_once(self, messages: list[ChatMessage]) -> str: ...


class OpenAiCompatibleClient:
    def __init__(self, config: AppConfig) -> None:
        self._model = config.model
        self._temperature = config.temperature
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_host,
            http_client=httpx.Client(trust_env=False),
        )

    def stream_chat(self, messages: list[ChatMessage]) -> Iterable[str]:
        try:
            stream = cast(
                Iterable[ChatCompletionChunk],
                self._client.chat.completions.create(
                    model=self._model,
                    messages=self._to_openai_messages(messages),
                    temperature=self._temperature,
                    stream=True,
                ),
            )

            for event in stream:
                if not event.choices:
                    continue

                delta = event.choices[0].delta.content
                if delta is not None:
                    yield delta

        except OpenAIError as exc:
            raise LlmError(f'LLM request failed: {exc}') from exc

    def chat_once(self, messages: list[ChatMessage]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages),
                temperature=self._temperature,
                stream=False,
            )

        except OpenAIError as exc:
            raise LlmError(f'LLM request failed: {exc}') from exc

        if not response.choices:
            return ''

        content = response.choices[0].message.content
        return content or ''

    @staticmethod
    def _to_openai_messages(
        messages: list[ChatMessage],
    ) -> list[ChatCompletionMessageParam]:
        raw_messages = [
            {
                'role': message['role'],
                'content': message['content'],
            }
            for message in messages
        ]

        return cast(list[ChatCompletionMessageParam], raw_messages)
