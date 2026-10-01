# AirGuard

<img src="https://flagcdn.com/20x15/ru.png" alt="RU"> Утилита пассивного аудита защищённости Wi-Fi сетей для macOS.
<img src="https://flagcdn.com/20x15/gb.png" alt="EN"> Passive Wi-Fi security audit tool for macOS.

Сканирует сети вокруг, оценивает защищённость (шифрование, заводские имена,
скрытые сети) и формирует отчёт — в терминале и в HTML. / Scans nearby
networks, assesses their security and generates a terminal + HTML report.

> Только пассивно, без атак. / Passive only, no attacks.

## Установка / Install

```bash
git clone https://github.com/Lottersss/airguard.git
cd airguard
./install.sh
```

## Запуск / Usage

```bash
source .venv/bin/activate
airguard --scan --report report.html
```

MIT · [docs/architecture.md](docs/architecture.md)
