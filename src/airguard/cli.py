"""Интерфейс командной строки AirGuard.

Примеры:
    airguard --scan                 обычный аудит эфира
    airguard --scan --report report.html   + сохранить HTML-отчёт
    airguard --scan --deep          + сканировать свою сеть на открытые порты
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from airguard import __version__
from airguard.collector import collect, CollectorError
from airguard.report import print_terminal, render_html
from airguard.risk import assess_all, load_rules
from airguard.scanner import (
    ScannerError,
    local_subnet,
    nmap_available,
    scan_subnet,
)


def project_root() -> Path:
    """Корень проекта (на два уровня выше этого файла: src/airguard/cli.py)."""
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="airguard",
        description="Пассивный аудит защищённости Wi-Fi сетей для macOS.",
    )
    p.add_argument("--scan", action="store_true", help="просканировать эфир и оценить сети")
    p.add_argument("--deep", action="store_true",
                   help="дополнительно просканировать СВОЮ сеть на открытые порты (нужен nmap)")
    p.add_argument("--report", metavar="FILE", help="сохранить HTML-отчёт в указанный файл")
    p.add_argument("--version", action="version", version=f"AirGuard {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = project_root()

    if not args.scan:
        build_parser().print_help()
        return 0

    # 1. Сбор сетей (нативный коллектор или запасной system_profiler).
    try:
        networks, source = collect(root)
    except CollectorError as exc:
        print(f"[ошибка] {exc}", file=sys.stderr)
        return 1

    print(f"Источник данных: {source}")

    if not networks:
        print("Сети не найдены. Проверь, что Wi-Fi включён и дан доступ к геолокации.")
        return 0

    # Подсказка, если система скрыла имена сетей.
    if any(n.ssid in (None, "<redacted>") for n in networks):
        print("Примечание: имена сетей скрыты системой (нет доступа к геолокации "
              "или используется запасной режим). Оценка риска опирается на тип шифрования.\n")

    # 2. Оценка риска.
    rules = load_rules(root / "rules" / "risk_rules.yaml")
    assessments = assess_all(networks, rules)

    # 3. Вывод в терминал.
    print_terminal(assessments)

    # 4. Опционально — углублённый аудит своей сети.
    hosts = []
    if args.deep:
        if not nmap_available():
            print("\n[--deep пропущен] nmap не установлен: brew install nmap", file=sys.stderr)
        else:
            subnet = local_subnet()
            if not subnet:
                print("\n[--deep пропущен] не удалось определить свою подсеть", file=sys.stderr)
            else:
                print(f"\nСканирую свою сеть {subnet} (это может занять до минуты)...")
                try:
                    hosts = scan_subnet(subnet)
                    print(f"Найдено устройств с открытыми портами: {len(hosts)}")
                except ScannerError as exc:
                    print(f"[--deep ошибка] {exc}", file=sys.stderr)

    # 5. Опционально — HTML-отчёт.
    if args.report:
        out = render_html(
            assessments,
            templates_dir=root / "templates",
            output_path=Path(args.report),
            hosts=hosts,
        )
        print(f"\nHTML-отчёт сохранён: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
