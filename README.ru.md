# AirGuard

[![English](https://img.shields.io/badge/lang-English-6b7280?style=for-the-badge)](README.md)
[![Русский](https://img.shields.io/badge/язык-Русский-2563eb?style=for-the-badge)](README.ru.md)

Утилита пассивного аудита защищённости Wi-Fi сетей для macOS.

AirGuard сканирует беспроводные сети вокруг, оценивает защищённость каждой
(тип шифрования, заводские имена, скрытые сети) и формирует отчёт с
рекомендациями — в терминале и в виде HTML. Дополнительно умеет проверять
**свою** сеть на открытые порты.

> Инструмент работает только пассивно: он не подключается к сетям, не
> перехватывает трафик и не подбирает пароли. Предназначен для аудита
> собственной и доверенной инфраструктуры.

## Возможности

- Сбор сетей через нативный фреймворк **CoreWLAN** (Swift).
- Двухуровневый сбор данных: нативный коллектор (CoreWLAN) с автоматическим
  переходом на `system_profiler`, если бинарник не собран.
- Оценка риска по управляемым правилам (YAML): Open / WEP / WPA / WPA2 / WPA3,
  заводские SSID, скрытые сети, слабый сигнал.
- Отчёт в терминале (цветная таблица) и в HTML.
- Режим `--deep`: сканирование своей подсети на открытые порты (nmap).
- Маскирование MAC-адресов в отчётах.

## Требования

- macOS 12+ (протестировано на macOS 26 / Apple Silicon)
- Xcode Command Line Tools: `xcode-select --install`
- Python 3.10+
- (опционально) nmap для режима `--deep`: `brew install nmap`

## Установка

```bash
git clone https://github.com/Lottersss/airguard.git
cd airguard
./install.sh
```

`install.sh` соберёт Swift-коллектор в `.app`-бандл, подпишет его и установит
зависимости Python в `.venv`. Если собрать Swift не удастся, утилита всё равно
работает в запасном режиме.

## Использование

```bash
source .venv/bin/activate

airguard --scan                        # аудит эфира
airguard --scan --report report.html   # + HTML-отчёт
airguard --scan --deep                 # + аудит своей сети (nmap)
```

При первом запуске macOS попросит доступ к геолокации — его нужно разрешить,
иначе система скрывает имена сетей и MAC-адреса.

## Структура проекта

```
airguard/
├── src/
│   ├── collector/   Swift: сбор данных (CoreWLAN + CoreLocation)
│   └── airguard/    Python-ядро (cli, collector, risk, scanner, report)
├── rules/           критерии оценки риска (YAML)
├── templates/       шаблон HTML-отчёта
├── tests/           модульные тесты
├── docs/            документация и архитектура
└── install.sh       сборка и установка
```

Подробнее — в [docs/architecture.md](docs/architecture.md).

## Тесты

```bash
source .venv/bin/activate
python -m pytest
```

## Правовые аспекты

Пассивный приём открыто вещаемых данных о сетях законен. Активные действия не
выполняются. Режим `--deep` ограничен собственной подсетью. Все данные
обрабатываются локально и не передаются третьим лицам.

## Лицензия

MIT — см. [LICENSE](LICENSE).
