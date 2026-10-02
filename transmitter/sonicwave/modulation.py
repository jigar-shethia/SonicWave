"""
Modulation engine for SonicWave:
- Linear Frequency Modulated (LFM) Preamble Chirp
- Continuous-Phase 2-FSK with Raised-Cosine / Tukey Pulse Shaping
"""

import numpy as np
from typing import List, Tuple
from .config import SonicConfig
from .framing import build_frame


class SonicModulator:
    def __init__(self, config: SonicConfig):
        self.config = config

    def generate_sync_chirp(self) -> np.ndarray:
        """
        Generates a Linear Frequency Modulated (LFM) up-chirp:
        f(t) = f_start + ((f_end - f_start) / T) * t
        With a smooth Hann taper at the head and tail to eliminate spectral leakage.
        """
        fs = self.config.sample_rate
        T = self.config.chirp_duration_sec
        N = int(fs * T)
        t = np.linspace(0, T, N, endpoint=False)
        
        f0 = self.config.chirp_f_start
        f1 = self.config.chirp_f_end
        
        # Instantaneous phase for linear sweep: phi(t) = 2*pi * (f0*t + ((f1 - f0)/(2*T)) * t^2)
        phase = 2.0 * np.pi * (f0 * t + ((f1 - f0) / (2.0 * T)) * (t ** 2))
        chirp = np.cos(phase).astype(np.float32)
        
        # Apply smooth 5 ms Hann envelope to start and end
        taper_len = int(fs * 0.005)
        if taper_len > 0 and 2 * taper_len < N:
            window = np.hanning(2 * taper_len)
            chirp[:taper_len] *= window[:taper_len]
            chirp[-taper_len:] *= window[taper_len:]
            
        return chirp

    def modulate_bits_fsk(self, bits: List[int]) -> np.ndarray:
        """
        Modulates a sequence of bits using Continuous-Phase Frequency-Shift Keying (CPFSK)
        with smooth symbol transition envelopes to prevent audible clicks.
        Bit 0 -> f0 (e.g. 18.8 kHz)
        Bit 1 -> f1 (e.g. 19.6 kHz)
        """
        fs = self.config.sample_rate
        T_sym = self.config.symbol_duration_sec
        N_sym = int(fs * T_sym)
        
        total_samples = len(bits) * N_sym
        audio = np.zeros(total_samples, dtype=np.float32)
        
        current_phase = 0.0
        two_pi = 2.0 * np.pi
        
        # Create a Tukey/Hann window for smooth symbol transitions if alpha > 0
        alpha = self.config.pulse_shape_alpha
        taper_samples = max(2, int(N_sym * alpha * 0.5))
        sym_envelope = np.ones(N_sym, dtype=np.float32)
        taper = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, taper_samples)))
        sym_envelope[:taper_samples] = taper
        sym_envelope[-taper_samples:] = taper[::-1]
        
        for idx, bit in enumerate(bits):
            freq = self.config.f1 if bit == 1 else self.config.f0
            phase_step = two_pi * freq / fs
            
            # Generate continuous phase samples for this symbol
            sample_indices = np.arange(N_sym)
            symbol_phase = current_phase + phase_step * sample_indices
            
            # Modulate sine and apply anti-click envelope
            symbol_wave = np.cos(symbol_phase).astype(np.float32) * sym_envelope
            
            start_sample = idx * N_sym
            audio[start_sample : start_sample + N_sym] = symbol_wave
            
            # Update carrier phase for the next symbol to ensure phase continuity
            current_phase = (current_phase + phase_step * N_sym) % two_pi
            
        return audio

    def modulate_packet(self, payload: bytes, gap_sec: float = 0.02) -> np.ndarray:
        """
        Generates a complete transmission packet:
        [Preamble Chirp] + [Guard Gap] + [CPFSK Modulated Frame] + [Trailing Silence]
        """
        chirp = self.generate_sync_chirp()
        frame_bits = build_frame(payload, self.config)
        fsk_audio = self.modulate_bits_fsk(frame_bits)
        
        gap_samples = int(self.config.sample_rate * gap_sec)
        gap = np.zeros(gap_samples, dtype=np.float32)
        
        return np.concatenate([chirp, gap, fsk_audio, gap])
