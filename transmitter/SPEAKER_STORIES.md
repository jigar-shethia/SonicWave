# SonicWave: Speaker / Transmitter Specification & Stories

## 1. Project Goal & Final Deliverable

The primary objective of the Speaker Stories is to produce an **Audio Soundtrack** (`.wav` file and live playback stream) that seamlessly combines:
1. **Audible Music:** A normal song (vocals, beats, instruments).
2. **Ultrasonic Data Channel:** A silent ultrasonic carrier ($19.2\text{ kHz}$ for universal iPhone/Mac compatibility or $24.0\text{ kHz}$ for HD mode) carrying the embedded payload `"HELLO"`.

When this soundtrack is played through **any speaker** (MacBook Pro, Bluetooth speaker, or home audio), a listening microphone will detect the ultrasonic carrier and immediately print:
```text
HELLO
```
on the receiver's console, while human listeners in the room hear **only the normal music**.

---

## 2. High-Level Flow & Deliverables

```
                                  TRANSMITTER PIPELINE
                                  
  ┌─────────────────────────┐
  │     Audible Song        │ (e.g. background_music.wav)
  └────────────┬────────────┘
               │
               │               ┌─────────────────────────┐
               │               │   Payload: "HELLO"      │
               │               └────────────┬────────────┘
               │                            │
               │                            ▼
               │               ┌─────────────────────────┐
               │               │ [ST-TX-01] Packet Frame │ (Sync + Len + Data + CRC)
               │               └────────────┬────────────┘
               │                            │
               │                            ▼
               │               ┌─────────────────────────┐
               │               │ [ST-TX-02] Modulation   │ (19.2 kHz / 24 kHz 2-FSK/OOK)
               │               └────────────┬────────────┘
               │                            │
               │                            ▼
               │               ┌─────────────────────────┐
               │               │ [ST-TX-03] Sync Chirp   │ (Linear Preamble Sweep)
               │               └────────────┬────────────┘
               │                            │
               │                            ▼
               │               ┌─────────────────────────┐
               │               │ [ST-TX-04] Pulse Shape  │ (Hann / RRC Anti-Click)
               │               └────────────┬────────────┘
               │                            │
               ▼                            ▼
  ┌──────────────────────────────────────────────────────┐
  │ [ST-TX-05] Dynamic Audio Mixer & Headroom Normalizer │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────┐
  │           ★ FINAL TRANSMITTER DELIVERABLES ★         │
  │                                                      │
  │ 1. [ST-TX-06] Composite Soundtrack WAV File:         │
  │    "sonicwave_music_hello.wav" (Playable anywhere)   │
  │                                                      │
  │ 2. [ST-TX-07] Live Audio Streamer to MacBook Speaker │
  │                                                      │
  │ 3. [ST-TX-08] Real-Time FFT Spectrum & Verification  │
  └──────────────────────────────────────────────────────┘
```

---

## 3. Carrier & Profile Configuration

| Parameter | Profile A: Universal Standard (Default) | Profile B: HD Pro Mode |
| :--- | :--- | :--- |
| **Primary Target** | MacBook Pro Speaker ➔ iPhone & Mac Mic | MacBook Pro ➔ HD Audio Interface |
| **Carrier Frequency ($f_c$)** | **$19.2\text{ kHz}$** | **$24.0\text{ kHz}$** |
| **Sample Rate ($F_s$)** | **$48\text{ kHz}$** (Standard for iOS/macOS) | **$96\text{ kHz}$** |
| **2-FSK Tone 0 ($f_0$)** | $18.8\text{ kHz}$ | $23.5\text{ kHz}$ |
| **2-FSK Tone 1 ($f_1$)** | $19.6\text{ kHz}$ | $24.5\text{ kHz}$ |
| **Sync Chirp Sweep** | $18.5\text{ kHz} \to 19.9\text{ kHz}$ ($50\text{ ms}$) | $23.0\text{ kHz} \to 25.0\text{ kHz}$ ($50\text{ ms}$) |
| **Transmission Payload** | `"HELLO"` (ASCII string) | `"HELLO"` (ASCII string) |

---

## 4. Speaker / Transmitter User Stories

### **ST-TX-01: Packet Framing & Checksum Generation**
* **User Story:** As a transmitter, I want to convert the payload `"HELLO"` into a structured bit frame with sync markers, length header, and a CRC-16 checksum, so that the receiver can reliably identify packet boundaries and detect corruption.
* **Frame Structure:**
  ```text
  ┌──────────────────┬──────────────┬───────────────┬───────────────────────────┬──────────┐
  │ Preamble Chirp   │ Barker Sync  │ Length Header │ Payload ("HELLO")         │ CRC-16   │
  │ (50 ms sweep)    │ (13-bit code)│ 1 byte (5)    │ 5 bytes (0x48 45 4C 4C 4F)│ 2 bytes  │
  └──────────────────┴──────────────┴───────────────┴───────────────────────────┴──────────┘
  ```
* **Acceptance Criteria:**
  1. Encodes `"HELLO"` (ASCII `0x48 0x45 0x4C 0x4C 0x4F` $\to 40\text{ bits}$).
  2. Computes CRC-16-CCITT (`0x1021`, init `0xFFFF`) over payload.
  3. Appends 13-bit Barker sync sequence (`1111100110101`).
  4. Returns deterministic binary vector.

---

### **ST-TX-02: Ultrasonic Carrier & 2-FSK / OOK Modulation**
* **User Story:** As a transmitter, I want to modulate the framed bitstream onto an ultrasonic carrier ($19.2\text{ kHz}$ or $24.0\text{ kHz}$), so that the digital data is converted into silent acoustic sound waves.
* **Acceptance Criteria:**
  1. Implements Continuous-Phase 2-FSK (Tone `0` = $18.8\text{ kHz}$, Tone `1` = $19.6\text{ kHz}$) with configurable symbol rate ($20 - 40\text{ ms}$ per bit).
  2. Supports Shaped OOK mode (Carrier ON = $19.2\text{ kHz}$, Carrier OFF = Silent).
  3. Ensures phase continuity across frequency shifts to eliminate harmonic distortion.

---

### **ST-TX-03: Preamble Linear Frequency Chirp Generator**
* **User Story:** As a transmitter, I want to prepend a linear frequency up-chirp ($18.5\text{ kHz} \to 19.9\text{ kHz}$) before the data frame, so that the receiver's matched filter can lock onto the exact start sample ($t_0$) even under low SNR or loud music.
* **Acceptance Criteria:**
  1. Generates a $50\text{ ms}$ linear frequency sweep.
  2. Tapers chirp edges with Hann envelope to eliminate spectral leakage.
  3. Chirp parameters strictly match receiver matched-filter reference.

---

### **ST-TX-04: Pulse Shaping & Anti-Click Smoothing**
* **User Story:** As a transmitter, I want to apply Raised-Cosine or Hann envelope windowing to all modulated symbols, so that rapid on/off or tone transitions do not create audible "clicks" or "pops" in human hearing range ($<16\text{ kHz}$).
* **Acceptance Criteria:**
  1. Smooths rise and fall edges of every symbol ($\alpha = 0.25$ or Hann envelope).
  2. Attenuates audible out-of-band splatter ($<16\text{ kHz}$) by $\ge 45\text{ dB}$.
  3. Verified by listening in a quiet room: data transmission produces zero audible clicks.

---

### **ST-TX-05: Dynamic Music Mixer & Headroom Normalizer**
* **User Story:** As a transmitter, I want to mix the generated ultrasonic `"HELLO"` signal with a normal music track, so that both coexist in a single audio stream without digital clipping or harmonic intermodulation.
* **Acceptance Criteria:**
  1. Layers: $\text{Output}[n] = \text{Music}[n] + G_{\text{ultrasonic}} \cdot \text{Data}[n]$.
  2. Ultrasonic gain $G_{\text{ultrasonic}}$ is set to $-18\text{ dB}$ to $-24\text{ dB}$ relative to music level.
  3. Peak normalizer / soft limiter ensures composite waveform satisfies $|\text{Output}| \le 0.98$ (preventing DAC clipping).

---

### **ST-TX-06: Export Composite Soundtrack WAV File**
* **User Story:** As a user, I want to export the mixed audio (Music + Ultrasonic `"HELLO"`) into a standard `.wav` soundtrack file, so that I can play it anywhere (Mac, iPhone, iPad, home speaker) or share it.
* **Acceptance Criteria:**
  1. Generates `sonicwave_music_hello.wav` in the project directory.
  2. Audio format: Standard 24-bit / 16-bit PCM stereo/mono at $48\text{ kHz}$ (or $96\text{ kHz}$).
  3. File is playable in any standard media player (QuickTime, Apple Music, VLC, browser).

---

### **ST-TX-07: Real-Time Audio Playback to MacBook Pro Speakers**
* **User Story:** As a user, I want to play the composite soundtrack directly through MacBook Pro speakers via command-line or Python script, so that I can instantly transmit `"HELLO"` across the room without third-party audio software.
* **Acceptance Criteria:**
  1. Streams low-latency audio via `sounddevice` / CoreAudio at $48\text{ kHz}$ / $96\text{ kHz}$.
  2. Supports loop mode (repeating the `"HELLO"` burst every few seconds over the song).
  3. Clean audio playback with no glitches, dropouts, or audible artifacts.

---

### **ST-TX-08: Transmitter Diagnostic Console & Spectrum Inspector**
* **User Story:** As a developer, I want to view a real-time FFT spectrum and diagnostic console when generating/playing the soundtrack, so that I can verify carrier frequency, amplitude, and packet timing.
* **Acceptance Criteria:**
  1. Generates high-resolution FFT plot showing normal music spectrum ($0 - 15\text{ kHz}$) and the sharp ultrasonic spike at $19.2\text{ kHz}$ (or $24.0\text{ kHz}$).
  2. Console displays:
     - Sample Rate & Duration.
     - Ultrasonic carrier power (dBFS).
     - Peak headroom indicator (Clipping: NO).
     - Total packet transmission time ($\approx 1.5\text{ s}$).

---

## 5. Summary of Outputs

| Output Item | Description | Location / Destination |
| :--- | :--- | :--- |
| **Soundtrack WAV File** | `sonicwave_music_hello.wav` (Music + Ultrasonic "HELLO") | `/Users/jigarshethia/Documents/SonicWave/` |
| **Physical Sound** | Audible music from speakers + silent ultrasonic acoustic waves | MacBook Pro Speaker |
| **Diagnostic Plot** | Power Spectral Density (PSD) showing 19.2 kHz carrier spike | `tx_spectrum_verification.png` |
| **Console Telemetry** | Status, symbol rate, ultrasonic gain, and peak limiter stats | Terminal Console |
