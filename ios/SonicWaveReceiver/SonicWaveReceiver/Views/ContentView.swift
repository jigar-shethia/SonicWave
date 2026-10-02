import SwiftUI

public struct ContentView: View {
    @StateObject private var audioEngine = SonicWaveAudioEngine()
    @State private var showingCopiedAlert = false
    @State private var showLogs = true
    
    public init() {}
    
    public var body: some View {
        NavigationView {
            ZStack {
                // Background dark gradient
                LinearGradient(
                    gradient: Gradient(colors: [
                        Color(red: 0.04, green: 0.06, blue: 0.10),
                        Color(red: 0.07, green: 0.10, blue: 0.16)
                    ]),
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 16) {
                        // MARK: - Header & Status Indicator
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("SonicWave")
                                    .font(.system(size: 26, weight: .bold, design: .rounded))
                                    .foregroundColor(.white)
                                Text("Ultrasonic Receiver (19.2 kHz)")
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(.gray)
                            }
                            
                            Spacer()
                            
                            // Status Badge Pill
                            HStack(spacing: 6) {
                                Circle()
                                    .fill(audioEngine.isListening ? Color.green : Color.gray)
                                    .frame(width: 8, height: 8)
                                Text(audioEngine.status.rawValue)
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(.white)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(
                                Capsule()
                                    .fill(audioEngine.isListening ? Color.green.opacity(0.2) : Color.gray.opacity(0.2))
                            )
                            .overlay(
                                Capsule()
                                    .stroke(audioEngine.isListening ? Color.green.opacity(0.5) : Color.gray.opacity(0.3), lineWidth: 1)
                            )
                        }
                        .padding(.horizontal)
                        .padding(.top, 6)
                        
                        // MARK: - Ultrasonic Signal Level (VU Meter)
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Label("19.2 kHz Signal Level", systemImage: "waveform.path")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundColor(.gray)
                                Spacer()
                                Text(String(format: "%.1f dBFS", audioEngine.ultrasonicLevelDB))
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundColor(audioEngine.isListening ? .cyan : .gray)
                            }
                            
                            GeometryReader { geo in
                                ZStack(alignment: .leading) {
                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(Color.white.opacity(0.08))
                                        .frame(height: 8)
                                    
                                    let normalized = max(0.0, min(1.0, (Double(audioEngine.ultrasonicLevelDB) + 60.0) / 50.0))
                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(
                                            LinearGradient(
                                                colors: [.blue, .cyan, .green],
                                                startPoint: .leading,
                                                endPoint: .trailing
                                            )
                                        )
                                        .frame(width: geo.size.width * CGFloat(normalized), height: 8)
                                        .animation(.easeOut(duration: 0.1), value: normalized)
                                }
                            }
                            .frame(height: 8)
                        }
                        .padding(.horizontal)
                        
                        // MARK: - Hero Decoded Message Card
                        VStack(spacing: 10) {
                            if let msg = audioEngine.latestMessage {
                                VStack(spacing: 10) {
                                    HStack {
                                        Label("DECODED MESSAGE", systemImage: "sparkles")
                                            .font(.system(size: 11, weight: .bold))
                                            .foregroundColor(.green)
                                        Spacer()
                                        Text(msg.formattedTime)
                                            .font(.system(size: 11, weight: .medium))
                                            .foregroundColor(.gray)
                                    }
                                    
                                    Text(msg.text)
                                        .font(.system(size: 36, weight: .heavy, design: .rounded))
                                        .foregroundColor(.white)
                                        .multilineTextAlignment(.center)
                                        .padding(.vertical, 4)
                                    
                                    HStack(spacing: 14) {
                                        HStack(spacing: 4) {
                                            Image(systemName: "checkmark.seal.fill")
                                                .foregroundColor(.green)
                                            Text("CRC PASS")
                                                .font(.system(size: 11, weight: .semibold))
                                                .foregroundColor(.green)
                                        }
                                        
                                        HStack(spacing: 4) {
                                            Image(systemName: "antenna.radiowaves.left.and.right")
                                                .foregroundColor(.cyan)
                                            Text(String(format: "SNR: %.1f dB", msg.snrDB))
                                                .font(.system(size: 11, weight: .semibold))
                                                .foregroundColor(.cyan)
                                        }
                                    }
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 4)
                                    .background(Capsule().fill(Color.white.opacity(0.06)))
                                }
                                .padding(16)
                                .frame(maxWidth: .infinity)
                                .background(
                                    RoundedRectangle(cornerRadius: 18)
                                        .fill(Color.white.opacity(0.06))
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 18)
                                        .stroke(Color.green.opacity(0.5), lineWidth: 1.5)
                                )
                            } else {
                                VStack(spacing: 8) {
                                    Image(systemName: audioEngine.isListening ? "waveform.badge.magnifyingglass" : "mic.slash")
                                        .font(.system(size: 32))
                                        .foregroundColor(audioEngine.isListening ? .cyan : .gray)
                                    
                                    Text(audioEngine.isListening ? "Listening for Ultrasonic Bursts..." : "Microphone Idle")
                                        .font(.system(size: 15, weight: .semibold))
                                        .foregroundColor(.white)
                                    
                                    Text("Play 'sonicwave_music_hello.wav' on your MacBook near this iPhone.")
                                        .font(.system(size: 12))
                                        .foregroundColor(.gray)
                                        .multilineTextAlignment(.center)
                                }
                                .padding(20)
                                .frame(maxWidth: .infinity)
                                .background(
                                    RoundedRectangle(cornerRadius: 18)
                                        .fill(Color.white.opacity(0.03))
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 18)
                                        .stroke(Color.white.opacity(0.08), lineWidth: 1)
                                )
                            }
                        }
                        .padding(.horizontal)
                        
                        // MARK: - Start / Stop Listening Button
                        Button(action: {
                            let impact = UIImpactFeedbackGenerator(style: .medium)
                            impact.impactOccurred()
                            audioEngine.toggleListening()
                        }) {
                            HStack(spacing: 10) {
                                Image(systemName: audioEngine.isListening ? "stop.fill" : "mic.fill")
                                    .font(.system(size: 18, weight: .bold))
                                Text(audioEngine.isListening ? "Stop Listening" : "Start Listening")
                                    .font(.system(size: 16, weight: .bold, design: .rounded))
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(
                                LinearGradient(
                                    colors: audioEngine.isListening
                                        ? [Color(red: 0.9, green: 0.2, blue: 0.2), Color(red: 0.7, green: 0.1, blue: 0.1)]
                                        : [Color(red: 0.1, green: 0.5, blue: 0.9), Color(red: 0.0, green: 0.7, blue: 0.6)],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                            .shadow(
                                color: audioEngine.isListening ? Color.red.opacity(0.3) : Color.cyan.opacity(0.3),
                                radius: 8,
                                x: 0,
                                y: 3
                            )
                        }
                        .padding(.horizontal)
                        
                        if let err = audioEngine.errorMessage {
                            Text(err)
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(.red)
                                .padding(.horizontal)
                        }
                        
                        // MARK: - Live Diagnostics & Logs
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Label("Live Diagnostic Logs", systemImage: "terminal.fill")
                                    .font(.system(size: 13, weight: .bold))
                                    .foregroundColor(.white)
                                Spacer()
                                
                                // Copy Logs Button
                                Button(action: {
                                    audioEngine.copyLogsToClipboard()
                                    showingCopiedAlert = true
                                    DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                                        showingCopiedAlert = false
                                    }
                                }) {
                                    HStack(spacing: 4) {
                                        Image(systemName: showingCopiedAlert ? "checkmark" : "doc.on.doc")
                                        Text(showingCopiedAlert ? "Copied!" : "Copy Logs")
                                    }
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundColor(showingCopiedAlert ? .green : .cyan)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 5)
                                    .background(Capsule().fill(Color.white.opacity(0.08)))
                                }
                                
                                Button(action: {
                                    audioEngine.clearLogs()
                                }) {
                                    Text("Clear")
                                        .font(.system(size: 11, weight: .medium))
                                        .foregroundColor(.gray)
                                }
                            }
                            
                            // Log Terminal Console Box
                            ScrollViewReader { proxy in
                                ScrollView {
                                    LazyVStack(alignment: .leading, spacing: 3) {
                                        if audioEngine.logs.isEmpty {
                                            Text("No logs yet. Tap 'Start Listening' to begin.")
                                                .font(.system(size: 11, design: .monospaced))
                                                .foregroundColor(.gray)
                                        } else {
                                            ForEach(audioEngine.logs.indices, id: \.self) { idx in
                                                let logLine = audioEngine.logs[idx]
                                                Text(logLine)
                                                    .font(.system(size: 10, design: .monospaced))
                                                    .foregroundColor(logLine.contains("SUCCESS") || logLine.contains("PASS") ? .green : (logLine.contains("ERROR") ? .red : (logLine.contains("Chirp") ? .yellow : .cyan.opacity(0.85))))
                                                    .id(idx)
                                            }
                                        }
                                    }
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(10)
                                }
                                .frame(height: 180)
                                .background(Color.black.opacity(0.5))
                                .cornerRadius(12)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.1), lineWidth: 1)
                                )
                                .onChange(of: audioEngine.logs.count) { _ in
                                    if let lastIdx = audioEngine.logs.indices.last {
                                        withAnimation {
                                            proxy.scrollTo(lastIdx, anchor: .bottom)
                                        }
                                    }
                                }
                            }
                        }
                        .padding(.horizontal)
                        .padding(.top, 4)
                        
                        // MARK: - Sensitivity Slider
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Chirp Sensitivity Threshold: \(String(format: "%.2f", audioEngine.correlationThreshold))")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(.gray)
                                Spacer()
                                Text(audioEngine.correlationThreshold <= 0.18 ? "High Sensitivity" : "Normal")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundColor(.cyan)
                            }
                            Slider(value: $audioEngine.correlationThreshold, in: 0.10...0.35, step: 0.02)
                                .accentColor(.cyan)
                        }
                        .padding(.horizontal)
                        .padding(.bottom, 20)
                    }
                }
            }
            .navigationBarHidden(true)
        }
    }
}
