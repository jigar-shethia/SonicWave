"""
Digital Acoustic Modulation Engine for SonicWave Transmitter.

This module converts a stream of discrete binary bits (0s and 1s) into continuous-time
analog acoustic waveform samples ready for speaker playback.

Key Modulation Techniques:
--------------------------
1. Linear Frequency Modulated (LFM) Preamble Chirp:
   A fast upward frequency sweep from 18.5 kHz to 19.9 kHz over 60 milliseconds.
   The receiver correlates incoming audio against this known reference template (matched filter).
   This delivers exceptional processing gain, allowing frame detection even in low-SNR, noisy environments.

2. Continuous-Phase Frequency-Shift Keying (CPFSK):
   Standard FSK abruptly switches frequencies, which creates phase discontinuities:
       cos(2*pi*f0*t) -> cos(2*pi*f1*t)   <-- Phase jump!
   In acoustics, a sudden phase jump creates high-frequency harmonics ("clicks" or "pops")
   that sound like a ticking clock in human audible frequencies.
   CPFSK eliminates this completely by preserving phase continuity across symbol boundaries:
       phi_next = (phi_current + 2*pi * f * N_sym / Fs) mod 2*pi
   Every symbol begins exactly at the instantaneous phase where the preceding symbol ended.

3. Raised-Cosine / Tukey Pulse Shaping:
   A smooth cosine taper is applied to the onset and tail of each symbol period,
   softening transitions and keeping side-lobe spectral energy contained strictly within
   the 18.4 kHz - 20.0 kHz ultrasonic band.
"""

import numpy as np
from typing import List
from .config import SonicConfig
from .framing import build_frame


class SonicModulator:
    """
    Synthesizes ultrasonic acoustic waveforms from digital bitframes.
    """
    def __init__(self, config: SonicConfig):
        """
        Initializes the modulator with a tuned configuration profile.

        Parameters
        ----------
        config : SonicConfig
            Acoustic parameters (sampling rate, carrier frequencies, symbol duration).
        """
        self.config = config

    def generate_sync_chirp(self) -> np.ndarray:
        """
        Synthesizes a Linear Frequency Modulated (LFM) up-chirp preamble.

        Mathematical Formulation:
        --------------------------
        Instantaneous frequency sweeps linearly from f_start to f_end over duration T:
            f(t) = f_start + ((f_end - f_start) / T) * t
        
        The instantaneous phase is the integral of angular frequency:
            phi(t) = 2 * pi * integral(f(tau) dtau) from 0 to t
                   = 2 * pi * [ f_start * t + ((f_end - f_start) / (2 * T)) * t^2 ]
        
        The waveform is:
            s(t) = cos(phi(t))

        Edge Tapering:
        --------------
        To avoid high-frequency clicks when the chirp turns on and off, a 5 ms Hann
        window taper is applied to both edges.

        Returns
        -------
        np.ndarray
            A 1D float32 array containing the synthesized chirp audio samples.
        """
        fs = self.config.sample_rate
        T = self.config.chirp_duration_sec
        N = int(fs * T)  # Total sample count (e.g. 48,000 * 0.060 = 2,880 samples)
        t = np.linspace(0, T, N, endpoint=False)
        
        f0 = self.config.chirp_f_start  # 18,500 Hz
        f1 = self.config.chirp_f_end    # 19,900 Hz
        
        # Calculate instantaneous phase vector
        phase = 2.0 * np.pi * (f0 * t + ((f1 - f0) / (2.0 * T)) * (t ** 2))
        chirp = np.cos(phase).astype(np.float32)
        
        # Apply smooth 5 ms Hann envelope to head and tail to eliminate spectral splatter
        taper_len = int(fs * 0.005)  # 5 ms = 240 samples
        if taper_len > 0 and 2 * taper_len < N:
            window = np.hanning(2 * taper_len)
            chirp[:taper_len] *= window[:taper_len]          # Smooth attack
            chirp[-taper_len:] *= window[taper_len:]         # Smooth release
            
        return chirp

    def modulate_bits_fsk(self, bits: List[int]) -> np.ndarray:
        """
        Modulates a sequence of digital bits into Continuous-Phase 2-FSK audio.

        Frequency Mapping:
        ------------------
        - Bit 0 -> f0 (e.g. 18,800 Hz)
        - Bit 1 -> f1 (e.g. 19,600 Hz)

        Phase Continuity:
        -----------------
        Each symbol has duration T_sym (20 ms = 960 samples at 48 kHz).
        The carrier phase accumulates smoothly from symbol to symbol.

        Pulse Shaping:
        --------------
        A Tukey (cosine) window is multiplied with each symbol's audio samples,
        softening transitions while preserving full energy in the center 70% of the symbol.

        Parameters
        ----------
        bits : List[int]
            List of binary integers (0s and 1s) to transmit.

        Returns
        -------
        np.ndarray
            A 1D float32 array containing the CPFSK modulated audio stream.
        """
        fs = self.config.sample_rate
        T_sym = self.config.symbol_duration_sec  # 0.020 s (20 ms)
        N_sym = int(fs * T_sym)                  # 960 samples per symbol
        
        total_samples = len(bits) * N_sym
        audio = np.zeros(total_samples, dtype=np.float32)
        
        current_phase = 0.0
        two_pi = 2.0 * np.pi
        
        # Precompute Tukey/Hann window for smooth intra-symbol pulse shaping
        alpha = self.config.pulse_shape_alpha  # 0.35
        taper_samples = max(2, int(N_sym * alpha * 0.5))
        sym_envelope = np.ones(N_sym, dtype=np.float32)
        taper = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, taper_samples)))
        sym_envelope[:taper_samples] = taper
        sym_envelope[-taper_samples:] = taper[::-1]
        
        # Modulate symbol by symbol
        for idx, bit in enumerate(bits):
            # Select tone frequency based on bit value
            freq = self.config.f1 if bit == 1 else self.config.f0
            phase_step = two_pi * freq / fs
            
            # Generate sample indices for this symbol: [0, 1, 2, ..., N_sym - 1]
            sample_indices = np.arange(N_sym)
            symbol_phase = current_phase + phase_step * sample_indices
            
            # Synthesize cosine waveform and shape with anti-click envelope
            symbol_wave = np.cos(symbol_phase).astype(np.float32) * sym_envelope
            
            # Write to output audio buffer
            start_sample = idx * N_sym
            audio[start_sample : start_sample + N_sym] = symbol_wave
            
            # Preserve phase continuity: the starting phase of the NEXT symbol
            # equals the final instantaneous phase of the CURRENT symbol.
            current_phase = (current_phase + phase_step * N_sym) % two_pi
            
        return audio

    def modulate_packet(self, payload: bytes, gap_sec: float = 0.02) -> np.ndarray:
        """
        Assembles and modulates a complete acoustic transmission packet:

        Packet Timeline:
        ----------------
        [ Preamble Chirp ] ---> [ Guard Gap ] ---> [ CPFSK Data Frame ] ---> [ Post-Gap ]
           (60 ms LFM)            (20 ms silence)     (Barker + Len + Data)     (20 ms silence)

        Parameters
        ----------
        payload : bytes
            Raw message bytes (e.g. b"Hello world").
        gap_sec : float, optional
            Duration of silence guard intervals in seconds (default: 0.02s = 20 ms).

        Returns
        -------
        np.ndarray
            A single contiguous 1D float32 audio array containing the complete ultrasonic burst.
        """
        # 1. Synthesize 60 ms synchronization chirp
        chirp = self.generate_sync_chirp()
        
        # 2. Build serialized digital bitframe (Barker + Length + Payload + CRC16)
        frame_bits = build_frame(payload, self.config)
        
        # 3. Modulate bitframe into Continuous-Phase 2-FSK audio
        fsk_audio = self.modulate_bits_fsk(frame_bits)
        
        # 4. Synthesize silence guard intervals (prevents acoustic multipath echo overlap)
        gap_samples = int(self.config.sample_rate * gap_sec)
        gap = np.zeros(gap_samples, dtype=np.float32)
        
        # 5. Concatenate all elements into a single contiguous transmission burst
        return np.concatenate([chirp, gap, fsk_audio, gap])
