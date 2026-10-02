# SonicWave 🌊🔊

SonicWave enables near-ultrasonic, acoustic data transmission over standard audio speakers and microphones. Digital text payloads are encoded silently within music tracks using continuous-phase 2-FSK at 19.2 kHz with CRC-16 error checking and decoded in real-time on native iOS devices or Python receivers.

## Repository Organization

The project is structured into two dedicated directories:

### 1. `transmitter/` (Mac / Audio Generation & Playback)
- **`generate_soundtrack.py`**: Generates composite soundtrack WAV files mixing ambient music and ultrasonic data bursts.
- **`transmit.py`**: Streams generated soundtracks through MacBook Pro or external speakers.
- **`sonicwave/`**: Transmitter DSP engine (FSK modulation, chirp synthesis, ambient chord generator, soft-knee mixer).
- **`sonicwave_music_hello.wav`**: Pre-generated audio ready to play.
- **`SPEAKER_STORIES.md`**: Specification and requirements for speaker transmission.

### 2. `receiver/` (iOS Native App & Desktop Listener)
- **`ios/SonicWaveReceiver/`**: Native iOS app built with SwiftUI, `AVAudioEngine` (.measurement mode, 48 kHz), and Accelerate `vDSP` / Biquad bandpass filter.
- **`listen.py`**: Desktop Python microphone listener and real-time decoder.
- **`sonicwave/`**: Receiver DSP engine (matched-filter cross-correlation, non-coherent quadrature tone energy demodulation, CRC-16).
- **`test_roundtrip.py`**: End-to-end file streaming and decoding test suite.
- **`tests/`**: DSP and framing unit tests.
- **`MICROPHONE_STORIES.md`**: Specification and requirements for microphone reception.

---

## Quick Start

### Transmitter
```bash
# 1. Generate soundtrack with custom text
python transmitter/generate_soundtrack.py --payload "Hello world"

# 2. Transmit through speakers
python transmitter/transmit.py
```

### Receiver
1. **iOS App**: Open `receiver/ios/SonicWaveReceiver/SonicWaveReceiver.xcodeproj` in Xcode and press **Run (⌘R)** to install on iPhone.
2. **Desktop Listener**:
   ```bash
   python receiver/listen.py
   ```
