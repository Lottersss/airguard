import Foundation
import CoreLocation
import CoreWLAN

// MARK: - LocationGate
//
// Отвечает за получение разрешения Location Services и, что важнее на
// macOS 26, за регистрацию процесса как активного потребителя геолокации.
// Без этого CoreWLAN скрывает SSID/BSSID.

final class LocationGate: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var settled = false

    /// Блокирует выполнение, пока статус доступа не определится
    /// (или не истечёт таймаут). Прокручивает RunLoop — это принципиально:
    /// Thread.sleep не прокручивает цикл, и обмен с службой locationd
    /// не завершается, из-за чего скан вернул бы пустые данные.
    func ensureAuthorized() {
        manager.delegate = self
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()

        let deadline = Date().addingTimeInterval(12)
        while !settled && Date() < deadline {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.2))
        }
        // Небольшая доп. прокрутка, чтобы locationd успел пометить
        // процесс как зарегистрированного потребителя геолокации.
        RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.6))
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            settled = true
        case .denied, .restricted:
            FileHandle.standardError.write(
                "Предупреждение: доступ к геолокации запрещён — имена сетей и MAC будут скрыты системой.\n"
                    .data(using: .utf8)!
            )
            settled = true
        case .notDetermined:
            break // ждём ответа пользователя в системном окне
        @unknown default:
            settled = true
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        settled = true
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // Ошибка геолокации не должна ломать скан — просто разблокируемся.
        settled = true
    }
}

// MARK: - Модель сети

struct WiFiNetwork {
    let ssid: String?
    let bssid: String?
    let rssi: Int
    let channel: Int
    let band: String
    let security: String
    let securityRank: Int   // 0 (хуже) … 5 (лучше) — для оценки риска
}

// MARK: - WiFiScanner
//
// Тонкая обёртка над CoreWLAN: один пассивный скан эфира и приведение
// полей каждой точки доступа к нашей модели WiFiNetwork.

final class WiFiScanner {

    func scan() throws -> [WiFiNetwork] {
        guard let iface = CWWiFiClient.shared().interface() else {
            throw NSError(domain: "airguard", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "Нет доступного Wi-Fi интерфейса"])
        }

        let networks = try iface.scanForNetworks(withName: nil)

        return networks.map { net in
            let (secName, rank) = WiFiScanner.classifySecurity(net)
            return WiFiNetwork(
                ssid: net.ssid,
                bssid: net.bssid,
                rssi: net.rssiValue,
                channel: net.wlanChannel?.channelNumber ?? 0,
                band: WiFiScanner.band(for: net.wlanChannel),
                security: secName,
                securityRank: rank
            )
        }
    }

    /// Диапазон частот точки доступа.
    static func band(for ch: CWChannel?) -> String {
        guard let ch = ch else { return "—" }
        switch ch.channelBand {
        case .band2GHz: return "2.4 ГГц"
        case .band5GHz: return "5 ГГц"
        case .band6GHz: return "6 ГГц"
        default: return "—"
        }
    }

    /// Определяет тип защиты и присваивает ранг надёжности (0…5).
    /// Проверяем от небезопасного к безопасному; выбираем лучший
    /// поддерживаемый режим (у «переходных» сетей их несколько).
    static func classifySecurity(_ net: CWNetwork) -> (String, Int) {
        if net.supportsSecurity(.none) { return ("Open (нет шифрования)", 0) }
        if net.supportsSecurity(.WEP)  { return ("WEP", 1) }

        if net.supportsSecurity(.wpa3Personal) || net.supportsSecurity(.wpa3Enterprise) {
            return ("WPA3", 5)
        }
        if net.supportsSecurity(.wpa2Personal) || net.supportsSecurity(.wpa2Enterprise) {
            return ("WPA2", 3)
        }
        if net.supportsSecurity(.wpaPersonal)
            || net.supportsSecurity(.wpaPersonalMixed)
            || net.supportsSecurity(.wpaEnterprise) {
            return ("WPA", 2)
        }
        return ("Неизвестно", 0)
    }
}
