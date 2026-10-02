# SonicWave: iOS Microphone / Receiver Specification & Stories

## 1. Project Goal & Final Deliverable

The primary deliverable of the Microphone Stories is a **Native iOS Application (Swift / SwiftUI)** called **SonicWave Receiver**.

### App Behavior:
1. The user opens the iOS app on an **iPhone** or **iPad**.
2. The user taps a **"Start Listening"** button to start real-time microphone capture.
3. When `sonicwave_music_hello.wav` (or any music track containing the ultrasonic payload) plays in the room from a MacBook Pro or external speaker, the iPhone's microphone captures the sound.
4. The iOS DSP engine filters out audible music ($<16\text{ kHz}$), locks onto the $19.2\text{ kHz}$ ultrasonic carrier, demodulates the bits, validates the CRC-16 checksum, and **instantly displays `"HELLO"` on the iPhone screen**.
5. The user can tap **"Stop Listening"** to halt microphone capture and release audio hardware.

---

## 2. iOS App Architecture & Pipeline

```
                                  iOS APP ARCHITECTURE

  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                            SwiftUI User Interface                               │
  │                                                                                 │
  │   [ Start / Stop Listening Button ]   [ Live Ultrasonic Level Bar (dBFS) ]      │
  │   [ Connection / Sync Status HUD  ]   [ Large Decoded Message Card: "HELLO" ]   │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ ObservableObject / @Published State
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                           SonicWaveAudioEngine (Swift)                          │
  │                                                                                 │
  │   AVAudioEngine / AVAudioSession (48 kHz, .measurement mode, No AGC/Filters)    │
  └───────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ 48 kHz PCM Float32 Tap Buffer
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                           SonicWaveDSPCore (Accelerate / vDSP)                  │
  │                                                                                 │
  │   1. [ST-RX-02] vDSP Biquad Bandpass Filter (18.5 kHz - 20.0 kHz)               │
  │   2. [ST-RX-03] Matched-Filter Cross-Correlation (LFM Chirp Detector)           │
  │   3. [ST-RX-04] 2-FSK Quadrature Energy Demodulator (f0=18.8k, f1=19.6k)        │
  │   4. [ST-RX-05] Packet Deframer & CRC-16 Checksum Validator                     │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Acoustic Channel Configuration (iOS Target)

| Parameter | iOS Standard Profile |
| :--- | :--- |
| **Hardware** | iPhone built-in microphone (Bottom & Top Mics) |
| **Native iOS Sample Rate ($F_s$)** | **$48,000\text{ Hz}$** |
| **Center Frequency ($f_c$)** | **$19,200\text{ Hz}$** ($19.2\text{ kHz}$) |
| **Passband Range** | $18,500\text{ Hz} - 20,000\text{ Hz}$ |
| **Audible Music Attenuation** | $\ge 40\text{ dB}$ for $f < 16,500\text{ Hz}$ |
| **2-FSK Tone 0 ($f_0$)** | $18,800\text{ Hz}$ (Bit `0`) |
| **2-FSK Tone 1 ($f_1$)** | $19,600\text{ Hz}$ (Bit `1`) |
| **Preamble Chirp Reference** | $18,500\text{ Hz} \to 19,900\text{ Hz}$ ($50\text{ ms}$ linear sweep) |

---

## 4. iOS Microphone User Stories

### **ST-RX-01: iOS Audio Session & Raw Microphone Capture**
* **User Story:** As an iOS app user, I want the app to configure the iPhone audio hardware for raw, unprocessed high-frequency capture at $48\text{ kHz}$, so that iOS does not filter out or suppress ultrasonic tones.
* **Technical Details:**
  - Configures `AVAudioSession` with `.measurement` mode:
    ```swift
    let session = AVAudioSession.sharedInstance()
    try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .allowBluetooth])
    try session.setPreferredSampleRate(48000.0)
    try session.setActive(true)
    ```
  - Attaches `AVAudioNodeTap` on `AVAudioEngine.inputNode` with a buffer size of 2048 samples ($\approx 42\text{ ms}$).
* **Acceptance Criteria:**
  1. Prompts the user for microphone permission (`NSMicrophoneUsageDescription`).
  2. Successfully acquires $48\text{ kHz}$ float PCM audio buffers without clipping or dropouts.
  3. Bypasses Apple's automatic noise cancellation, voice isolation, and AGC filters.

---

### **ST-RX-02: Real-Time Biquad Bandpass Filter (Accelerate / vDSP)**
* **User Story:** As an iOS receiver engine, I want to filter incoming PCM buffers using Apple's `Accelerate` / `vDSP` biquad filter, so that loud music and human voices ($<16\text{ kHz}$) are removed with low CPU overhead.
* **Technical Details:**
  - Cascaded 4-section Biquad IIR Bandpass Filter ($18.5\text{ kHz} - 20.0\text{ kHz}$).
  - Computed using `vDSP_biquad` or `vDSP_biquadm_Setup`.
* **Acceptance Criteria:**
  1. Attenuates audible music ($<16\text{ kHz}$) by at least $40\text{ dB}$.
  2. Processes 2048-sample audio blocks in $< 2\text{ ms}$ ($< 5\%$ CPU utilization).
  3. Preserves phase linearity across the $18.5 - 19.9\text{ kHz}$ data band.

---

### **ST-RX-03: Preamble Chirp Matched-Filter Detector (Swift / vDSP)**
* **User Story:** As an iOS receiver engine, I want to cross-correlate incoming filtered audio with a pre-computed reference chirp template, so that packet start time ($t_0$) is detected accurately in real time.
* **Technical Details:**
  - Sliding cross-correlation via `vDSP_conv` or FFT correlation.
  - Normalized peak detection with dynamic noise-floor scaling.
* **Acceptance Criteria:**
  1. Triggers a synchronization lock within $1\text{ ms}$ of preamble chirp arrival.
  2. Rejects false positives caused by high-frequency music transients (cymbal crashes, hi-hats).
  3. Emits packet boundary sample index to downstream demodulator.

---

### **ST-RX-04: Non-Coherent 2-FSK Quadrature Energy Demodulator**
* **User Story:** As an iOS receiver engine, I want to measure quadrature tone energy at $18.8\text{ kHz}$ ($f_0$) and $19.6\text{ kHz}$ ($f_1$) for each symbol window, so that transmitted bits are recovered without requiring carrier phase locking.
* **Technical Details:**
  - Quadrature integration:
    $$\text{Power}(f) = \left(\sum x[n] \cos(2\pi f n)\right)^2 + \left(\sum x[n] \sin(2\pi f n)\right)^2$$
  - Decision: $\text{Power}(f_1) > \text{Power}(f_0) \implies \text{bit } 1$, else $\text{bit } 0$.
* **Acceptance Criteria:**
  1. Accurately recovers bits across a $20\text{ ms}$ symbol period.
  2. Samples at symbol mid-points to avoid transition boundaries.
  3. Calculates instantaneous Signal-to-Noise Ratio (SNR in dB).

---

### **ST-RX-05: Packet Deframer, CRC-16 Validation & Payload Dispatch**
* **User Story:** As an iOS receiver engine, I want to parse the decoded bitstream, verify the CRC-16 checksum, and extract the text payload (`"HELLO"`), so that only verified messages reach the UI.
* **Technical Details:**
  - Parses 13-bit Barker code (`1111100110101`).
  - Reads 8-bit length header $N$.
  - Computes standard CRC-16-CCITT (`0x1021`, init `0xFFFF`) over payload bytes.
* **Acceptance Criteria:**
  1. If CRC passes: Dispatches payload (e.g., `"HELLO"`) and SNR metric to SwiftUI `@Published` state on the main thread.
  2. If CRC fails: Discards corrupted packet silently without UI error popup.
  3. Includes a debounce filter (prevents duplicate triggers within $1.0\text{ second}$).

---

### **ST-RX-06: SwiftUI User Interface & Controls**
* **User Story:** As an iPhone user, I want a clean, modern iOS interface with a Start/Stop listening button, a live ultrasonic VU meter, and a large message display card, so that I can see the decoded message when music plays.
* **UI Components:**
  1. **Header:** "SonicWave Ultrasonic Receiver" + Status badge (`IDLE` / `LISTENING` / `DECODING`).
  2. **Start / Stop Toggle Button:**
     - Large, prominent button (Green "Start Listening" ➔ Red "Stop Listening").
     - Haptic feedback on tap (`UIImpactFeedbackGenerator`).
  3. **Live Ultrasonic Signal Bar:**
     - Dynamic VU meter bar showing incoming energy in the $18.5 - 20\text{ kHz}$ band in real time.
  4. **Decoded Message Card:**
     - Prominent central card displaying the latest message:
       ```text
       ┌────────────────────────────────────────┐
       │  LATEST RECEIVED MESSAGE               │
       │                                        │
       │               "HELLO"                  │
       │                                        │
       │  CRC: PASS  •  SNR: 38.2 dB  •  17:46  │
       └────────────────────────────────────────┘
       ```
  5. **History Log:** Scrollable list of previously received messages with timestamps.
* **Acceptance Criteria:**
  1. Supports iOS 16+ on all iPhone screen sizes.
  2. Updates UI instantly on the main thread when a message is decoded.
  3. Smooth animations for VU meter and message card transitions.

---

## 5. End-to-End iOS Verification Protocol

| Test Case | Scenario | Expected Result |
| :--- | :--- | :--- |
| **TC-iOS-01** | App Launch & Mic Permission | App launches, requests microphone permission, and displays IDLE state. |
| **TC-iOS-02** | Start / Stop Toggle | Tapping "Start Listening" activates mic stream and VU meter; tapping "Stop" halts mic and sets status to IDLE. |
| **TC-iOS-03** | Silent Room Noise Floor | In a quiet room, VU meter shows low noise floor ($-50\text{ dBFS}$ to $-60\text{ dBFS}$); no false triggers. |
| **TC-iOS-04** | Soundtrack Decoding (`sonicwave_music_hello.wav`) | When `sonicwave_music_hello.wav` is played on MacBook Pro speakers, the iPhone app detects the carrier within 2 seconds and displays **`"HELLO"`** with CRC PASS. |
| **TC-iOS-05** | Distance & Orientation Test | iPhone successfully decodes `"HELLO"` from 1 meter, 2 meters, and 3 meters away across the desk. |
