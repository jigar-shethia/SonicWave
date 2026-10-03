import Foundation

public struct CRC16 {
    /// Computes 16-bit CRC-CCITT checksum over a byte buffer.
    ///
    /// - Parameters:
    ///   - data: Array of payload bytes to calculate checksum for.
    ///   - poly: CRC polynomial bitmask (default: 0x1021 -> x^16 + x^12 + x^5 + 1).
    ///   - initVal: Initial register value (default: 0xFFFF).
    /// - Returns: 16-bit unsigned integer checksum matching transmitter and Python receiver.
    public static func compute(data: [UInt8], poly: UInt16 = 0x1021, initVal: UInt16 = 0xFFFF) -> UInt16 {
        var crc = initVal
        for byte in data {
            crc ^= (UInt16(byte) << 8)
            for _ in 0..<8 {
                if (crc & 0x8000) != 0 {
                    crc = ((crc << 1) ^ poly) & 0xFFFF
                } else {
                    crc = (crc << 1) & 0xFFFF
                }
            }
        }
        return crc
    }
}
