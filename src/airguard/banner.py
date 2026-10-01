"""Стартовый баннер утилиты (ASCII-логотип в терминале)."""

from __future__ import annotations

from rich.console import Console

from airguard import __version__

PURPLE = "#a855f7"

LOGO = r"""
 █████╗ ██╗██████╗  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
██╔══██╗██║██╔══██╗██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
███████║██║██████╔╝██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██╔══██║██║██╔══██╗██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
██║  ██║██║██║  ██║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
"""


def print_banner(console: Console | None = None) -> None:
    c = console or Console()
    c.print(LOGO, style=f"bold {PURPLE}")
    c.print(f"  Wi-Fi security audit for macOS · passive, no attacks",
            style=PURPLE)
    c.print(f"  v{__version__}\n", style="dim")
