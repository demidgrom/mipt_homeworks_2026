from gigavibemiptcode.models import ChatMessage, Role


class MessageHistory:
    def __init__(self, limit_messages: int | None, limit_chars: int | None) -> None:
        self._messages: list[ChatMessage] = []
        self._limit_messages: int | None = limit_messages
        self._limit_chars: int | None = limit_chars

    @property
    def messages(self) -> list[ChatMessage]:
        return self._messages.copy()

    def append(self, role: Role, content: str) -> None:
        self._messages.append({'role': role, 'content': content})
        self._trim()

    def reset(self) -> None:
        self._messages.clear()

    def build_payload(self, system_prompt: str | None) -> list[ChatMessage]:
        messages: list[ChatMessage] = []

        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        messages.extend(self._messages)
        return messages

    def _trim(self) -> None:
        self._trim_by_message_count()
        self._trim_by_char_count()

    def _trim_by_message_count(self) -> None:
        if self._limit_messages is None:
            return

        while len(self._messages) > self._limit_messages:
            self._messages.pop(0)

    def _trim_by_char_count(self) -> None:
        if self._limit_chars is None:
            return

        while len(self._messages) > 1 and self._total_chars() > self._limit_chars:
            self._messages.pop(0)

        if self._messages and self._total_chars() > self._limit_chars:
            last_message = self._messages[-1]
            last_message['content'] = last_message['content'][-self._limit_chars :]

    def _total_chars(self) -> int:
        return sum(len(message['content']) for message in self._messages)
