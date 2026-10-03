#!/usr/bin/env python3
"""
SonicWave Interactive Terminal Transmitter (REPL)
Allows instant, conversational acoustic data transmission by simply typing text.
"""

import os
import sys
import time
import readline  # Enables command history, up/down arrows, and line editing

# Ensure script dir and root are in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import numpy as np
import sounddevice as sd

from sonicwave.config import SonicConfig, ProfileType
from sonicwave.modulation import SonicModulator
from sonicwave.mixer import generate_ambient_music_sample, mix_music_and_data


class InteractiveTransmitter:
    def __init__(self, profile_type: ProfileType = ProfileType.UNIVERSAL_48K, gain_db: float = -20.0):
        self.config = SonicConfig.get_profile(profile_type)
        self.config.ultrasonic_gain_db = gain_db
        self.modulator = SonicModulator(self.config)
        self.history = []
        self.is_looping = False
        
        # Pre-generate 12s ambient music buffer to make transmission instantaneous
        print("[*] Pre-synthesizing ambient music carrier...")
        self.ambient_music = generate_ambient_music_sample(duration_sec=12.0, sample_rate=self.config.sample_rate)
        dev_name = sd.query_devices(kind='output')['name']
        print(f"[*] Audio Output: {dev_name}")
        print(f"[*] Ultrasonic Carrier: {self.config.carrier_freq:.0f} Hz (Gain: {self.config.ultrasonic_gain_db:.1f} dB)")

    def transmit_text(self, text: str, loop: bool = False, delay_sec: float = 2.0):
        """Modulates text and plays through speakers."""
        if not text.strip():
            return
            
        payload_bytes = text.encode('utf-8')
        if len(payload_bytes) > 255:
            print(f"[!] Error: Text exceeds 255 bytes limit ({len(payload_bytes)} bytes)")
            return

        # 1. Modulate ultrasonic packet
        ultrasonic_audio = self.modulator.modulate_packet(payload_bytes)
        burst_duration = len(ultrasonic_audio) / self.config.sample_rate
        
        # 2. Mix with ambient music
        mixed_audio = mix_music_and_data(self.ambient_music, ultrasonic_audio, self.config, offset_sec=1.0)
        total_duration = len(mixed_audio) / self.config.sample_rate
        
        # Save to history
        if text not in self.history:
            self.history.append(text)
            
        iteration = 1
        try:
            while True:
                prefix = f"[▶] [Loop #{iteration}] " if loop else "[▶] "
                print(f"{prefix}Transmitting \"{text}\" ({len(payload_bytes)} bytes, burst: {burst_duration:.2f}s, total: {total_duration:.2f}s)...")
                
                sd.play(mixed_audio, self.config.sample_rate)
                
                # Visual progress bar
                start_time = time.time()
                while time.time() - start_time < total_duration:
                    elapsed = time.time() - start_time
                    pct = min(100, int((elapsed / total_duration) * 100))
                    bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
                    sys.stdout.write(f"\r    Progress: [{bar}] {pct}% ({elapsed:.1f}s / {total_duration:.1f}s)")
                    sys.stdout.flush()
                    time.sleep(0.08)
                    
                sd.wait()
                sys.stdout.write("\r    Progress: [████████████████████] 100% [TRANSMITTED]       \n")
                sys.stdout.flush()
                
                if not loop:
                    break
                    
                iteration += 1
                print(f"[...] Waiting {delay_sec:.1f}s before next transmission (Ctrl+C to stop loop)...")
                time.sleep(delay_sec)
                
        except KeyboardInterrupt:
            sd.stop()
            print("\n[!] Playback stopped by user.")


def run_repl():
    print("=" * 65)
    print("           SONICWAVE INTERACTIVE TRANSMITTER")
    print("=" * 65)
    print("Type any message and press [Enter] to transmit silently.")
    print("Special Commands:")
    print("  :loop <text>   - Transmit continuously on loop (Ctrl+C to break)")
    print("  :gain <dB>     - Change ultrasonic volume (e.g. :gain -15)")
    print("  :history       - View sent messages")
    print("  :exit or :q    - Quit")
    print("=" * 65)
    
    tx = InteractiveTransmitter()
    print("\nReady! Type your message below:")
    
    while True:
        try:
            line = input("\nSonicWave TX > ").strip()
            if not line:
                continue
                
            if line in (":exit", ":quit", ":q", "exit", "quit"):
                print("Goodbye!")
                break
                
            elif line.startswith(":loop "):
                text = line[6:].strip()
                if text:
                    tx.transmit_text(text, loop=True, delay_sec=2.5)
                    
            elif line.startswith(":gain "):
                try:
                    val = float(line[6:].strip())
                    tx.config.ultrasonic_gain_db = val
                    print(f"[*] Ultrasonic gain set to {val:.1f} dB")
                except ValueError:
                    print("[!] Invalid gain value. Example: :gain -18.0")
                    
            elif line in (":history", ":h"):
                print("\n--- Recent Messages ---")
                for i, msg in enumerate(tx.history[-10:], 1):
                    print(f"  {i}. {msg}")
                    
            elif line.startswith(":"):
                print(f"[!] Unknown command '{line}'. Type any text directly to transmit.")
                
            else:
                # Direct message transmission
                tx.transmit_text(line, loop=False)
                
        except (KeyboardInterrupt, EOFError):
            print("\nExiting SonicWave Interactive Transmitter.")
            break


if __name__ == '__main__':
    run_repl()
