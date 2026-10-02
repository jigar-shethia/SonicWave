# SonicWave: Ultrasonic Audio Data Transmission
## User Stories & Technical Backlog

### Project Deliverables
1. **Speaker / Transmitter (MacBook Pro):**
   - Produces the composite audio soundtrack (`sonicwave_music_hello.wav` / `transmit.py`) containing **Normal Music + Silent Ultrasonic Carrier ($19.2\text{ kHz}$)** carrying `"HELLO"`.
2. **Microphone / Receiver (Native iOS App):**
   - A **SwiftUI iOS App** with a **"Start/Stop Listening"** button.
   - Listens to audio in the room via iPhone built-in microphone.
   - When `sonicwave_music_hello.wav` is played, the app filters out audible music, extracts the ultrasonic data, and **displays `"HELLO"` on the screen** with CRC status and SNR metrics.

---

## 1. System Parameter Profiles

| Parameter | iOS Standard Profile (Default) |
| :--- | :--- |
| **Transmitter** | MacBook Pro Speakers (`sonicwave_music_hello.wav`) |
| **Receiver** | iPhone App (Swift / SwiftUI / AVFoundation / Accelerate) |
| **Center Frequency ($f_c$)** | **$19.2\text{ kHz}$** ($19,200\text{ Hz}$) |
| **Channel Passband** | $18.5\text{ kHz} - 20.0\text{ kHz}$ |
| **Native Sample Rate ($F_s$)** | **$48\text{ kHz}$** ($48,000\text{ Hz}$) |
| **2-FSK Tone 0 ($f_0$)** | $18.8\text{ kHz}$ |
| **2-FSK Tone 1 ($f_1$)** | $19.6\text{ kHz}$ |
| **Payload** | `"HELLO"` (ASCII string) |

---

## 2. Speaker / Transmitter Stories (TX)

* **ST-TX-01 (Packet Framing & CRC-16):** Encapsulates `"HELLO"` with Barker sync code, length byte, and CRC-16 checksum.
* **ST-TX-02 (Ultrasonic 2-FSK Modulation):** Modulates bitstream onto $19.2\text{ kHz}$ carrier using Continuous-Phase FSK.
* **ST-TX-03 (Preamble Chirp Generator):** Prepends $50\text{ ms}$ linear frequency sweep ($18.5 \to 19.9\text{ kHz}$) for matched-filter synchronization.
* **ST-TX-04 (Pulse Shaping & Anti-Click):** Raised-Cosine / Hann windowing to suppress audible clicks ($<16\text{ kHz}$) by $\ge 45\text{ dB}$.
* **ST-TX-05 (Dynamic Music Mixer):** Layers ultrasonic data onto normal music at $-20\text{ dB}$ with soft-knee peak limiting (no clipping).
* **ST-TX-06 (Export Soundtrack WAV):** Generates `sonicwave_music_hello.wav` (playable anywhere).
* **ST-TX-07 (Mac Audio Player):** Streams soundtrack directly to MacBook Pro speakers via `transmit.py`.
* **ST-TX-08 (Transmitter Spectrum Plot):** Exports `sonicwave_music_hello_spectrum.png` for frequency verification.

---

## 3. iOS Microphone / Receiver Stories (RX)

* **ST-RX-01 (iOS Audio Session Setup):** Configures `AVAudioSession` with `.measurement` mode at $48\text{ kHz}$ to bypass iOS voice isolation and AGC.
* **ST-RX-02 (vDSP Biquad Bandpass Filter):** High-performance bandpass filter isolating $18.5 - 20.0\text{ kHz}$ and attenuating audible music by $\ge 40\text{ dB}$.
* **ST-RX-03 (Matched-Filter Chirp Detector):** Cross-correlates audio buffer against reference chirp to lock packet boundary ($t_0$).
* **ST-RX-04 (2-FSK Energy Demodulator):** Quadrature tone energy detector comparing power at $18.8\text{ kHz}$ vs $19.6\text{ kHz}$.
* **ST-RX-05 (Packet Deframer & CRC-16 Validator):** Reconstructs payload, verifies CRC-16, and dispatches verified message.
* **ST-RX-06 (SwiftUI Screen & Controls):**
  - **Start / Stop Listening Button** (toggles microphone capture).
  - **Live Ultrasonic VU Meter** (real-time signal level bar).
  - **Prominent Message Display Card** (displays `"HELLO"`, CRC status, and SNR).
  - **History Log** (timestamped list of received messages).

---

## 4. End-to-End Test (Mac Speaker ➔ iPhone App)

* **E2E-01 (Acoustic Decoding of 'HELLO'):**
  1. User taps **"Start Listening"** on the iPhone app.
  2. User plays `sonicwave_music_hello.wav` on MacBook Pro speaker.
  3. iPhone microphone captures audio, processes ultrasonic channel, and displays **`"HELLO"`** on the screen.
