#!/usr/bin/env python3
"""
SonicWave Microphone Receiver
Listens continuously via the microphone, isolates the ultrasonic channel,
and decodes the payload, printing 'HELLO' in the console.
"""

import argparse
import os
import sys
import time
import datetime

# Ensure script dir and root are in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import numpy as np
import sounddevice as sd

from sonicwave.config import SonicConfig, ProfileType
from sonicwave.demodulation import StreamReceiver


def on_message_decoded(payload_bytes: bytes, snr_db: float):
    """
    Callback triggered whenever a complete packet is successfully demodulated
    and passes 16-bit CRC validation.

    Prints a formatted reception banner showing:
    - Current local timestamp (millisecond precision).
    - Decoded UTF-8 text message.
    - Measured Signal-to-Noise Ratio (SNR) in dB.
    - Payload size in bytes.

    Args:
        payload_bytes: Verified binary payload extracted from packet.
        snr_db: Average signal-to-noise ratio across all demodulated symbols.
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    try:
        decoded_text = payload_bytes.decode('utf-8')
    except UnicodeDecodeError:
        decoded_text = repr(payload_bytes)
        
    print("\n" + "=" * 70)
    print(f" [★] [SonicWave RX] [{timestamp}] >>> DECODED MESSAGE: \"{decoded_text}\"")
    print(f"     Status: CRC-16 PASS  |  SNR: {snr_db:.1f} dB  |  Bytes: {len(payload_bytes)}")
    print("=" * 70 + "\n")


def run_listener(profile_type: ProfileType = ProfileType.UNIVERSAL_48K, device_index=None):
    """
    Initializes and runs the live continuous microphone listener loop.

    1. Loads acoustic profile configuration (48 kHz / 96 kHz).
    2. Instantiates StreamReceiver with bandpass filtering and matched filter.
    3. Opens a sounddevice InputStream with 50 ms buffer callback blocks.
    4. Computes real-time ultrasonic band RMS energy and renders an animated ASCII VU meter.
    5. Gracefully handles Ctrl+C to terminate cleanly without audio driver hangs.

    Args:
        profile_type: Selected ProfileType (UNIVERSAL_48K or HD_96K).
        device_index: Optional integer audio input device index (default: system default mic).
    """
    config = SonicConfig.get_profile(profile_type)
    receiver = StreamReceiver(config, on_payload_decoded=on_message_decoded)
    
    print("=" * 70)
    print("               SONICWAVE MICROPHONE RECEIVER")
    print("=" * 70)
    print(f"[*] Profile           : {profile_type.value}")
    print(f"[*] Sample Rate       : {config.sample_rate} Hz")
    print(f"[*] Ultrasonic Band   : {config.filter_lowcut:.0f} Hz - {config.filter_highcut:.0f} Hz")
    print(f"[*] Carrier Frequency : {config.carrier_freq:.0f} Hz")
    
    dev_info = sd.query_devices(device=device_index, kind='input')
    print(f"[*] Microphone Device : {dev_info['name']}")
    print("=" * 70)
    print("[*] Listening for ultrasonic transmissions... (Press Ctrl+C to stop)\n")
    
    block_size = int(config.sample_rate * 0.05)  # 50 ms chunks (2400 samples)
    
    last_print = time.time()
    
    def audio_callback(indata, frames, time_info, status):
        if status:
            pass  # Overflow/underflow flag
        receiver.process_block(indata[:, 0])
        
    try:
        with sd.InputStream(
            device=device_index,
            channels=1,
            samplerate=config.sample_rate,
            blocksize=block_size,
            dtype='float32',
            callback=audio_callback
        ):
            spinner = ['|', '/', '-', '\\']
            spin_idx = 0
            while True:
                time.sleep(0.2)
                # Compute instantaneous RMS energy of recent filtered buffer
                rms = np.sqrt(np.mean(receiver.raw_buffer[-block_size:] ** 2))
                rms_db = 20 * np.log10(max(rms, 1e-6))
                
                # Visual level bar
                bar_len = min(20, max(0, int((rms_db + 60) / 3)))
                vu_bar = "█" * bar_len + "░" * (20 - bar_len)
                
                spin_idx = (spin_idx + 1) % len(spinner)
                sys.stdout.write(
                    f"\r[{spinner[spin_idx]}] Listening... [Ultrasonic Band Level: {rms_db:5.1f} dBFS |{vu_bar}|]"
                )
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("\n\n[!] Receiver stopped by user.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SonicWave Microphone Receiver")
    parser.add_argument("--profile", type=str, choices=["48k", "96k"], default="48k", help="Audio profile (48k or 96k)")
    parser.add_argument("--device", type=int, default=None, help="Input device index (optional)")
    args = parser.parse_args()
    
    profile = ProfileType.UNIVERSAL_48K if args.profile == "48k" else ProfileType.HD_96K
    run_listener(profile_type=profile, device_index=args.device)
