from pathlib import Path

import pytest

from gigavibemiptcode.chunking import (
    ChunkError,
    load_chunks,
    parse_file_chunk_command,
    split_by_length,
    split_by_paragraphs,
)


def test_parse_command() -> None:
    options = parse_file_chunk_command('/file_chunk paragraph=3 -y')

    assert options.paragraph_count == 3
    assert options.length is None
    assert options.auto_yes is True


def test_parse_conflicting_options() -> None:
    with pytest.raises(ChunkError):
        parse_file_chunk_command('/file_chunk paragraph=2 len=100')


def test_split_by_length() -> None:
    assert split_by_length('abcdef', 2) == ['ab', 'cd', 'ef']


def test_split_by_paragraphs() -> None:
    assert split_by_paragraphs('a\n\nb\n\nc', 2) == ['a\n\nb', 'c']


def test_load_chunks(tmp_path: Path) -> None:
    path = tmp_path / 'text.txt'
    path.write_text('one\n\ntwo\n\nthree', encoding='utf-8')
    options = parse_file_chunk_command('/file_chunk paragraph=2')

    assert load_chunks(str(path), options) == ['one\n\ntwo', 'three']
