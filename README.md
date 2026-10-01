# AirGuard

[<img src="https://flagcdn.com/20x15/ru.png" alt="RU"> Русский](#-русский) &nbsp;·&nbsp; [<img src="https://flagcdn.com/20x15/gb.png" alt="EN"> English](#-english)

---

<a id="-русский"></a>
## <img src="https://flagcdn.com/24x18/ru.png" alt="RU"> Русский

Утилита пассивного аудита защищённости Wi-Fi сетей для macOS.

AirGuard сканирует беспроводные сети вокруг, оценивает защищённость каждой
(тип шифрования, заводские имена, скрытые сети) и формирует отчёт с
рекомендациями — в терминале и в виде HTML. Дополнительно умеет проверять
**свою** сеть на открытые порты.

> Инструмент работает только пассивно: он не подключается к сетям, не
> перехватывает трафик и не подбирает пароли. Предназначен для аудита
> собственной и доверенной инфраструктуры.

### Возможности

- Сбор сетей через нативный фреймворк **CoreWLAN** (Swift).
- Двухуровневый сбор данных: нативный коллектор (CoreWLAN) с автоматическим
  переходом на `system_profiler`, если бинарник не собран.
- Оценка риска по управляемым правилам (YAML): Open / WEP / WPA / WPA2 / WPA3,
  заводские SSID, скрытые сети, слабый сигнал.
- Отчёт в терминале (цветная таблица) и в HTML.
- Режим `--deep`: сканирование своей подсети на открытые порты (nmap).
- Маскирование MAC-адресов в отчётах.

### Требования

- macOS 12+ (протестировано на macOS 26 / Apple Silicon)
- Xcode Command Line Tools: `xcode-select --install`
- Python 3.10+
- (опционально) nmap для режима `--deep`: `brew install nmap`

### Установка

```bash
git clone https://github.com/Lottersss/airguard.git
cd airguard
./install.sh
```

`install.sh` соберёт Swift-коллектор в `.app`-бандл, подпишет его и установит
зависимости Python в `.venv`. Если собрать Swift не удастся, утилита всё равно
работает в запасном режиме.

### Использование

```bash
source .venv/bin/activate

airguard --scan                        # аудит эфира
airguard --scan --report report.html   # + HTML-отчёт
airguard --scan --deep                 # + аудит своей сети (nmap)
```

При первом запуске macOS попросит доступ к геолокации — его нужно разрешить,
иначе система скрывает имена сетей и MAC-адреса.

### Структура проекта

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

### Тесты

```bash
source .venv/bin/activate
python -m pytest
```

### Правовые аспекты

Пассивный приём открыто вещаемых данных о сетях законен. Активные действия не
выполняются. Режим `--deep` ограничен собственной подсетью. Все данные
обрабатываются локально и не передаются третьим лицам.

### Лицензия

MIT — см. [LICENSE](LICENSE).

---

<a id="-english"></a>
## <img src="https://flagcdn.com/24x18/gb.png" alt="EN"> English

Passive Wi-Fi security audit tool for macOS.

AirGuard scans nearby wireless networks, assesses the security of each one
(encryption type, factory-default names, hidden networks) and produces a
report with recommendations — in the terminal and as HTML. It can also check
**your own** network for open ports.

> The tool is strictly passive: it does not connect to networks, intercept
> traffic, or crack passwords. It is intended for auditing your own and
> trusted infrastructure.

### Features

- Network discovery via the native **CoreWLAN** framework (Swift).
- Two-level data collection: native collector (CoreWLAN) with automatic
  fallback to `system_profiler` when the native binary is not built.
- Risk assessment driven by rules (YAML): Open / WEP / WPA / WPA2 / WPA3,
  factory-default SSIDs, hidden networks, weak signal.
- Report in the terminal (colored table) and as HTML.
- `--deep` mode: scans your own subnet for open ports (nmap).
- BSSID masking in reports.

### Requirements

- macOS 12+ (tested on macOS 26 / Apple Silicon)
- Xcode Command Line Tools: `xcode-select --install`
- Python 3.10+
- (optional) nmap for `--deep` mode: `brew install nmap`

### Installation

```bash
git clone https://github.com/Lottersss/airguard.git
cd airguard
./install.sh
```

`install.sh` builds the Swift collector into an `.app` bundle, signs it, and
installs the Python dependencies into `.venv`. If Swift cannot be built, the
tool still works in fallback mode.

### Usage

```bash
source .venv/bin/activate

airguard --scan                        # audit the airwaves
airguard --scan --report report.html   # + HTML report
airguard --scan --deep                 # + audit your own network (nmap)
```

On first run macOS asks for Location access — it must be granted, otherwise
the system hides network names and MAC addresses.

### Project structure

```
airguard/
├── src/
│   ├── collector/   Swift: data collection (CoreWLAN + CoreLocation)
│   └── airguard/    Python core (cli, collector, risk, scanner, report)
├── rules/           risk assessment criteria (YAML)
├── templates/       HTML report template
├── tests/           unit tests
├── docs/            documentation and architecture
└── install.sh       build and install
```

See [docs/architecture.md](docs/architecture.md) for details.

### Tests

```bash
source .venv/bin/activate
python -m pytest
```

### Legal

Passive reception of openly broadcast network data is lawful. No active
actions are performed. The `--deep` mode is limited to your own subnet. All
data is processed locally and never sent to third parties.

### License

MIT — see [LICENSE](LICENSE).
