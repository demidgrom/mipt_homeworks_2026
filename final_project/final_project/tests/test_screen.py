from __future__ import annotations

import os

from pytest import MonkeyPatch

from gigavibemiptcode import screen


def test_clear_screen_calls_system(monkeypatch: MonkeyPatch) -> None:
    called_commands: list[str] = []

    def fake_system(command: str) -> int:
        called_commands.append(command)
        return 0

    monkeypatch.setattr(os, 'system', fake_system)

    screen.clear_screen()

    assert called_commands
    assert called_commands[0] in {'clear', 'cls'}
