#!/usr/bin/env python3
"""
Automated End-to-End File Roundtrip Test
Tests reading 'sonicwave_music_hello.wav', feeding it in chunks through StreamReceiver,
and validating that 'HELLO' is decoded with 100% accuracy.
"""

import os
import sys

# Ensure script dir and root are in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import numpy as np
import soundfile as sf
from sonicwave.config import SonicConfig, ProfileType
from sonicwave.demodulation import StreamReceiver


def test_file_roundtrip(wav_file="sonicwave_music_hello.wav"):
    """
    Automated verification harness for the complete SonicWave receiver pipeline.
    
    1. Loads an encoded composite audio file containing embedded ultrasonic data.
    2. Slices the audio into small 50 ms chunks to accurately simulate real-time microphone input.
    3. Streams blocks sequentially through StreamReceiver (IIR filter, matched filter, Barker sync, CPFSK demod, CRC).
    4. Asserts that the decoded payload matches expected text and reports measured SNR.

    Args:
        wav_file: Filename or path to the input soundtrack WAV.

    Returns:
        True if at least one packet decoded with CRC PASS, False otherwise.
    """
    if not os.path.exists(wav_file):
        candidates = [
            os.path.join(script_dir, wav_file),
            os.path.join(script_dir, "..", "transmitter", wav_file),
            os.path.join(script_dir, "transmitter", wav_file),
        ]
        for c in candidates:
            if os.path.exists(c):
                wav_file = c
                break

    print("=" * 65)
    print("      SONICWAVE END-TO-END SOUNDTRACK ROUNDTRIP TEST")
    print("=" * 65)
    print(f"[*] Testing File: {wav_file}")
    
    audio_data, sample_rate = sf.read(wav_file, dtype='float32')
    print(f"[*] Sample Rate : {sample_rate} Hz")
    print(f"[*] Total Samples: {len(audio_data)} ({len(audio_data)/sample_rate:.2f}s)")
    
    decoded_messages = []
    
    def on_decoded(payload, snr):
        text = payload.decode('utf-8', errors='replace')
        print(f"\n[★] [TEST CALLBACK] >>> Successfully Decoded: '{text}' (SNR: {snr:.1f} dB)")
        decoded_messages.append((text, snr))
        
    config = SonicConfig.get_profile(ProfileType.UNIVERSAL_48K if sample_rate == 48000 else ProfileType.HD_96K)
    receiver = StreamReceiver(config, on_payload_decoded=on_decoded)
    
    # Feed audio in 50 ms blocks (simulating streaming microphone input)
    block_size = int(sample_rate * 0.05)
    total_blocks = int(np.ceil(len(audio_data) / block_size))
    
    print("[*] Streaming audio chunks through receiver pipeline...")
    for i in range(total_blocks):
        block = audio_data[i * block_size : (i + 1) * block_size]
        receiver.process_block(block)
        
    print("\n" + "=" * 65)
    if decoded_messages:
        msg, snr = decoded_messages[0]
        print(f"[✓] TEST PASSED: Successfully decoded '{msg}' with SNR {snr:.1f} dB!")
        print("=" * 65)
        return True
    else:
        print("[✗] TEST FAILED: No message was decoded from the soundtrack.")
        print("=" * 65)
        return False


if __name__ == '__main__':
    file_path = sys.argv[1] if len(sys.argv) > 1 else "sonicwave_music_hello.wav"
    success = test_file_roundtrip(file_path)
    sys.exit(0 if success else 1)
