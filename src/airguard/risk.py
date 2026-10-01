"""Ядро продукта — оценка риска каждой сети по правилам из rules/risk_rules.yaml.

Логика намеренно вынесена из кода в YAML: критерии можно менять и дополнять,
не трогая Python. Это упрощает расширение и объясняется в пояснительной записке
как «гибкая, управляемая правилами архитектура».
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from airguard.collector import Network


# Порядок уровней от худшего к лучшему — используется для сортировки отчёта.
LEVEL_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


@dataclass
class Assessment:
    """Результат оценки одной сети."""
    network: Network
    level: str
    reasons: list[str]
    recommendations: list[str]

    @property
    def order(self) -> int:
        return LEVEL_ORDER.index(self.level) if self.level in LEVEL_ORDER else len(LEVEL_ORDER)


def load_rules(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def assess(network: Network, rules: dict) -> Assessment:
    """Оценивает одну сеть и возвращает уровень риска с объяснением."""
    reasons: list[str] = []
    recommendations: list[str] = []

    # 1. Базовый уровень по типу шифрования.
    sec_rules = rules.get("security_levels", {})
    sec_rule = sec_rules.get(network.security, sec_rules.get("default", {}))
    level = sec_rule.get("level", "MEDIUM")
    if sec_rule.get("reason"):
        reasons.append(sec_rule["reason"])
    if sec_rule.get("recommendation"):
        recommendations.append(sec_rule["recommendation"])

    # 2. Дополнительные признаки, которые могут повысить уровень риска.
    for check in rules.get("extra_checks", []):
        if _check_matches(network, check):
            reasons.append(check.get("reason", ""))
            if check.get("recommendation"):
                recommendations.append(check["recommendation"])
            level = _escalate(level, check.get("escalate_to"))

    return Assessment(
        network=network,
        level=level,
        reasons=[r for r in reasons if r],
        recommendations=[r for r in recommendations if r],
    )


def _check_matches(network: Network, check: dict) -> bool:
    """Простой движок условий для доп. проверок из YAML."""
    kind = check.get("type")

    if kind == "ssid_contains":
        needles = [s.lower() for s in check.get("values", [])]
        name = (network.ssid or "").lower()
        return any(n in name for n in needles)

    if kind == "hidden_ssid":
        return not network.ssid

    if kind == "weak_signal":
        return network.rssi <= check.get("below_dbm", -75)

    return False


def _escalate(current: str, target: str | None) -> str:
    """Поднимает уровень риска, если целевой строже текущего."""
    if not target or target not in LEVEL_ORDER:
        return current
    if current not in LEVEL_ORDER:
        return target
    return target if LEVEL_ORDER.index(target) < LEVEL_ORDER.index(current) else current


def assess_all(networks: list[Network], rules: dict) -> list[Assessment]:
    results = [assess(n, rules) for n in networks]
    # Сортируем: сначала самые опасные, внутри уровня — по силе сигнала.
    results.sort(key=lambda a: (a.order, a.network.rssi))
    return results


def summary(assessments: list[Assessment]) -> dict[str, int]:
    """Счётчики по уровням риска для сводки."""
    counts = {level: 0 for level in LEVEL_ORDER}
    for a in assessments:
        counts[a.level] = counts.get(a.level, 0) + 1
    counts["total"] = len(assessments)
    return counts
