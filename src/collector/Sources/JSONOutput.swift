import Foundation

// MARK: - JSONOutput
//
// Сериализует список найденных сетей в JSON. Этот JSON — единственный
// канал связи между Swift-коллектором и Python-ядром, поэтому формат
// фиксированный и простой.

enum JSONOutput {
    static func encode(_ networks: [WiFiNetwork]) throws -> String {
        let objects: [[String: Any]] = networks.map { n in
            [
                "ssid": n.ssid ?? NSNull(),
                "bssid": n.bssid ?? NSNull(),
                "rssi": n.rssi,
                "channel": n.channel,
                "band": n.band,
                "security": n.security,
                "security_rank": n.securityRank,
            ]
        }

        let payload: [String: Any] = [
            "tool": "airguard-collector",
            "count": networks.count,
            "networks": objects,
        ]

        let data = try JSONSerialization.data(
            withJSONObject: payload,
            options: [.prettyPrinted, .sortedKeys]
        )
        return String(data: data, encoding: .utf8) ?? "{}"
    }
}
