from pathlib import Path

import pytest

from gigavibemiptcode.attachments import AttachmentError, expand_attachments


def test_expand_one_attachment(tmp_path: Path) -> None:
    source = tmp_path / 'main.py'
    source.write_text('print(1 / 0)\n', encoding='utf-8')

    result = expand_attachments(f'Find bug @::{source}::')

    assert 'Find bug' in result
    assert 'print(1 / 0)' in result


def test_missing_attachment_fails() -> None:
    with pytest.raises(AttachmentError):
        expand_attachments('look @::/not/exist.py::')
