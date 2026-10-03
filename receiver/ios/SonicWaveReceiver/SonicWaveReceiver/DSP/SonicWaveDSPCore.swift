import Foundation
import Accelerate

public final class SonicWaveDSPCore {
    // Configuration constants
    public var sampleRate: Double = 48000.0
    public let carrierFreq: Double = 19200.0
    public let f0: Double = 18800.0
    public let f1: Double = 19600.0
    public let symbolDurationSec: Double = 0.020 // 20 ms -> 960 samples
    public let chirpDurationSec: Double = 0.060  // 60 ms -> 2880 samples
    public let chirpStartFreq: Double = 18500.0
    public let chirpEndFreq: Double = 19900.0
    public let barkerCode: [Int] = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]
    
    // Configurable sensitivity threshold (default 0.20 for acoustic air channels)
    public var correlationThreshold: Float = 0.20
    
    // Derived sample counts
    private var samplesPerSymbol: Int = 960
    private var chirpLength: Int = 2880
    
    // Precomputed reference chirp and quadrature basis vectors
    private var refChirp: [Float] = []
    private var refChirpEnergy: Float = 0.0
    
    private var cos0: [Float] = []
    private var sin0: [Float] = []
    private var cos1: [Float] = []
    private var sin1: [Float] = []
    
    // Circular sliding buffer for incoming filtered audio (10 seconds capacity)
    private var bufferCapacity: Int
    private var circularBuffer: [Float]
    private var totalSamplesProcessed: Int64 = 0
    private var lastEvaluatedChirpSample: Int64 = -100000
    private var lastDecodedSample: Int64 = -100000
    private var lastHeartbeatTime: Date = Date()
    
    // Second-Order Section Biquad Bandpass Filter (18.5 kHz - 20.0 kHz @ 48 kHz Fs)
    private let b0: Float = 0.02390558
    private let b1: Float = 0.0
    private let b2: Float = -0.02390558
    private let a1: Float = 1.57935395
    private let a2: Float = 0.95218884
    private var biquadState: [Float] = [0, 0]
    
    // Callbacks
    public var onMessageDecoded: ((DecodedMessage) -> Void)?
    public var onLevelUpdate: ((Float) -> Void)?
    public var onLog: ((String) -> Void)?
    
    /// Initializes DSP buffers, generates reference chirp and quadrature basis vectors for 48 kHz.
    public init() {
        self.samplesPerSymbol = Int(sampleRate * symbolDurationSec) // 960
        self.chirpLength = Int(sampleRate * chirpDurationSec)       // 2880
        self.bufferCapacity = Int(sampleRate * 10.0)                // 480,000 samples (10 sec)
        self.circularBuffer = [Float](repeating: 0.0, count: bufferCapacity)
        
        setupReferenceChirp()
        setupQuadratureTones()
    }
    
    /// Dynamically adapts the DSP engine to hardware sample rate changes (e.g. 44.1k or 48k).
    /// Re-allocates circular buffer and recalculates all reference waveforms.
    public func updateSampleRate(_ newFs: Double) {
        guard newFs > 0 && newFs != sampleRate else { return }
        sampleRate = newFs
        samplesPerSymbol = Int(sampleRate * symbolDurationSec)
        chirpLength = Int(sampleRate * chirpDurationSec)
        bufferCapacity = Int(sampleRate * 10.0)
        circularBuffer = [Float](repeating: 0.0, count: bufferCapacity)
        setupReferenceChirp()
        setupQuadratureTones()
        log("DSP sample rate updated to \(newFs) Hz")
    }
    
    /// Formats and dispatches diagnostic log messages to console and subscriber UI.
    private func log(_ message: String) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        let logMsg = "[\(timestamp)] \(message)"
        print("[SonicWaveDSP] \(logMsg)")
        DispatchQueue.main.async { [weak self] in
            self?.onLog?(logMsg)
        }
    }
    
    /// Precomputes the 60 ms reference linear frequency modulated (LFM) up-chirp (18.5k - 19.9k)
    /// with a 5 ms Hann edge taper and calculates its total reference energy for normalization.
    private func setupReferenceChirp() {
        refChirp = [Float](repeating: 0.0, count: chirpLength)
        let twoPi = 2.0 * Double.pi
        let f0 = chirpStartFreq
        let f1 = chirpEndFreq
        let T = chirpDurationSec
        
        for n in 0..<chirpLength {
            let t = Double(n) / sampleRate
            let phase = twoPi * (f0 * t + ((f1 - f0) / (2.0 * T)) * (t * t))
            var sample = Float(cos(phase))
            
            let taperLen = Int(sampleRate * 0.005)
            if n < taperLen {
                let w = 0.5 * (1.0 - cos(Double.pi * Double(n) / Double(taperLen)))
                sample *= Float(w)
            } else if n > chirpLength - taperLen {
                let w = 0.5 * (1.0 - cos(Double.pi * Double(chirpLength - n) / Double(taperLen)))
                sample *= Float(w)
            }
            refChirp[n] = sample
        }
        
        refChirpEnergy = refChirp.reduce(0.0) { $0 + ($1 * $1) }
    }
    
    /// Precomputes quadrature cosine and sine basis arrays for Tone 0 (18.8 kHz) and Tone 1 (19.6 kHz).
    private func setupQuadratureTones() {
        cos0 = [Float](repeating: 0.0, count: samplesPerSymbol)
        sin0 = [Float](repeating: 0.0, count: samplesPerSymbol)
        cos1 = [Float](repeating: 0.0, count: samplesPerSymbol)
        sin1 = [Float](repeating: 0.0, count: samplesPerSymbol)
        
        let twoPi = 2.0 * Double.pi
        for n in 0..<samplesPerSymbol {
            let t = Double(n) / sampleRate
            cos0[n] = Float(cos(twoPi * f0 * t))
            sin0[n] = Float(sin(twoPi * f0 * t))
            cos1[n] = Float(cos(twoPi * f1 * t))
            sin1[n] = Float(sin(twoPi * f1 * t))
        }
    }
    
    // MARK: - Bandpass Filtering (18.5 kHz - 20.0 kHz)
    /// Direct Form II Transposed Second-Order Section (Biquad) IIR Bandpass Filter.
    /// Isolates the 18.5 kHz - 20.0 kHz ultrasonic channel while attenuating audible room sound.
    private func bandpassFilter(_ input: [Float]) -> [Float] {
        var output = [Float](repeating: 0.0, count: input.count)
        var w1 = biquadState[0]
        var w2 = biquadState[1]
        
        for i in 0..<input.count {
            let x = input[i]
            let w0 = x - a1 * w1 - a2 * w2
            output[i] = b0 * w0 + b1 * w1 + b2 * w2
            w2 = w1
            w1 = w0
        }
        
        biquadState[0] = w1
        biquadState[1] = w2
        return output
    }
    
    // MARK: - Process Incoming Audio Buffer
    /// Ingests a new buffer of raw PCM audio samples from the microphone tap:
    /// 1. Passes input through the 18.5k - 20k Biquad bandpass filter.
    /// 2. Computes root-mean-square (RMS) energy in dBFS using Apple Accelerate `vDSP_rmsqv`.
    /// 3. Updates the 10.0s circular sliding buffer.
    /// 4. Triggers matched-filter chirp search and dynamic packet decoding over recent 9.0s window.
    public func processAudioBuffer(_ rawSamples: [Float]) {
        guard !rawSamples.isEmpty else { return }
        
        let filtered = bandpassFilter(rawSamples)
        let blockCount = filtered.count
        totalSamplesProcessed += Int64(blockCount)
        
        var rms: Float = 0.0
        vDSP_rmsqv(filtered, 1, &rms, vDSP_Length(blockCount))
        let rmsDB = 20.0 * log10(max(rms, 1e-6))
        DispatchQueue.main.async { [weak self] in
            self?.onLevelUpdate?(rmsDB)
        }
        
        if blockCount >= bufferCapacity {
            circularBuffer = Array(filtered.suffix(bufferCapacity))
        } else {
            circularBuffer.removeFirst(blockCount)
            circularBuffer.append(contentsOf: filtered)
        }
        
        // Search in recent 9.0 seconds
        let searchWindowSize = min(circularBuffer.count, Int(sampleRate * 9.0))
        let searchWindow = Array(circularBuffer.suffix(searchWindowSize))
        
        detectAndDecode(in: searchWindow, currentRMSDB: rmsDB)
    }
    
    // MARK: - Matched Filter & Demodulation
    /// Executes cross-correlation against the reference chirp using Apple Accelerate `vDSP_conv`.
    /// Upon finding a peak exceeding `correlationThreshold`:
    /// - Checks 13-bit Barker synchronization code (<= 3 bit errors tolerated).
    /// - Extracts 8-bit packet length header (1..64 bytes).
    /// - Ensures all audio symbols for the full payload + CRC have arrived before demodulation.
    /// - Debounces duplicate triggers within a 1.5s window.
    private func detectAndDecode(in searchWindow: [Float], currentRMSDB: Float) {
        guard searchWindow.count >= chirpLength + (barkerCode.count + 8) * samplesPerSymbol else { return }
        
        let convLen = searchWindow.count - chirpLength + 1
        var correlation = [Float](repeating: 0.0, count: convLen)
        
        vDSP_conv(searchWindow, 1, refChirp, 1, &correlation, 1, vDSP_Length(convLen), vDSP_Length(chirpLength))
        
        var maxCorr: Float = 0.0
        var maxIdx: vDSP_Length = 0
        vDSP_maxvi(correlation, 1, &maxCorr, &maxIdx, vDSP_Length(convLen))
        
        let peakIndex = Int(maxIdx)
        let localEnergy = searchWindow[peakIndex..<(peakIndex + chirpLength)].reduce(0.0) { $0 + ($1 * $1) }
        let denom = sqrt(max(localEnergy * refChirpEnergy, 1e-6))
        let normCorr = maxCorr / denom
        
        if Date().timeIntervalSince(lastHeartbeatTime) >= 2.5 {
            lastHeartbeatTime = Date()
            log("Status: Listening | 19.2k Level: \(String(format: "%.1f", currentRMSDB)) dBFS | Max Correlation: \(String(format: "%.3f", normCorr)) (Threshold: \(String(format: "%.2f", correlationThreshold)))")
        }
        
        if normCorr >= correlationThreshold {
            let chirpGlobalPos = totalSamplesProcessed - Int64(searchWindow.count - peakIndex)
            
            if abs(chirpGlobalPos - lastEvaluatedChirpSample) > Int64(sampleRate * 1.5) {
                let chirpEndIdx = peakIndex + chirpLength
                let gapSamples = Int(sampleRate * 0.02)
                let dataStartIdx = chirpEndIdx + gapSamples
                
                // 1. Need header samples (Barker 13 + Length 8 = 21 symbols)
                let headerBitsCount = barkerCode.count + 8
                let headerSamplesNeeded = dataStartIdx + headerBitsCount * samplesPerSymbol
                guard searchWindow.count >= headerSamplesNeeded else {
                    return // Wait for header to arrive
                }
                
                // 2. Decode header bits to read length
                let (headerBits, _) = demodulateBits(from: searchWindow, startIdx: dataStartIdx, bitCount: headerBitsCount)
                
                let receivedBarker = Array(headerBits.prefix(barkerCode.count))
                var barkerErrors = 0
                for i in 0..<barkerCode.count {
                    if receivedBarker[i] != barkerCode[i] { barkerErrors += 1 }
                }
                guard barkerErrors <= 3 else {
                    return // Not a valid Barker sync code
                }
                
                // Read length
                var payloadLength: Int = 0
                for i in 0..<8 {
                    payloadLength = (payloadLength << 1) | headerBits[barkerCode.count + i]
                }
                guard payloadLength > 0 && payloadLength <= 64 else {
                    return
                }
                
                // 3. Check if the full packet has arrived in searchWindow
                let totalPacketBits = barkerCode.count + 8 + (payloadLength * 8) + 16
                let fullPacketSamplesNeeded = dataStartIdx + totalPacketBits * samplesPerSymbol
                guard searchWindow.count >= fullPacketSamplesNeeded else {
                    return // Wait for remaining packet samples to arrive!
                }
                
                // Full packet is available! Lock and decode
                lastEvaluatedChirpSample = chirpGlobalPos
                log(">>> Sync Locked! NormCorr: \(String(format: "%.3f", normCorr)) (Payload length: \(payloadLength) bytes)")
                
                let (allBits, snrList) = demodulateBits(from: searchWindow, startIdx: dataStartIdx, bitCount: totalPacketBits)
                validateAndDispatch(allBits: allBits, length: payloadLength, snrList: snrList, peakIndex: peakIndex)
            }
        }
    }
    
    /// Demodulates FSK symbols into binary bits using non-coherent quadrature tone energy integration.
    /// Uses Apple Accelerate `vDSP_dotpr` for SIMD vectorized dot products on 80% center slices.
    ///
    /// - Parameters:
    ///   - audio: Filtered audio slice.
    ///   - startIdx: First symbol start sample index.
    ///   - bitCount: Number of sequential symbols to decode.
    /// - Returns: Tuple of decoded bit array and array of per-symbol SNR values (in dB).
    private func demodulateBits(from audio: [Float], startIdx: Int, bitCount: Int) -> ([Int], [Float]) {
        var bits: [Int] = []
        var snrValues: [Float] = []
        var currIdx = startIdx
        
        let pad = Int(Double(samplesPerSymbol) * 0.1)
        let symLen = samplesPerSymbol - 2 * pad
        let c0Slice = Array(cos0[pad..<(samplesPerSymbol - pad)])
        let s0Slice = Array(sin0[pad..<(samplesPerSymbol - pad)])
        let c1Slice = Array(cos1[pad..<(samplesPerSymbol - pad)])
        let s1Slice = Array(sin1[pad..<(samplesPerSymbol - pad)])
        
        for _ in 0..<bitCount {
            guard currIdx + samplesPerSymbol <= audio.count else { break }
            let symSlice = Array(audio[(currIdx + pad)..<(currIdx + samplesPerSymbol - pad)])
            
            var i0: Float = 0.0, q0: Float = 0.0, i1: Float = 0.0, q1: Float = 0.0
            vDSP_dotpr(symSlice, 1, c0Slice, 1, &i0, vDSP_Length(symLen))
            vDSP_dotpr(symSlice, 1, s0Slice, 1, &q0, vDSP_Length(symLen))
            vDSP_dotpr(symSlice, 1, c1Slice, 1, &i1, vDSP_Length(symLen))
            vDSP_dotpr(symSlice, 1, s1Slice, 1, &q1, vDSP_Length(symLen))
            
            let power0 = i0 * i0 + q0 * q0
            let power1 = i1 * i1 + q1 * q1
            let bit = power1 > power0 ? 1 : 0
            bits.append(bit)
            
            let pSignal = max(power0, power1, 1e-9)
            let pNoise = max(min(power0, power1), 1e-9)
            snrValues.append(10.0 * log10(pSignal / pNoise))
            
            currIdx += samplesPerSymbol
        }
        
        return (bits, snrValues)
    }
    
    /// Reassembles payload bytes, computes and validates CRC-16-CCITT checksum,
    /// debounces redundant packets, instantiates DecodedMessage, and notifies UI on main thread.
    private func validateAndDispatch(allBits: [Int], length: Int, snrList: [Float], peakIndex: Int) {
        let expectedTotalBits = barkerCode.count + 8 + (length * 8) + 16
        guard allBits.count >= expectedTotalBits else { return }
        
        var idx = barkerCode.count + 8
        var payloadBytes: [UInt8] = []
        for _ in 0..<length {
            var byteVal: UInt8 = 0
            for _ in 0..<8 {
                byteVal = (byteVal << 1) | UInt8(allBits[idx])
                idx += 1
            }
            payloadBytes.append(byteVal)
        }
        
        var receivedCRC: UInt16 = 0
        for _ in 0..<16 {
            receivedCRC = (receivedCRC << 1) | UInt16(allBits[idx])
            idx += 1
        }
        
        let computedCRC = CRC16.compute(data: payloadBytes)
        let crcHexReceived = String(format: "0x%04X", receivedCRC)
        let crcHexComputed = String(format: "0x%04X", computedCRC)
        
        if receivedCRC == computedCRC {
            log("★ CRC-16 PASS! (Received: \(crcHexReceived), Computed: \(crcHexComputed))")
            
            let approxSamplePos = totalSamplesProcessed - Int64(bufferCapacity - peakIndex)
            if abs(approxSamplePos - lastDecodedSample) > Int64(sampleRate * 1.0) {
                lastDecodedSample = approxSamplePos
                
                let avgSNR = snrList.isEmpty ? 0.0 : snrList.reduce(0.0, +) / Float(snrList.count)
                let decodedString = String(bytes: payloadBytes, encoding: .utf8) ?? "BINARY (\(payloadBytes.count) bytes)"
                
                log("★ SUCCESS: Decoded payload = \"\(decodedString)\" (SNR: \(String(format: "%.1f", avgSNR)) dB)")
                
                let message = DecodedMessage(
                    text: decodedString,
                    rawBytes: payloadBytes,
                    timestamp: Date(),
                    snrDB: avgSNR,
                    isCRCValid: true
                )
                
                DispatchQueue.main.async { [weak self] in
                    self?.onMessageDecoded?(message)
                }
            }
        } else {
            log("CRC-16 FAIL: Received \(crcHexReceived) != Computed \(crcHexComputed)")
        }
    }
}
