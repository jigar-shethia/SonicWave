"""
Audio mixing, normalizer, and music synthesizer for SonicWave.
"""

import numpy as np
from .config import SonicConfig


def generate_ambient_music_sample(duration_sec: float = 10.0, sample_rate: int = 48000) -> np.ndarray:
    """
    Generates a pleasant, lush ambient chord progression (Cmaj9 - Am9 - Fmaj7 - Gsus4)
    with soft harmonic overtone decays in the 100 Hz - 8 kHz range to simulate a real song.
    """
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    music = np.zeros_like(t, dtype=np.float32)
    
    # 4 chords over duration
    chord_len = duration_sec / 4.0
    chords = [
        [130.81, 164.81, 196.00, 246.94, 293.66],  # Cmaj9 (C3, E3, G3, B3, D4)
        [110.00, 130.81, 164.81, 196.00, 220.00],  # Am9   (A2, C3, E3, G3, A3)
        [87.31,  110.00, 130.81, 174.61, 220.00],  # Fmaj7 (F2, A2, C3, F3, A3)
        [98.00,  146.83, 196.00, 261.63, 293.66],  # Gsus4 (G2, D3, G3, C4, D4)
    ]
    
    for i, chord_freqs in enumerate(chords):
        t_start = i * chord_len
        t_end = (i + 1) * chord_len
        mask = (t >= t_start) & (t < t_end)
        t_seg = t[mask] - t_start
        
        # Segment envelope (gentle attack, sustain, soft release)
        seg_samples = len(t_seg)
        env = np.ones(seg_samples, dtype=np.float32)
        attack_len = int(sample_rate * 0.3)
        decay_len = int(sample_rate * 0.4)
        if seg_samples > attack_len + decay_len:
            env[:attack_len] = np.linspace(0, 1, attack_len)
            env[-decay_len:] = np.linspace(1, 0, decay_len)
            
        chord_wave = np.zeros(seg_samples, dtype=np.float32)
        for freq in chord_freqs:
            # Fundamental + 2nd + 3rd harmonics
            chord_wave += 0.5 * np.sin(2 * np.pi * freq * t_seg)
            chord_wave += 0.25 * np.sin(2 * np.pi * (freq * 2) * t_seg)
            chord_wave += 0.12 * np.sin(2 * np.pi * (freq * 3) * t_seg)
            
        music[mask] += (chord_wave * env) / len(chord_freqs)
        
    # Soft low-pass feel: normalize peak to -3 dBFS (0.7)
    peak = np.max(np.abs(music))
    if peak > 0:
        music = (music / peak) * 0.7
        
    return music.astype(np.float32)


def mix_music_and_data(
    music: np.ndarray,
    ultrasonic_data: np.ndarray,
    config: SonicConfig,
    offset_sec: float = 1.0,
) -> np.ndarray:
    """
    Layers ultrasonic data onto a music track with configurable attenuation (e.g. -20 dB)
    and applies soft-knee peak limiting to guarantee zero DAC digital clipping.
    """
    fs = config.sample_rate
    offset_samples = int(offset_sec * fs)
    
    # Ensure music is long enough to hold the data packet
    required_len = offset_samples + len(ultrasonic_data) + int(fs * 0.5)
    if len(music) < required_len:
        # Repeat or pad music
        repeats = int(np.ceil(required_len / len(music)))
        music = np.tile(music, repeats)[:required_len]
        
    mixed = music.copy().astype(np.float32)
    
    # Calculate linear gain from dB
    gain_linear = 10.0 ** (config.ultrasonic_gain_db / 20.0)
    data_scaled = ultrasonic_data * gain_linear
    
    end_samples = offset_samples + len(data_scaled)
    mixed[offset_samples:end_samples] += data_scaled
    
    # Soft-knee limiter / peak normalization to prevent clipping (|x| <= config.peak_limit)
    peak = np.max(np.abs(mixed))
    if peak > config.peak_limit:
        mixed = (mixed / peak) * config.peak_limit
        
    return mixed
