"""Сбор данных о Wi-Fi сетях.

Поддерживаются два источника (уровня) сбора:

1. Нативный коллектор на Swift/CoreWLAN (`build/AirGuardScanner.app`).
   Даёт полные данные, включая имена сетей (SSID) и MAC точек (BSSID),
   но требует собранного бинарника и выданного доступа к геолокации.

2. Запасной сбор через системную утилиту `system_profiler` (без Swift).
   Работает всегда и без сборки, отдаёт шифрование, канал, диапазон и
   сигнал. Имена сетей и MAC система отдаёт скрытыми (<redacted>), пока
   процесс не получит доступ к геолокации, — поэтому для оценки риска
   используется прежде всего тип шифрования.

Ядро пробует нативный коллектор, а при его отсутствии автоматически
переходит на запасной. Это описано в записке как «двухуровневый сбор данных».
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


BUNDLE_REL = Path("build/AirGuardScanner.app/Contents/MacOS/AirGuardScanner")

REDACTED = "<redacted>"


@dataclass
class Network:
    """Одна точка доступа."""
    ssid: str | None
    bssid: str | None
    rssi: int
    channel: int
    band: str
    security: str
    security_rank: int

    @property
    def display_ssid(self) -> str:
        if not self.ssid:
            return "<скрыт>"
        if self.ssid == REDACTED:
            return "<скрыт системой>"
        return self.ssid


class CollectorError(RuntimeError):
    pass


# --- Источник 1: нативный Swift-коллектор ------------------------------------

def _bundle_path(project_root: Path) -> Path | None:
    path = project_root / BUNDLE_REL
    return path if path.exists() else None


def collect_native(binary: Path, timeout: int = 30) -> list[Network]:
    try:
        proc = subprocess.run([str(binary)], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise CollectorError("Коллектор не ответил за отведённое время") from exc

    if proc.returncode != 0:
        raise CollectorError(f"Коллектор завершился с ошибкой:\n{proc.stderr.strip()}")

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise CollectorError(f"Не удалось разобрать вывод коллектора: {exc}") from exc

    return [
        Network(
            ssid=item.get("ssid"),
            bssid=item.get("bssid"),
            rssi=item.get("rssi", 0),
            channel=item.get("channel", 0),
            band=item.get("band", "—"),
            security=item.get("security", "Неизвестно"),
            security_rank=item.get("security_rank", 0),
        )
        for item in payload.get("networks", [])
    ]


# --- Источник 2: запасной сбор через system_profiler -------------------------

# Соответствие кодов security_mode из system_profiler нашим обозначениям.
_SEC_TABLE = {
    "none": ("Open (нет шифрования)", 0),
    "open": ("Open (нет шифрования)", 0),
    "wep": ("WEP", 1),
    "wpa_personal": ("WPA", 2),
    "wpa_personal_mixed": ("WPA", 2),
    "wpa_wpa2_personal": ("WPA2", 3),
    "wpa2_personal": ("WPA2", 3),
    "wpa2_enterprise": ("WPA2", 3),
    "wpa2_wpa3_personal": ("WPA3", 5),
    "wpa3_personal": ("WPA3", 5),
    "wpa3_enterprise": ("WPA3", 5),
    "wpa3_transition": ("WPA3", 5),
}


def _map_security(raw: str) -> tuple[str, int]:
    code = raw.replace("spairport_security_mode_", "").strip().lower()
    if code in _SEC_TABLE:
        return _SEC_TABLE[code]
    # Запасное определение по подстроке.
    if "wpa3" in code:
        return ("WPA3", 5)
    if "wpa2" in code:
        return ("WPA2", 3)
    if "wpa" in code:
        return ("WPA", 2)
    if "wep" in code:
        return ("WEP", 1)
    if "none" in code or "open" in code:
        return ("Open (нет шифрования)", 0)
    return ("Неизвестно", 0)


def _parse_channel(raw: str) -> tuple[int, str]:
    """'40 (5GHz, 80MHz)' -> (40, '5 ГГц')."""
    m = re.match(r"\s*(\d+)", raw or "")
    channel = int(m.group(1)) if m else 0
    if "6ghz" in (raw or "").lower().replace(" ", ""):
        band = "6 ГГц"
    elif "5ghz" in (raw or "").lower().replace(" ", ""):
        band = "5 ГГц"
    elif "2ghz" in (raw or "").lower().replace(" ", ""):
        band = "2.4 ГГц"
    else:
        band = "—"
    return channel, band


def _parse_rssi(raw: str) -> int:
    """'-80 dBm / -93 dBm' -> -80."""
    m = re.search(r"(-?\d+)", raw or "")
    return int(m.group(1)) if m else 0


def _network_from_sp(entry: dict) -> Network:
    sec_name, rank = _map_security(entry.get("spairport_security_mode", ""))
    channel, band = _parse_channel(entry.get("spairport_network_channel", ""))
    return Network(
        ssid=entry.get("_name"),
        bssid=None,  # system_profiler не отдаёт BSSID
        rssi=_parse_rssi(entry.get("spairport_signal_noise", "")),
        channel=channel,
        band=band,
        security=sec_name,
        security_rank=rank,
    )


def collect_system_profiler(timeout: int = 30) -> list[Network]:
    try:
        proc = subprocess.run(
            ["system_profiler", "-json", "SPAirPortDataType"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise CollectorError("Не удалось выполнить system_profiler") from exc

    try:
        data = json.loads(proc.stdout)
        iface = data["SPAirPortDataType"][0]["spairport_airport_interfaces"][0]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise CollectorError("Не удалось разобрать вывод system_profiler") from exc

    networks: list[Network] = []

    current = iface.get("spairport_current_network_information")
    if isinstance(current, dict):
        networks.append(_network_from_sp(current))

    for entry in iface.get("spairport_airport_other_local_wireless_networks", []):
        networks.append(_network_from_sp(entry))

    return networks


# --- Единая точка входа ------------------------------------------------------

def collect(project_root: Path, prefer_native: bool = True) -> tuple[list[Network], str]:
    """Собирает сети, выбирая доступный источник.

    Возвращает (список сетей, человекочитаемое имя источника).
    """
    if prefer_native:
        binary = _bundle_path(project_root)
        if binary is not None:
            return collect_native(binary), "нативный коллектор (CoreWLAN)"

    return collect_system_profiler(), "system_profiler (запасной режим)"
