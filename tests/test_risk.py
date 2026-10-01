"""Модульные тесты логики оценки риска.

Запуск из корня проекта:  python -m pytest
"""

import sys
from pathlib import Path

# Добавляем src/ в путь импорта, чтобы тесты видели пакет airguard.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from airguard.collector import Network          # noqa: E402
from airguard.risk import assess, load_rules     # noqa: E402


RULES = load_rules(Path(__file__).resolve().parents[1] / "rules" / "risk_rules.yaml")


def _net(ssid="TestNet", security="WPA2", rank=3, rssi=-50):
    return Network(
        ssid=ssid, bssid="AA:BB:CC:DD:EE:FF", rssi=rssi,
        channel=6, band="2.4 ГГц", security=security, security_rank=rank,
    )


def test_open_network_is_critical():
    a = assess(_net(security="Open (нет шифрования)", rank=0), RULES)
    assert a.level == "КРИТИЧНО"
    assert a.reasons  # есть объяснение


def test_wep_is_critical():
    a = assess(_net(security="WEP", rank=1), RULES)
    assert a.level == "КРИТИЧНО"


def test_wpa3_is_low():
    a = assess(_net(security="WPA3", rank=5), RULES)
    assert a.level == "НИЗКО"


def test_wpa2_is_medium():
    a = assess(_net(security="WPA2", rank=3), RULES)
    assert a.level == "СРЕДНЕ"


def test_default_ssid_escalates_risk():
    # WPA2 (СРЕДНЕ), но заводское имя повышает риск до ВЫСОКО.
    a = assess(_net(ssid="TP-LINK_2F30", security="WPA2", rank=3), RULES)
    assert a.level == "ВЫСОКО"


def test_hidden_ssid_is_noted():
    a = assess(_net(ssid=None, security="WPA2", rank=3), RULES)
    # уровень остаётся СРЕДНЕ, но появляется отдельное замечание
    assert any("крыт" in r.lower() for r in a.reasons)
