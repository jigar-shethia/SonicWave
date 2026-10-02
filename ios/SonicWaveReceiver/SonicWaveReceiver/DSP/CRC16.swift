import Foundation

public struct CRC16 {
    /// Computes CRC-16-CCITT (polynomial 0x1021, init 0xFFFF)
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
