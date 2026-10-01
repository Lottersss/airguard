"""Углублённый аудит СВОЕЙ сети (режим --deep): поиск устройств и открытых портов.

ВАЖНО: сканируется только та подсеть, к которой подключён сам компьютер.
Сканирование чужих сетей без разрешения незаконно. Поэтому подсеть
определяется автоматически по текущему подключению, а не задаётся вручную.

Требует установленного nmap (brew install nmap).
"""

from __future__ import annotations

import ipaddress
import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass
class Host:
    ip: str
    open_ports: list[int] = field(default_factory=list)
    services: dict[int, str] = field(default_factory=dict)


class ScannerError(RuntimeError):
    pass


def nmap_available() -> bool:
    return shutil.which("nmap") is not None


def local_subnet() -> str | None:
    """Определяет подсеть текущего подключения в формате CIDR (например 192.168.1.0/24)."""
    try:
        # IP активного интерфейса.
        route = subprocess.run(
            ["route", "-n", "get", "default"],
            capture_output=True, text=True, timeout=5,
        )
        iface = None
        for line in route.stdout.splitlines():
            if "interface:" in line:
                iface = line.split(":")[1].strip()
        if not iface:
            return None

        ipcfg = subprocess.run(
            ["ipconfig", "getifaddr", iface],
            capture_output=True, text=True, timeout=5,
        )
        ip = ipcfg.stdout.strip()
        if not ip:
            return None

        # Предполагаем маску /24 — типичную для домашних сетей.
        network = ipaddress.ip_network(f"{ip}/24", strict=False)
        return str(network)
    except Exception:
        return None


def scan_subnet(cidr: str, timeout: int = 180) -> list[Host]:
    """Сканирует устройства в подсети и их открытые порты через nmap."""
    if not nmap_available():
        raise ScannerError("nmap не установлен. Установи: brew install nmap")

    # -T4 быстрее, --top-ports 100 — только популярные порты (хватает для аудита).
    cmd = ["nmap", "-T4", "--top-ports", "100", "-oG", "-", cidr]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ScannerError("nmap не завершился за отведённое время") from exc

    return _parse_grepable(proc.stdout)


def _parse_grepable(output: str) -> list[Host]:
    """Разбирает -oG (greppable) вывод nmap."""
    hosts: list[Host] = []
    for line in output.splitlines():
        if not line.startswith("Host:") or "Ports:" not in line:
            continue
        ip = line.split()[1]
        host = Host(ip=ip)
        ports_part = line.split("Ports:")[1]
        for chunk in ports_part.split(","):
            fields = chunk.strip().split("/")
            if len(fields) >= 5 and fields[1] == "open":
                port = int(fields[0])
                service = fields[4] or "?"
                host.open_ports.append(port)
                host.services[port] = service
        if host.open_ports:
            hosts.append(host)
    return hosts
