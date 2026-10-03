# 24 kHz Ultrasonic Audio Data Transmission

## 1. Project Overview

Build an acoustic data communication system that transmits digital data alongside a normal song using a **24 kHz ultrasonic carrier**.

The system has two primary components:

- **Speaker / Transmitter:** Plays a normal song while embedding data in a 24 kHz carrier.
- **Microphone / Receiver:** Captures the audio, isolates the 24 kHz channel, demodulates it, and reconstructs the original data.

### High-level flow

```text
                    TRANSMITTER

        ┌─────────────────────────────┐
        │          Normal Song        │
        └──────────────┬──────────────┘
                       │
                       │
        ┌──────────────▼──────────────┐
        │       Data / Payload        │
        └──────────────┬──────────────┘
                       │
                       ▼
                 Data Encoder
                       │
                       ▼
                Packet Builder
                       │
                       ▼
                24 kHz Modulator
                       │
                       ▼
              Song + 24 kHz Data
                       │
                       ▼
                    Speaker
                       │
                 Acoustic Path
                       │
                       ▼
                   Microphone
                       │
                       ▼
                 Audio Capture
                       │
                       ▼
               24 kHz Filtering
                       │
                       ▼
                 Demodulator
                       │
                       ▼
               Packet Decoder
                       │
                       ▼
                  CRC Check
                       │
                       ▼
                  Data Output

                    RECEIVER
```

---

# 2. Goal

The initial goal is to successfully transmit a small payload such as:

```text
HELLO
```

while a normal song is playing.

The receiver should detect the 24 kHz ultrasonic channel and reconstruct:

```text
HELLO
```

without requiring the user to hear the data channel.

---

# 3. Technical Constraints

## 3.1 Sample Rate

A 24 kHz signal requires an audio sample rate above 48 kHz for practical digital processing.

Recommended:

```text
Sample Rate: 96 kHz
Bit Depth:   24-bit where supported
```

### Why 96 kHz?

| Sample Rate | Nyquist Frequency | 24 kHz |
|-------------|-------------------|--------|
| 44.1 kHz | 22.05 kHz | Not possible |
| 48 kHz | 24 kHz | Exactly at Nyquist; not recommended |
| 96 kHz | 48 kHz | Supported |
| 192 kHz | 96 kHz | Supported |

The initial POC should therefore use **96 kHz** end-to-end wherever the hardware permits.

---

# 4. System Architecture

## 4.1 Speaker / Transmitter

```text
Song
  │
  ├─────────────────────┐
  │                     │
  │                  Audio Mixer
  │                     │
Data                   │
  │                     │
  ▼                     │
Encoder                  │
  │                      │
  ▼                      │
Packet Builder           │
  │                      │
  ▼                      │
24 kHz Modulator ────────┘
  │
  ▼
Song + Ultrasonic Data
  │
  ▼
Speaker
```

## 4.2 Microphone / Receiver

```text
Microphone
    │
    ▼
Audio Capture
    │
    ▼
96 kHz PCM
    │
    ▼
24 kHz Band-Pass Filter
    │
    ▼
Signal Detection
    │
    ▼
Demodulator
    │
    ▼
Bit Stream
    │
    ▼
Packet Synchronization
    │
    ▼
Payload Extraction
    │
    ▼
CRC Validation
    │
    ▼
Original Data
```

---

# 5. Speaker / Transmitter Stories

## ST-01 — Generate 24 kHz Carrier

### User Story

As a transmitter, I want to generate a stable 24 kHz carrier so that data can be transmitted in the ultrasonic frequency range.

### Acceptance Criteria

- Generate a stable 24 kHz sine wave.
- Support 96 kHz PCM.
- Carrier frequency should be configurable.
- Carrier amplitude should be configurable.
- Verify the carrier using FFT/spectrum analysis.

---

## ST-02 — Encode Data into Bits

### User Story

As a transmitter, I want to convert a payload into a stream of bits so that it can be transmitted acoustically.

### Acceptance Criteria

- Accept text or binary payload.
- Convert payload into bytes.
- Convert bytes into bits.
- Preserve payload ordering.
- Support configurable payload size.

Example:

```text
HELLO

48 45 4C 4C 4F

01001000 01000101 01001100 01001100 01001111
```

---

## ST-03 — Build Transmission Packet

### User Story

As a transmitter, I want to wrap the payload in a packet so that the receiver can identify and validate transmissions.

### Initial packet format

```text
┌──────────┬──────┬────────┬─────────┬─────┐
│ Preamble │ Sync │ Length │ Payload │ CRC │
└──────────┴──────┴────────┴─────────┴─────┘
```

### Acceptance Criteria

- Generate a known preamble.
- Include synchronization information.
- Include payload length.
- Include payload.
- Append CRC.
- Packet format should be versionable.

---

## ST-04 — Modulate Data onto 24 kHz Carrier

### User Story

As a transmitter, I want to modulate data onto a 24 kHz carrier so that the data can travel through the speaker.

### Initial modulation

Use **OOK (On-Off Keying)**.

```text
Bit 1 → 24 kHz carrier present
Bit 0 → carrier absent
```

### Acceptance Criteria

- Configurable symbol duration.
- Correct waveform generated for 0 and 1.
- Carrier remains at 24 kHz.
- Configurable transmission bitrate.
- Generate deterministic output for testing.

---

## ST-05 — Mix Ultrasonic Data with Music

### User Story

As a transmitter, I want to mix the ultrasonic data channel with a normal song so that both can be transmitted simultaneously.

Mathematically:

```text
Output(t) = Song(t) + UltrasonicData(t)
```

### Acceptance Criteria

- Preserve normal song playback.
- Add 24 kHz data channel.
- Prevent digital clipping.
- Provide configurable ultrasonic amplitude.
- Support gain normalization.

---

## ST-06 — Output Mixed Audio

### User Story

As a transmitter, I want to output the mixed audio through a speaker capable of reproducing 24 kHz.

### Acceptance Criteria

- Output using 96 kHz where supported.
- Detect unsupported audio routes.
- Verify 24 kHz output.
- Provide diagnostic information about sample rate and audio route.

---

## ST-07 — Transmitter Diagnostics

### User Story

As a developer, I want to inspect the generated signal so that I can verify the ultrasonic channel.

### Diagnostics

```text
Sample Rate:      96 kHz
Carrier:          24 kHz
Amplitude:        configurable
Bitrate:          configurable
Packet Size:      configurable
Clipping:         YES / NO
```

A spectrum view should show:

```text
Amplitude
   │
   │                 *
   │                 *
   │                 *
   └──────────────────────── Frequency
                    24 kHz
```

---

# 6. Microphone / Receiver Stories

## ST-08 — Capture Microphone Audio

### User Story

As a receiver, I want to capture microphone audio so that I can receive the ultrasonic transmission.

### Acceptance Criteria

- Request microphone permission.
- Capture audio continuously.
- Use 96 kHz where supported.
- Detect unsupported hardware/sample rates.
- Provide audio input diagnostics.

---

## ST-09 — Detect 24 kHz Signal

### User Story

As a receiver, I want to detect the presence of a 24 kHz signal so that I know when an ultrasonic transmission is occurring.

### Acceptance Criteria

- Analyze incoming PCM.
- Detect energy around 24 kHz.
- Configurable detection threshold.
- Avoid false detection from normal audio.
- Return signal strength.

---

## ST-10 — Isolate 24 kHz Channel

### User Story

As a receiver, I want to isolate the frequency region around 24 kHz so that the normal song has minimal impact on decoding.

### Initial architecture

```text
Microphone
    │
    ▼
96 kHz PCM
    │
    ▼
Band-Pass Filter
23–25 kHz
    │
    ▼
24 kHz Channel
```

### Acceptance Criteria

- Configurable filter bandwidth.
- Remove unwanted frequencies.
- Preserve the modulated 24 kHz signal.
- Provide signal-to-noise measurements.

---

## ST-11 — Demodulate 24 kHz Signal

### User Story

As a receiver, I want to demodulate the 24 kHz signal so that I can recover the transmitted bits.

### Initial OOK decoder

```text
24 kHz present → 1
24 kHz absent  → 0
```

### Acceptance Criteria

- Recover individual bits.
- Configurable symbol duration.
- Configurable detection threshold.
- Handle amplitude variation.
- Produce a raw bit stream.

---

## ST-12 — Detect Preamble and Synchronize

### User Story

As a receiver, I want to detect the packet preamble so that I can synchronize with the incoming data stream.

### Acceptance Criteria

- Detect known preamble.
- Identify packet start.
- Synchronize symbol timing.
- Ignore random ultrasonic noise.
- Handle packets arriving at arbitrary times.

---

## ST-13 — Decode Packet

### User Story

As a receiver, I want to decode the packet so that I can extract the payload.

### Acceptance Criteria

- Read packet length.
- Extract payload.
- Extract CRC.
- Reject malformed packets.
- Support future protocol versions.

---

## ST-14 — Validate CRC

### User Story

As a receiver, I want to validate the CRC so that corrupted packets are rejected.

### Acceptance Criteria

- Calculate CRC from received payload.
- Compare with transmitted CRC.
- Return PASS/FAIL.
- Do not expose corrupted payload as valid data.

---

## ST-15 — Reconstruct Original Data

### User Story

As a receiver, I want to convert decoded bits back into the original payload.

### Acceptance Criteria

- Convert bits to bytes.
- Convert bytes to payload.
- Preserve byte ordering.
- Support binary and text payloads.

---

## ST-16 — Receiver Diagnostics

### User Story

As a developer, I want visibility into the receiver pipeline so that transmission failures can be diagnosed.

### Example UI

```text
Microphone:       Connected
Sample Rate:      96 kHz
24 kHz Detected:  YES
Signal Strength:  -XX dB
Noise Floor:      -XX dB
SNR:              XX dB
Preamble:         Detected
Bits Received:    128
CRC:              PASS
Payload:          HELLO
```

---

# 7. End-to-End Stories

## ST-17 — End-to-End HELLO Transmission

### User Story

As a user, I want to transmit `HELLO` through a speaker and receive it through a microphone.

### Acceptance Criteria

- Speaker transmits `HELLO`.
- Microphone detects 24 kHz signal.
- Receiver identifies packet.
- Receiver decodes payload.
- CRC passes.
- Receiver displays `HELLO`.

---

## ST-18 — Music + Data Transmission

### User Story

As a user, I want to play a normal song while simultaneously transmitting data through the 24 kHz channel.

### Acceptance Criteria

- Song continues playing.
- 24 kHz data is transmitted simultaneously.
- Receiver can isolate the 24 kHz channel.
- Receiver can decode data while music is playing.
- No audible clipping is introduced.

---

## ST-19 — Measure Transmission Reliability

### User Story

As a developer, I want to measure the reliability of the acoustic data channel.

### Metrics

```text
Bit Rate
Bit Error Rate (BER)
Packet Success Rate
Detection Rate
Signal-to-Noise Ratio (SNR)
Maximum Reliable Distance
```

### Test distances

```text
1 m
2 m
5 m
10 m
```

### Test environments

```text
Quiet room
Normal room
Music at low volume
Music at normal volume
Different songs
Different speakers
Different microphones
```

---

# 8. Future Modulation Options

Once OOK works, evaluate more advanced modulation schemes.

## Phase 1 — OOK

```text
1 → Carrier ON
0 → Carrier OFF
```

Simple and easy to debug.

## Phase 2 — BPSK

Keep the carrier at 24 kHz and encode data using phase changes.

```text
0 → 0°
1 → 180°
```

Potentially more robust than OOK.

## Phase 3 — QPSK

Encode two bits per symbol.

```text
00 → 0°
01 → 90°
10 → 180°
11 → 270°
```

This can increase data throughput but requires a more sophisticated receiver.

## Phase 4 — Error Correction

Evaluate:

- Hamming codes
- Reed-Solomon
- Convolutional coding
- LDPC
- Interleaving

---

# 9. Initial POC Scope

The first POC should remain deliberately simple.

### Transmitter

```text
Text
 ↓
Bits
 ↓
Packet
 ↓
OOK
 ↓
24 kHz
 ↓
Mix with Song
 ↓
Speaker
```

### Receiver

```text
Microphone
 ↓
96 kHz PCM
 ↓
23–25 kHz Filter
 ↓
24 kHz Detection
 ↓
OOK Demodulation
 ↓
Packet Sync
 ↓
CRC
 ↓
Text
```

---

# 10. MVP Definition

The MVP is complete when the following scenario works:

```text
             SPEAKER
                │
       ┌────────▼────────┐
       │ Normal Song     │
       │       +         │
       │  24 kHz "HELLO" │
       └────────┬────────┘
                │
                │ Air
                ▼
            MICROPHONE
                │
                ▼
         24 kHz Decoder
                │
                ▼
             "HELLO"
```

### MVP acceptance criteria

- [ ] Generate 24 kHz carrier.
- [ ] Encode `HELLO`.
- [ ] Build packet.
- [ ] OOK-modulate packet.
- [ ] Mix with a normal song.
- [ ] Play through a 24 kHz-capable speaker.
- [ ] Capture through a 24 kHz-capable microphone.
- [ ] Detect 24 kHz.
- [ ] Recover bits.
- [ ] Detect preamble.
- [ ] Decode packet.
- [ ] Validate CRC.
- [ ] Display `HELLO`.

---

# 11. Recommended Development Order

```text
Phase 1
  ↓
24 kHz Tone Generation
  ↓
Phase 2
  ↓
Speaker → Microphone Detection
  ↓
Phase 3
  ↓
OOK Bit Transmission
  ↓
Phase 4
  ↓
Packet + Preamble + CRC
  ↓
Phase 5
  ↓
HELLO End-to-End
  ↓
Phase 6
  ↓
Song + 24 kHz Data
  ↓
Phase 7
  ↓
Range / BER Testing
  ↓
Phase 8
  ↓
BPSK / QPSK / Error Correction
```

---

# 12. Key Technical Risks

## Hardware Frequency Response

The speaker and microphone must actually support the 24 kHz channel.

A device advertised as 20 Hz–20 kHz is not sufficient evidence that it can transmit or receive 24 kHz.

## iOS Audio Pipeline

If the final implementation targets iPhone/iOS, verify:

- Microphone hardware response
- Audio session configuration
- Supported input sample rates
- Bluetooth audio limitations
- System audio processing
- Hardware filters
- Route-specific limitations

The physical acoustic path must be tested rather than assuming the theoretical sample rate guarantees 24 kHz transmission.

## Music Interference

The song may contain energy near the upper end of the audible spectrum and may introduce nonlinear/intermodulation components.

Testing should therefore include multiple songs and playback levels.

## Speaker Nonlinearity

A speaker can generate harmonics and intermodulation products. These can potentially create unwanted components that interfere with the receiver.

## Signal Level

Increasing the ultrasonic signal amplitude improves detection but can introduce:

- Clipping
- Audible artifacts
- Speaker distortion
- Unwanted harmonics

The transmitter should therefore have configurable gain and safety limits.

---

# 13. Success Metrics

The project should ultimately report:

```text
Carrier Frequency       = 24 kHz
Sample Rate             = 96 kHz
Modulation              = OOK / BPSK / QPSK
Bitrate                 = XX bps
Packet Size             = XX bytes
BER                     = XX%
Packet Success Rate     = XX%
SNR                     = XX dB
Maximum Reliable Range  = XX meters
```

The objective is not only to demonstrate that data can be transmitted, but to determine **how reliably and at what data rate the 24 kHz acoustic channel works under realistic conditions**.
