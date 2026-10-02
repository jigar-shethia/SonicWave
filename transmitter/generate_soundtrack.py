#!/usr/bin/env python3
"""
SonicWave Soundtrack Generator
Generates a composite soundtrack WAV file (Normal Music + Ultrasonic 'HELLO')
and exports diagnostic spectrum plots.
"""

import argparse
import os
import sys

# Ensure script dir and root are in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

from sonicwave.config import SonicConfig, ProfileType
from sonicwave.modulation import SonicModulator
from sonicwave.mixer import generate_ambient_music_sample, mix_music_and_data


def generate_soundtrack(
    payload_str: str = "Hello",
    music_file: str = None,
    output_file: str = "sonicwave_music_hello.wav",
    profile_type: ProfileType = ProfileType.UNIVERSAL_48K,
    ultrasonic_gain_db: float = -20.0,
    offset_sec: float = 1.0,
    plot_spectrum: bool = True,
):
    """
    Orchestrates the entire acoustic transmission soundtrack generation workflow.

    Workflow Stages:
    ----------------
    1. Configuration Setup: Loads hardware sample rate (48 kHz) and 2-FSK frequencies (18.8/19.6 kHz).
    2. Digital Modulation: Serializes the payload text into bits, appends Barker code & CRC-16,
       and synthesizes the continuous-phase 2-FSK acoustic waveform preceded by the LFM sync chirp.
    3. Music Sourcing: Synthesizes a soothing ambient chord progression (or reads an external WAV).
    4. Audio Mixing: Attenuates the ultrasonic burst by -20 dB and blends it into the music.
    5. Export: Saves high-resolution 24-bit PCM audio WAV files and generates an FFT diagnostic plot.

    Parameters
    ----------
    payload_str : str, optional
        The secret text message to transmit silently (default: "Hello").
    music_file : str, optional
        Optional path to a custom background music WAV file. If None, ambient chords are synthesized.
    output_file : str, optional
        Target filename for the generated composite soundtrack WAV.
    profile_type : ProfileType, optional
        Audio profile: UNIVERSAL_48K (48 kHz Fs) or HD_96K (96 kHz Fs).
    ultrasonic_gain_db : float, optional
        Ultrasonic signal attenuation relative to music in dB (default: -20.0 dB).
    offset_sec : float, optional
        Lead-in delay in seconds before ultrasonic data starts (default: 1.0s).
    plot_spectrum : bool, optional
        If True, generates a frequency spectrum verification PNG plot.
    """
    if not os.path.isabs(output_file):
        output_file = os.path.join(script_dir, output_file)
    print("=" * 65)
    print("           SONICWAVE SOUNDTRACK GENERATOR")
    print("=" * 65)
    
    # Load profile configuration and apply custom ultrasonic gain
    config = SonicConfig.get_profile(profile_type)
    config.ultrasonic_gain_db = ultrasonic_gain_db
    
    # Encode message text into UTF-8 bytes
    payload_bytes = payload_str.encode('utf-8')
    print(f"[*] Payload: '{payload_str}' ({len(payload_bytes)} bytes)")
    print(f"[*] Profile: {profile_type.value} | Sample Rate: {config.sample_rate} Hz")
    print(f"[*] Ultrasonic Carrier: {config.carrier_freq} Hz (2-FSK: {config.f0} Hz / {config.f1} Hz)")
    print(f"[*] Ultrasonic Gain: {config.ultrasonic_gain_db:.1f} dB")
    
    # -------------------------------------------------------------------------
    # 1. Modulate payload text into ultrasonic acoustic packet
    # -------------------------------------------------------------------------
    modulator = SonicModulator(config)
    ultrasonic_audio = modulator.modulate_packet(payload_bytes)
    data_duration = len(ultrasonic_audio) / config.sample_rate
    print(f"[+] Modulated ultrasonic burst: {len(ultrasonic_audio)} samples ({data_duration:.2f}s)")
    
    # -------------------------------------------------------------------------
    # 2. Source background music (synthesize ambient chord or load user file)
    # -------------------------------------------------------------------------
    if music_file and os.path.exists(music_file):
        print(f"[*] Loading input music file: {music_file}")
        music_audio, fs_music = sf.read(music_file, dtype='float32')
        if music_audio.ndim > 1:
            music_audio = np.mean(music_audio, axis=1)  # Convert stereo to mono
        if fs_music != config.sample_rate:
            print(f"[!] Warning: resampling music from {fs_music} Hz to {config.sample_rate} Hz")
            from scipy import signal
            num_samples = int(len(music_audio) * config.sample_rate / fs_music)
            music_audio = signal.resample(music_audio, num_samples)
    else:
        # Dynamically calculate track duration to comfortably enclose the entire packet
        duration_sec = max(6.0, offset_sec + data_duration + 2.0)
        print(f"[*] Synthesizing lush ambient music track ({duration_sec:.1f}s)...")
        music_audio = generate_ambient_music_sample(duration_sec=duration_sec, sample_rate=config.sample_rate)
        
    # -------------------------------------------------------------------------
    # 3. Layer music and ultrasonic data together with soft-knee limiting
    # -------------------------------------------------------------------------
    mixed_audio = mix_music_and_data(music_audio, ultrasonic_audio, config, offset_sec=offset_sec)
    total_duration = len(mixed_audio) / config.sample_rate
    
    # 4. Export WAV file
    sf.write(output_file, mixed_audio, config.sample_rate, subtype='PCM_24')
    print(f"[✓] Successfully exported composite soundtrack: {output_file}")
    print(f"    - Duration: {total_duration:.2f}s")
    print(f"    - Sample Rate: {config.sample_rate} Hz (24-bit PCM)")
    print(f"    - Peak Amplitude: {np.max(np.abs(mixed_audio)):.2f} (No Clipping)")
    
    # Export isolated ultrasonic track as well
    isolated_file = output_file.replace(".wav", "_ultrasonic_only.wav")
    sf.write(isolated_file, ultrasonic_audio, config.sample_rate, subtype='PCM_24')
    print(f"[✓] Exported isolated ultrasonic track: {isolated_file}")
    
    # 5. Generate Spectrum Verification Plot
    if plot_spectrum:
        plot_file = output_file.replace(".wav", "_spectrum.png")
        print(f"[*] Generating FFT Spectrum Plot: {plot_file}")
        
        plt.figure(figsize=(10, 6))
        
        # Compute FFT of mixed audio in the transmission region
        start_idx = int(offset_sec * config.sample_rate)
        end_idx = start_idx + len(ultrasonic_audio)
        segment = mixed_audio[start_idx:end_idx]
        
        n_fft = 4096
        freqs = np.fft.rfftfreq(n_fft, 1.0 / config.sample_rate)
        fft_vals = np.abs(np.fft.rfft(segment[:n_fft] * np.hanning(n_fft)))
        fft_db = 20 * np.log10(np.maximum(fft_vals, 1e-6))
        fft_db -= np.max(fft_db)  # Normalize to 0 dB peak
        
        plt.plot(freqs / 1000.0, fft_db, color='#1E88E5', lw=1.5, label='Composite Audio Spectrum')
        plt.axvspan(0.02, 16.0, alpha=0.15, color='green', label='Audible Music Range (20 Hz - 16 kHz)')
        plt.axvspan(config.filter_lowcut / 1000.0, config.filter_highcut / 1000.0, alpha=0.25, color='red', label=f'Ultrasonic Data Band ({config.carrier_freq/1000.0:.1f} kHz)')
        
        plt.title(f"SonicWave Audio Spectrum: Normal Music + Silent Ultrasonic '{payload_str}'", fontsize=12, pad=12)
        plt.xlabel("Frequency (kHz)", fontsize=11)
        plt.ylabel("Normalized Power (dB)", fontsize=11)
        plt.xlim(0, config.sample_rate / 2000.0)
        plt.ylim(-70, 5)
        plt.grid(True, alpha=0.3, ls='--')
        plt.legend(loc='upper right', framealpha=0.9)
        plt.tight_layout()
        plt.savefig(plot_file, dpi=150)
        plt.close()
        print(f"[✓] Spectrum verification plot saved: {plot_file}")

    print("=" * 65)
    print("Soundtrack is ready to play! Run 'python transmit.py' or open in QuickTime.")
    print("=" * 65)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SonicWave Ultrasonic Soundtrack Generator")
    parser.add_argument("--payload", type=str, default="Hello", help="Text payload to encode (default: 'Hello')")
    parser.add_argument("--music", type=str, default=None, help="Optional background music WAV file")
    parser.add_argument("--output", type=str, default="sonicwave_music_hello.wav", help="Output WAV filename")
    parser.add_argument("--gain", type=float, default=-20.0, help="Ultrasonic gain in dB relative to music (default: -20.0 dB)")
    parser.add_argument("--profile", type=str, choices=["48k", "96k"], default="48k", help="Audio profile (48k universal or 96k HD)")
    
    args = parser.parse_args()
    profile = ProfileType.UNIVERSAL_48K if args.profile == "48k" else ProfileType.HD_96K
    
    generate_soundtrack(
        payload_str=args.payload,
        music_file=args.music,
        output_file=args.output,
        profile_type=profile,
        ultrasonic_gain_db=args.gain,
    )
