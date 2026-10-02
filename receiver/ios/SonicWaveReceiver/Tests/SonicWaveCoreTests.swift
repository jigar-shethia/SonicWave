import XCTest
import Accelerate
@testable import SonicWaveCore

final class SonicWaveCoreTests: XCTestCase {
    func testBandpassFilterPeak() {
        let b0: Float = 0.02390558
        let b1: Float = 0.0
        let b2: Float = -0.02390558
        let a1: Float = 1.57935395
        let a2: Float = 0.95218884
        
        let N = 4800
        var tone19k = [Float](repeating: 0.0, count: N)
        var tone1k = [Float](repeating: 0.0, count: N)
        for i in 0..<N {
            let t = Double(i) / 48000.0
            tone19k[i] = Float(cos(2.0 * Double.pi * 19200.0 * t))
            tone1k[i] = Float(cos(2.0 * Double.pi * 1000.0 * t))
        }
        
        func filterSignal(_ sig: [Float]) -> [Float] {
            var out = [Float](repeating: 0.0, count: sig.count)
            var w1: Float = 0.0
            var w2: Float = 0.0
            for i in 0..<sig.count {
                let x = sig[i]
                let w0 = x - a1 * w1 - a2 * w2
                out[i] = b0 * w0 + b1 * w1 + b2 * w2
                w2 = w1
                w1 = w0
            }
            return out
        }
        
        let out19k = filterSignal(tone19k)
        let out1k = filterSignal(tone1k)
        
        let rms19k = sqrt(out19k.suffix(2000).reduce(0.0) { $0 + $1*$1 } / 2000.0)
        let rms1k = sqrt(out1k.suffix(2000).reduce(0.0) { $0 + $1*$1 } / 2000.0)
        
        XCTAssertGreaterThan(rms19k, 0.5)
        XCTAssertLessThan(rms1k, 0.01)
    }
    
    func testEndToEndDSPPacketDecode() {
        let core = SonicWaveDSPCore()
        
        // 1. Build test frame bits for "HELLO"
        let barker = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]
        let payload = Array("HELLO".utf8)
        let len = payload.count
        let crc = CRC16.compute(data: payload)
        
        var bits = barker
        for i in (0..<8).reversed() { bits.append((len >> i) & 1) }
        for byte in payload {
            for i in (0..<8).reversed() { bits.append((Int(byte) >> i) & 1) }
        }
        for i in (0..<16).reversed() { bits.append((Int(crc) >> i) & 1) }
        
        // 2. Synthesize audio waveform
        let fs = 48000.0
        let chirpLen = 2880
        let gapLen = 960
        let symLen = 960
        
        var audio: [Float] = []
        // Lead-in silence
        audio.append(contentsOf: [Float](repeating: 0.0, count: 4800))
        
        // Chirp (60ms)
        for n in 0..<chirpLen {
            let t = Double(n) / fs
            let phase = 2.0 * Double.pi * (18500.0 * t + ((19900.0 - 18500.0) / (2.0 * 0.060)) * (t * t))
            var sample = Float(cos(phase))
            let taperLen = Int(fs * 0.005)
            if n < taperLen {
                let w = 0.5 * (1.0 - cos(Double.pi * Double(n) / Double(taperLen)))
                sample *= Float(w)
            } else if n > chirpLen - taperLen {
                let w = 0.5 * (1.0 - cos(Double.pi * Double(chirpLen - n) / Double(taperLen)))
                sample *= Float(w)
            }
            audio.append(sample)
        }
        
        // Gap
        audio.append(contentsOf: [Float](repeating: 0.0, count: gapLen))
        
        // FSK symbols
        var phase: Double = 0.0
        for bit in bits {
            let freq = bit == 1 ? 19600.0 : 18800.0
            let phaseStep = 2.0 * Double.pi * freq / fs
            for _ in 0..<symLen {
                audio.append(Float(cos(phase)))
                phase += phaseStep
            }
        }
        
        // Trailing silence
        audio.append(contentsOf: [Float](repeating: 0.0, count: 9600))
        
        // 3. Process through DSP core in chunks of 2048 samples (simulating mic input)
        var decodedResult: String?
        core.onMessageDecoded = { msg in
            decodedResult = msg.text
        }
        
        let chunkSize = 2048
        var offset = 0
        while offset < audio.count {
            let end = min(offset + chunkSize, audio.count)
            let chunk = Array(audio[offset..<end])
            core.processAudioBuffer(chunk)
            offset += chunkSize
        }
        
        print(">>> End-to-end DSP test decoded result: \(decodedResult ?? "NIL")")
        XCTAssertEqual(decodedResult, "HELLO", "Should successfully decode HELLO")
    }
}
