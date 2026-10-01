# AirGuard

🇬🇧 **English**  ·  [🇷🇺 Русский](README.ru.md)

Passive Wi-Fi security audit tool for macOS.

AirGuard scans nearby wireless networks, assesses the security of each one
(encryption type, factory-default names, hidden networks) and produces a
report with recommendations — in the terminal and as HTML. It can also check
**your own** network for open ports.

> The tool is strictly passive: it does not connect to networks, intercept
> traffic, or crack passwords. It is intended for auditing your own and
> trusted infrastructure.

## Features

- Network discovery via the native **CoreWLAN** framework (Swift).
- Two-level data collection: native collector (CoreWLAN) with automatic
  fallback to `system_profiler` when the native binary is not built.
- Risk assessment driven by rules (YAML): Open / WEP / WPA / WPA2 / WPA3,
  factory-default SSIDs, hidden networks, weak signal.
- Report in the terminal (colored table) and as HTML.
- `--deep` mode: scans your own subnet for open ports (nmap).
- BSSID masking in reports.

## Requirements

- macOS 12+ (tested on macOS 26 / Apple Silicon)
- Xcode Command Line Tools: `xcode-select --install`
- Python 3.10+
- (optional) nmap for `--deep` mode: `brew install nmap`

## Installation

```bash
git clone https://github.com/Lottersss/airguard.git
cd airguard
./install.sh
```

`install.sh` builds the Swift collector into an `.app` bundle, signs it, and
installs the Python dependencies into `.venv`. If Swift cannot be built, the
tool still works in fallback mode.

## Usage

```bash
source .venv/bin/activate

airguard --scan                        # audit the airwaves
airguard --scan --report report.html   # + HTML report
airguard --scan --deep                 # + audit your own network (nmap)
```

On first run macOS asks for Location access — it must be granted, otherwise
the system hides network names and MAC addresses.

## Project structure

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

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

## Legal

Passive reception of openly broadcast network data is lawful. No active
actions are performed. The `--deep` mode is limited to your own subnet. All
data is processed locally and never sent to third parties.

## License

MIT — see [LICENSE](LICENSE).
