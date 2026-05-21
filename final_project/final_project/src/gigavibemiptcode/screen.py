from __future__ import annotations

import os


def clear_screen() -> None:
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)
