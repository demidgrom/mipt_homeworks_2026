import sys

from gigavibemiptcode.attachments import AttachmentError, expand_attachments
from gigavibemiptcode.chunking import ChunkError, load_chunks, parse_file_chunk_command
from gigavibemiptcode.config import ConfigError, load_config
from gigavibemiptcode.history import MessageHistory
from gigavibemiptcode.llm_client import LlmClient, LlmError, OpenAiCompatibleClient
from gigavibemiptcode.models import ChatMessage
from gigavibemiptcode.screen import clear_screen

QUIT_COMMAND: str = '\\q'
RESET_COMMAND: str = '/reset'
FILE_CHUNK_COMMAND: str = '/file_chunk'
FILECHUNK_COMMAND: str = '/filechunk'


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f'Configuration error: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc

    history = MessageHistory(
        limit_messages=config.limit_messages, limit_chars=config.limit_chars
    )
    client = OpenAiCompatibleClient(config)
    run_chat_loop(client, history, config.system_prompt, stream=config.stream)


def run_chat_loop(
    client: LlmClient,
    history: MessageHistory,
    system_prompt: str | None,
    *,
    stream: bool,
) -> None:
    print('GigaVibeMiptCode. Type \\q to exit, /reset to reset chat history.')

    while True:
        user_input = input('>>> ').strip()

        if user_input == QUIT_COMMAND:
            return

        if user_input == RESET_COMMAND:
            history.reset()
            clear_screen()
            continue

        if user_input.startswith((FILE_CHUNK_COMMAND, FILECHUNK_COMMAND)):
            _run_file_chunk_mode(client, system_prompt, user_input, stream=stream)
            continue

        if not user_input:
            continue

        try:
            expanded = expand_attachments(user_input)
        except AttachmentError as exc:
            print(f'File error: {exc}')
            continue

        history.append('user', expanded)

        messages = history.build_payload(system_prompt)

        answer = _ask_model(client, messages, stream=stream)

        if answer is None:
            continue

        history.append('assistant', answer)


def _ask_model(
    client: LlmClient,
    messages: list[ChatMessage],
    *,
    stream: bool,
) -> str | None:
    try:
        if stream:
            answer_parts: list[str] = []

            for text in client.stream_chat(messages):
                answer_parts.append(text)

                print(text, end='', flush=True)

            print()

            return ''.join(answer_parts)

        answer = client.chat_once(messages)

        print(answer)
        return answer

    except KeyboardInterrupt:
        print('\nRequest interrupted. You can type a new message.')
        return None

    except LlmError as exc:
        print(f'LLM error: {exc}')
        return None


def _run_file_chunk_mode(
    client: LlmClient,
    system_prompt: str | None,
    command: str,
    *,
    stream: bool,
) -> None:
    try:
        options = parse_file_chunk_command(command)
        file_path = input('Enter file path: ').strip()
        user_prompt = input('What should be done for each chunk? ').strip()
        chunks = load_chunks(file_path, options)
    except ChunkError as exc:
        print(f'Chunk error: {exc}')
        return

    print('Accepted. Starting chunk processing.')

    for index, chunk in enumerate(chunks, start=1):
        if index > 1 and not options.auto_yes:
            command = input('Press Enter for next chunk or \\q to stop: ').strip()
            if command == QUIT_COMMAND:
                return

        messages: list[ChatMessage] = []

        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        messages.append(
            {
                'role': 'user',
                'content': f'{user_prompt}\n\n{chunk}',
            }
        )

        print(f'\n--- chunk {index}/{len(chunks)} ---')
        _ask_model(client, messages, stream=stream)

    print('File processing finished.')
