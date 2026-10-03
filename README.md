# SonicWave 🌊🔊

SonicWave enables near-ultrasonic, acoustic data transmission over standard audio speakers and microphones. Digital text payloads are encoded silently within music tracks using continuous-phase 2-FSK at 19.2 kHz with CRC-16 error checking and decoded in real-time on native iOS devices or Python receivers.

## Repository Organization

The project is structured into two dedicated directories:

### 1. `transmitter/` (Mac / Audio Generation & Playback)
- **`web_app.py`**: Modern Web UI Dashboard for one-click browser-based transmission.
- **`interactive.py`**: Interactive terminal prompt REPL for conversational typing.
- **`transmit.py`**: Multi-mode audio transmitter (supports `--text`, `--interactive`, `--web`, `--loop`).
- **`generate_soundtrack.py`**: Standalone soundtrack generator mixing music and ultrasonic data bursts.
- **`sonicwave/`**: Transmitter DSP engine (FSK modulation, chirp synthesis, ambient chord generator, soft-knee mixer).
- **`SPEAKER_STORIES.md`**: Specification and requirements for speaker transmission.

### 2. `receiver/` (iOS Native App & Desktop Listener)
- **`ios/SonicWaveReceiver/`**: Native iOS app built with SwiftUI, `AVAudioEngine` (.measurement mode, 48 kHz), and Accelerate `vDSP` / Biquad bandpass filter.
- **`listen.py`**: Desktop Python microphone listener and real-time decoder.
- **`sonicwave/`**: Receiver DSP engine (matched-filter cross-correlation, non-coherent quadrature tone energy demodulation, CRC-16).
- **`test_roundtrip.py`**: End-to-end file streaming and decoding test suite.
- **`tests/`**: DSP and framing unit tests.
- **`MICROPHONE_STORIES.md`**: Specification and requirements for microphone reception.

---

## Quick Start: Easy Transmitter Interfaces

You can choose whichever transmission interface fits your preference:

### Option A: Modern Web Dashboard (Recommended) 🌐
Launch the visual web interface with one-click presets and live status:
```bash
python transmitter/web_app.py
# or
python transmitter/transmit.py --web
```
*(Automatically opens `http://127.0.0.1:5005` in your browser. Type your message and hit **⌘+Enter** to broadcast!)*

### Option B: Interactive Terminal Prompt 💬
Type messages conversationally straight from your shell:
```bash
python transmitter/interactive.py
# or
python transmitter/transmit.py --interactive
```
```
SonicWave TX > Hello
[▶] Transmitting "Hello" (5 bytes, 19.2 kHz)... [COMPLETE]

SonicWave TX > Jigar
[▶] Transmitting "Jigar" (5 bytes, 19.2 kHz)... [COMPLETE]
```

### Option C: Instant One-Liner CLI ⚡
Transmit arbitrary text on the fly without separate generation steps:
```bash
python transmitter/transmit.py --text "Hello world"

# Continuous loop transmission:
python transmitter/transmit.py --text "Jigar" --loop --delay 3.0
```

### Receiver
1. **iOS App**: Open `receiver/ios/SonicWaveReceiver/SonicWaveReceiver.xcodeproj` in Xcode and press **Run (⌘R)** to install on iPhone.
2. **Desktop Listener**:
   ```bash
   python receiver/listen.py
   ```
