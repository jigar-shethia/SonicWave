import Foundation

public struct DecodedMessage: Identifiable, Equatable {
    public let id: UUID
    public let text: String
    public let rawBytes: [UInt8]
    public let timestamp: Date
    public let snrDB: Float
    public let isCRCValid: Bool
    
    public init(
        id: UUID = UUID(),
        text: String,
        rawBytes: [UInt8],
        timestamp: Date = Date(),
        snrDB: Float,
        isCRCValid: Bool = true
    ) {
        self.id = id
        self.text = text
        self.rawBytes = rawBytes
        self.timestamp = timestamp
        self.snrDB = snrDB
        self.isCRCValid = isCRCValid
    }
    
    public var formattedTime: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        return formatter.string(from: timestamp)
    }
}
