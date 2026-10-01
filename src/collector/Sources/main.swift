import Foundation
import CoreWLAN

// AirGuard — модуль сбора данных о Wi-Fi сетях (collector).
//
// Точка входа. Задача модуля — пассивно просканировать эфир средствами
// фреймворка CoreWLAN и напечатать список найденных точек доступа в
// формате JSON (его затем читает Python-ядро).
//
// Особенность macOS 26 (Tahoe): CoreWLAN возвращает реальные имена сетей
// (SSID) и MAC-адреса точек (BSSID) только процессу, который
// зарегистрирован в системе как активный потребитель геолокации
// (Location Services). Если этого не сделать, скан не падает с ошибкой, а
// возвращает нужное число сетей, но с пустыми идентификаторами. Поэтому
// перед сканированием мы «прогреваем» разрешение геолокации (см. LocationGate).

// 1. Получаем и регистрируем доступ к геолокации (блокирующий вызов).
let gate = LocationGate()
gate.ensureAuthorized()

// 2. Сканируем эфир и выводим результат.
let scanner = WiFiScanner()
do {
    let networks = try scanner.scan()
    let json = try JSONOutput.encode(networks)
    print(json)
} catch {
    FileHandle.standardError.write(
        "Ошибка сканирования: \(error.localizedDescription)\n".data(using: .utf8)!
    )
    exit(1)
}
