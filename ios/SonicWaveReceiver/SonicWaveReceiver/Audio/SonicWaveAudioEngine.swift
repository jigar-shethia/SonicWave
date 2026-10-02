import Foundation
import AVFoundation
import Combine
import UIKit

public enum AudioEngineStatus: String {
    case idle = "IDLE"
    case listening = "LISTENING..."
    case error = "ERROR"
}

public final class SonicWaveAudioEngine: ObservableObject {
    @Published public var status: AudioEngineStatus = .idle
    @Published public var isListening: Bool = false
    @Published public var ultrasonicLevelDB: Float = -60.0
    @Published public var latestMessage: DecodedMessage?
    @Published public var messageHistory: [DecodedMessage] = []
    @Published public var errorMessage: String?
    @Published public var logs: [String] = []
    @Published public var correlationThreshold: Float = 0.20 {
        didSet {
            dspCore.correlationThreshold = correlationThreshold
            addLog("Sensitivity threshold set to \(String(format: "%.2f", correlationThreshold))")
        }
    }
    
    private let audioEngine = AVAudioEngine()
    private let dspCore = SonicWaveDSPCore()
    private var isEngineRunning = false
    
    public init() {
        setupDSPCallbacks()
        addLog("SonicWaveAudioEngine initialized.")
    }
    
    public func addLog(_ message: String) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        let formatted = "[\(timestamp)] \(message)"
        print("[SonicWaveAudioEngine] \(formatted)")
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.logs.append(formatted)
            if self.logs.count > 150 {
                self.logs.removeFirst(self.logs.count - 150)
            }
        }
    }
    
    private func setupDSPCallbacks() {
        dspCore.onLevelUpdate = { [weak self] levelDB in
            self?.ultrasonicLevelDB = levelDB
        }
        
        dspCore.onMessageDecoded = { [weak self] message in
            guard let self = self else { return }
            self.latestMessage = message
            self.messageHistory.insert(message, at: 0)
            self.addLog(">>> UI UPDATED: Received \"\(message.text)\" (SNR: \(String(format: "%.1f", message.snrDB)) dB)")
        }
        
        dspCore.onLog = { [weak self] logStr in
            self?.addLog(logStr)
        }
    }
    
    // MARK: - Permissions & Start/Stop Controls
    public func toggleListening() {
        if isListening {
            stopListening()
        } else {
            requestPermissionAndStart()
        }
    }
    
    private func requestPermissionAndStart() {
        let session = AVAudioSession.sharedInstance()
        addLog("Checking microphone record permission (Current: \(session.recordPermission.rawValue))...")
        
        switch session.recordPermission {
        case .granted:
            startAudioStream()
        case .denied:
            let err = "Microphone access is denied. Please enable it in iPhone Settings > SonicWave."
            self.errorMessage = err
            self.addLog("ERROR: \(err)")
            self.status = .error
        case .undetermined:
            session.requestRecordPermission { [weak self] granted in
                DispatchQueue.main.async {
                    if granted {
                        self?.addLog("Microphone permission granted by user.")
                        self?.startAudioStream()
                    } else {
                        let err = "Microphone access was denied by user."
                        self?.errorMessage = err
                        self?.addLog("ERROR: \(err)")
                        self?.status = .error
                    }
                }
            }
        @unknown default:
            break
        }
    }
    
    public func startAudioStream() {
        guard !isEngineRunning else { return }
        
        do {
            let session = AVAudioSession.sharedInstance()
            addLog("Configuring AVAudioSession (.measurement mode, 48 kHz)...")
            
            try session.setCategory(
                .playAndRecord,
                mode: .measurement,
                options: [.defaultToSpeaker, .allowBluetooth]
            )
            try session.setPreferredSampleRate(48000.0)
            try session.setPreferredIOBufferDuration(0.02)
            try session.setActive(true, options: .notifyOthersOnDeactivation)
            
            let actualFs = session.sampleRate
            let inputPort = session.currentRoute.inputs.first?.portName ?? "Unknown"
            addLog("AVAudioSession active. Actual Fs: \(actualFs) Hz | Input Port: \(inputPort)")
            
            // Sync DSP core with actual sample rate
            dspCore.updateSampleRate(actualFs)
            
            let inputNode = audioEngine.inputNode
            let inputFormat = inputNode.inputFormat(forBus: 0)
            addLog("Input Node Format: \(inputFormat.sampleRate) Hz, \(inputFormat.channelCount) ch")
            
            inputNode.removeTap(onBus: 0)
            
            inputNode.installTap(onBus: 0, bufferSize: 2048, format: inputFormat) { [weak self] buffer, _ in
                guard let self = self,
                      let channelData = buffer.floatChannelData?[0] else { return }
                
                let frameCount = Int(buffer.frameLength)
                let samples = Array(UnsafeBufferPointer(start: channelData, count: frameCount))
                
                self.dspCore.processAudioBuffer(samples)
            }
            
            audioEngine.prepare()
            try audioEngine.start()
            
            isEngineRunning = true
            isListening = true
            status = .listening
            errorMessage = nil
            addLog("Audio Engine started successfully! Listening for ultrasonic bursts...")
            
        } catch {
            isEngineRunning = false
            isListening = false
            status = .error
            let errStr = "Failed to start audio engine: \(error.localizedDescription)"
            errorMessage = errStr
            addLog("ERROR: \(errStr)")
        }
    }
    
    public func stopListening() {
        guard isEngineRunning else { return }
        addLog("Stopping audio engine...")
        
        audioEngine.inputNode.removeTap(onBus: 0)
        audioEngine.stop()
        
        do {
            try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        } catch {
            print("Error deactivating session: \(error)")
        }
        
        isEngineRunning = false
        isListening = false
        status = .idle
        ultrasonicLevelDB = -60.0
        addLog("Audio engine stopped. Microphone idle.")
    }
    
    public func copyLogsToClipboard() {
        let allLogs = logs.joined(separator: "\n")
        UIPasteboard.general.string = allLogs
        addLog("Copied \(logs.count) log lines to clipboard.")
    }
    
    public func clearLogs() {
        logs.removeAll()
        addLog("Logs cleared.")
    }
    
    public func clearHistory() {
        messageHistory.removeAll()
        latestMessage = nil
        addLog("Message history cleared.")
    }
}
