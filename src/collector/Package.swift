// swift-tools-version:5.9
// Манифест SwiftPM. Нужен в основном для подсказок редактора/IDE.
// Боевая сборка в install.sh идёт напрямую через swiftc, чтобы
// упаковать бинарник в .app-бандл с Info.plist (так требует macOS для
// доступа к геолокации).

import PackageDescription

let package = Package(
    name: "AirGuardScanner",
    platforms: [.macOS(.v12)],
    targets: [
        .executableTarget(
            name: "AirGuardScanner",
            path: "Sources"
        )
    ]
)
