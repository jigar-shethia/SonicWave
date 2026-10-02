#!/usr/bin/env python3
"""
SonicWave Audio Transmitter
Plays the composite soundtrack (Music + Ultrasonic 'HELLO') through the speakers.
"""

import argparse
import time
import os
import sys

# Ensure script dir and root are in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import numpy as np
import soundfile as sf
import sounddevice as sd


def play_soundtrack(file_path: str = "sonicwave_music_hello.wav", loop: bool = False, loop_delay: float = 2.0):
    if not os.path.isabs(file_path):
        if not os.path.exists(file_path) and os.path.exists(os.path.join(script_dir, file_path)):
            file_path = os.path.join(script_dir, file_path)

    if not os.path.exists(file_path):
        print(f"[!] Error: Soundtrack file '{file_path}' not found.")
        print("    Please run 'python generate_soundtrack.py' first.")
        sys.exit(1)

    audio_data, sample_rate = sf.read(file_path, dtype='float32')
    duration = len(audio_data) / sample_rate
    
    print("=" * 65)
    print("             SONICWAVE AUDIO TRANSMITTER")
    print("=" * 65)
    print(f"[*] Playing File: {file_path}")
    print(f"[*] Sample Rate : {sample_rate} Hz")
    print(f"[*] Duration    : {duration:.2f} seconds")
    print(f"[*] Loop Mode   : {'ON (Repeat every ' + str(loop_delay) + 's)' if loop else 'OFF (Single Shot)'}")
    print(f"[*] Audio Device: {sd.query_devices(kind='output')['name']}")
    print("=" * 65)
    
    iteration = 1
    try:
        while True:
            print(f"\n[▶] [Burst #{iteration}] Transmitting Soundtrack...")
            sd.play(audio_data, sample_rate)
            
            # Simple progress display
            start_time = time.time()
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                pct = min(100, int((elapsed / duration) * 100))
                bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
                sys.stdout.write(f"\r    Progress: [{bar}] {pct}% ({elapsed:.1f}s / {duration:.1f}s)")
                sys.stdout.flush()
                time.sleep(0.1)
                
            sd.wait()
            sys.stdout.write("\r    Progress: [████████████████████] 100% [COMPLETE]\n")
            sys.stdout.flush()
            print(f"[✓] [Burst #{iteration}] Finished playback.")
            
            if not loop:
                break
                
            iteration += 1
            print(f"[...] Waiting {loop_delay:.1f}s before next transmission...")
            time.sleep(loop_delay)
            
    except KeyboardInterrupt:
        sd.stop()
        print("\n[!] Transmission stopped by user.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SonicWave Audio Transmitter")
    parser.add_argument("--file", type=str, default="sonicwave_music_hello.wav", help="Soundtrack WAV file to play")
    parser.add_argument("--loop", action="store_true", help="Loop playback continuously")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between loops in seconds")
    args = parser.parse_args()
    
    play_soundtrack(file_path=args.file, loop=args.loop, loop_delay=args.delay)
