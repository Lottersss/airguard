"""Формирование отчёта: цветная таблица в терминале и HTML-файл."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console
from rich.table import Table

from airguard.risk import Assessment, LEVEL_ORDER, summary
from airguard.scanner import Host


# Цвета уровней риска для терминала.
LEVEL_STYLE = {
    "CRITICAL": "bold white on red",
    "HIGH": "bold red",
    "MEDIUM": "yellow",
    "LOW": "green",
}


def _mask_bssid(bssid: str | None) -> str:
    """Маскирует MAC точки в выводе (приватность): AA:BB:CC:**:**:**."""
    if not bssid:
        return "—"
    parts = bssid.split(":")
    if len(parts) == 6:
        return ":".join(parts[:3] + ["**", "**", "**"])
    return bssid


def print_terminal(assessments: list[Assessment]) -> None:
    """Печатает таблицу результатов в терминал."""
    console = Console()
    table = Table(
        title="AirGuard · аудит Wi-Fi сетей",
        show_lines=False,
        border_style="#a855f7",   # фиолетовая рамка
        title_style="bold #a855f7",
    )
    table.add_column("SSID", overflow="fold")
    table.add_column("BSSID")
    table.add_column("Шифрование")
    table.add_column("Сигнал", justify="right")
    table.add_column("Канал", justify="right")
    table.add_column("Риск")

    for a in assessments:
        n = a.network
        style = LEVEL_STYLE.get(a.level, "")
        table.add_row(
            n.display_ssid,
            _mask_bssid(n.bssid),
            n.security,
            f"{n.rssi} dBm",
            str(n.channel),
            f"[{style}]{a.level}[/{style}]" if style else a.level,
        )

    console.print(table)

    counts = summary(assessments)
    parts = [f"Найдено сетей: {counts['total']}"]
    for level in LEVEL_ORDER:
        if counts.get(level):
            parts.append(f"{level}: {counts[level]}")
    console.print("  ".join(parts), style="bold")


def render_html(
    assessments: list[Assessment],
    templates_dir: Path,
    output_path: Path,
    hosts: list[Host] | None = None,
) -> Path:
    """Генерирует HTML-отчёт по шаблону."""
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")

    rows = [
        {
            "ssid": a.network.display_ssid,
            "bssid": _mask_bssid(a.network.bssid),
            "security": a.network.security,
            "rssi": a.network.rssi,
            "channel": a.network.channel,
            "band": a.network.band,
            "level": a.level,
            "reasons": a.reasons,
            "recommendations": a.recommendations,
        }
        for a in assessments
    ]

    html = template.render(
        generated=datetime.now().strftime("%d.%m.%Y %H:%M"),
        rows=rows,
        counts=summary(assessments),
        levels=LEVEL_ORDER,
        hosts=hosts or [],
    )
    output_path.write_text(html, encoding="utf-8")
    return output_path
