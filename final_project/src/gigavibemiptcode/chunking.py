from dataclasses import dataclass
from pathlib import Path


class ChunkError(Exception):
    """Called when chunk is bad"""


@dataclass(frozen=True, slots=True)
class ChunkOptions:
    paragraph_count: int | None = None

    length: int | None = None

    auto_yes: bool = False


def parse_file_chunk_command(command: str) -> ChunkOptions:
    parts = command.split()

    paragraph_count: int | None = None

    length: int | None = None

    auto_yes = False

    for part in parts[1:]:
        if part == '-y':
            auto_yes = True

        elif part.startswith('paragraph='):
            paragraph_count = _parse_positive_int(part, 'paragraph')

        elif part.startswith('len='):
            length = _parse_positive_int(part, 'len')

        else:
            raise ChunkError(f'Unknown /file_chunk option: {part}')

    if paragraph_count is not None and length is not None:
        raise ChunkError('Use either paragraph=N or len=N, not both')

    return ChunkOptions(
        paragraph_count=paragraph_count, length=length, auto_yes=auto_yes
    )


def load_chunks(path: str, options: ChunkOptions) -> list[str]:
    text = _read_text(Path(path).expanduser())

    if options.length is not None:
        return split_by_length(text, options.length)

    return split_by_paragraphs(text, options.paragraph_count or 1)


def split_by_length(text: str, length: int) -> list[str]:
    if length <= 0:
        raise ChunkError('Len must be positive!')

    return [text[index : index + length] for index in range(0, len(text), length)]


def split_by_paragraphs(text: str, paragraph_count: int) -> list[str]:
    if paragraph_count <= 0:
        raise ChunkError('Paragraph count must be positive!')

    paragraphs = [part.strip() for part in text.splitlines() if part.strip()]

    return [
        '\n\n'.join(paragraphs[index : index + paragraph_count])
        for index in range(0, len(paragraphs), paragraph_count)
    ]


def _parse_positive_int(part: str, option_name: str) -> int:
    _, raw_value = part.split('=', maxsplit=1)
    try:
        value = int(raw_value)

    except ValueError as exc:
        raise ChunkError(f'{option_name} must be an integer') from exc

    if value <= 0:
        raise ChunkError(f'{option_name} must be positive')

    return value


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ChunkError(f'File not found: {path}')

    if not path.is_file():
        raise ChunkError(f'Not a regular file: {path}')

    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        raise ChunkError(f'File is not valid UTF-8: {path}') from exc
    except OSError as exc:
        raise ChunkError(f'Cannot read file: {path}') from exc
