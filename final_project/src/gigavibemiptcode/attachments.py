import re
from pathlib import Path

MAX_FILE_BYTES = 5 * 1024 * 1024
_ATTACHMENT_PATTERN = re.compile(r'@::(?P<path>.*?)::')


class AttachmentError(Exception):
    """Raised when an attached file cannot be loaded safely."""


def expand_attachments(text: str, max_bytes: int = MAX_FILE_BYTES) -> str:
    def replace(match: re.Match[str]) -> str:
        raw_path = match.group('path')

        path = Path(raw_path).expanduser()

        return '\n' + read_text_attachment(path, max_bytes=max_bytes)

    return _ATTACHMENT_PATTERN.sub(replace, text)


def read_text_attachment(path: Path, max_bytes: int = MAX_FILE_BYTES) -> str:
    if not path.exists():
        raise AttachmentError(f'File not found: {path}')

    if not path.is_file():
        raise AttachmentError(f'Not a regular file: {path}')

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise AttachmentError(f'Cannot read file metadata: {path}') from exc

    if size > max_bytes:
        raise AttachmentError(f'File is too large: {path} > {max_bytes} bytes')

    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        raise AttachmentError(f'File is not valid UTF-8 text: {path}') from exc
    except OSError as exc:
        raise AttachmentError(f'Cannot read file: {path}') from exc
