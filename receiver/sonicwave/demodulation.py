"""
Demodulation and receiver pipeline for SonicWave:
- 8th-order IIR (SOS) Ultrasonic Bandpass Filter
- Matched-Filter Cross-Correlation Chirp Detector
- Non-Coherent 2-FSK Tone Energy Detector
- Streaming Audio Receiver Engine
"""

import numpy as np
from scipy import signal
from typing import Optional, Tuple, List, Callable
from .config import SonicConfig
from .framing import parse_frame
from .modulation import SonicModulator


class UltrasonicBandpassFilter:
    """
    High-order Butterworth IIR Bandpass Filter using Second-Order Sections (SOS)
    for high numerical stability at high frequencies near Nyquist.
    """
    def __init__(self, config: SonicConfig):
        self.config = config
        fs = config.sample_rate
        nyq = 0.5 * fs
        
        low = max(100.0, config.filter_lowcut) / nyq
        high = min(nyq - 100.0, config.filter_highcut) / nyq
        
        self.sos = signal.butter(
            config.filter_order,
            [low, high],
            btype='bandpass',
            output='sos'
        )
        self.zi = signal.sosfilt_zi(self.sos)

    def filter_block(self, audio_block: np.ndarray) -> np.ndarray:
        """Filters an audio chunk maintaining filter state between calls."""
        filtered, self.zi = signal.sosfilt(self.sos, audio_block, zi=self.zi)
        return filtered.astype(np.float32)

    def filter_all(self, audio: np.ndarray) -> np.ndarray:
        """Filters an entire audio buffer."""
        return signal.sosfilt(self.sos, audio).astype(np.float32)


class MatchedFilterDetector:
    """
    Preamble Chirp Detector using Normalized Cross-Correlation.
    """
    def __init__(self, config: SonicConfig):
        self.config = config
        modulator = SonicModulator(config)
        self.ref_chirp = modulator.generate_sync_chirp()
        self.ref_energy = float(np.sum(self.ref_chirp ** 2))
        self.chirp_len = len(self.ref_chirp)
        self.energy_window = np.ones(self.chirp_len, dtype=np.float32)

    def find_peaks(self, filtered_audio: np.ndarray, min_threshold: float = 0.35) -> List[int]:
        """
        Calculates normalized cross-correlation of incoming filtered audio with reference chirp.
        Returns sample indices corresponding to chirp ends.
        """
        if len(filtered_audio) < self.chirp_len:
            return []

        # Cross-correlation via FFT
        corr = signal.fftconvolve(filtered_audio, self.ref_chirp[::-1], mode='valid')
        
        # Local energy of the incoming signal over window of length chirp_len
        local_energy = signal.fftconvolve(filtered_audio ** 2, self.energy_window, mode='valid')
        
        # Normalized cross-correlation coefficient: gamma in [0, 1]
        denom = np.sqrt(np.maximum(local_energy * self.ref_energy, 1e-6))
        norm_corr = np.abs(corr) / denom
        
        # Detect peaks above correlation threshold
        peaks, _ = signal.find_peaks(
            norm_corr,
            height=min_threshold,
            distance=int(self.config.sample_rate * 0.5)  # min 0.5s between packets
        )
        
        # Peak index in 'corr' corresponds to the start of the chirp match in filtered_audio.
        # So the end of the chirp is at peak + chirp_len.
        chirp_end_indices = [int(p + self.chirp_len) for p in peaks]
        return chirp_end_indices


class FSKDemodulator:
    """
    Non-coherent 2-FSK Demodulator using quadrature tone energy integration.
    """
    def __init__(self, config: SonicConfig):
        self.config = config
        self.fs = config.sample_rate
        self.N_sym = int(self.fs * config.symbol_duration_sec)
        
        # Precompute quadrature reference vectors for f0 and f1
        t_sym = np.arange(self.N_sym) / self.fs
        self.cos0 = np.cos(2 * np.pi * config.f0 * t_sym).astype(np.float32)
        self.sin0 = np.sin(2 * np.pi * config.f0 * t_sym).astype(np.float32)
        self.cos1 = np.cos(2 * np.pi * config.f1 * t_sym).astype(np.float32)
        self.sin1 = np.sin(2 * np.pi * config.f1 * t_sym).astype(np.float32)

    def decode_symbol(self, symbol_samples: np.ndarray) -> Tuple[int, float, float]:
        """
        Measures quadrature energy for Tone 0 and Tone 1 in the symbol window.
        Returns: (detected_bit, power_0, power_1)
        """
        if len(symbol_samples) < self.N_sym:
            return 0, 0.0, 0.0

        # Sample around center 80% to avoid transition boundaries
        pad = int(self.N_sym * 0.1)
        samples = symbol_samples[pad : self.N_sym - pad]
        c0 = self.cos0[pad : self.N_sym - pad]
        s0 = self.sin0[pad : self.N_sym - pad]
        c1 = self.cos1[pad : self.N_sym - pad]
        s1 = self.sin1[pad : self.N_sym - pad]

        # Quadrature energy integration: E = (sum(x*cos))^2 + (sum(x*sin))^2
        i0 = np.dot(samples, c0)
        q0 = np.dot(samples, s0)
        power_0 = float(i0 ** 2 + q0 ** 2)

        i1 = np.dot(samples, c1)
        q1 = np.dot(samples, s1)
        power_1 = float(i1 ** 2 + q1 ** 2)

        bit = 1 if power_1 > power_0 else 0
        return bit, power_0, power_1

    def demodulate_stream(
        self, audio: np.ndarray, start_idx: int, max_bits: int = 120
    ) -> Tuple[List[int], float]:
        """
        Decodes a sequence of bits starting from start_idx.
        Returns (decoded_bits, average_snr_db).
        """
        bits = []
        snr_list = []
        curr_idx = start_idx
        
        for _ in range(max_bits):
            if curr_idx + self.N_sym > len(audio):
                break
                
            sym_slice = audio[curr_idx : curr_idx + self.N_sym]
            bit, p0, p1 = self.decode_symbol(sym_slice)
            bits.append(bit)
            
            p_signal = max(p0, p1, 1e-12)
            p_noise = max(min(p0, p1), 1e-12)
            snr_db = 10.0 * np.log10(p_signal / p_noise)
            snr_list.append(snr_db)
            
            curr_idx += self.N_sym

        avg_snr = float(np.mean(snr_list)) if snr_list else 0.0
        return bits, avg_snr


class StreamReceiver:
    """
    Streaming Receiver that ingests live audio blocks from microphone,
    applies bandpass filtering, detects preambles, demodulates packets, and validates CRC.
    """
    def __init__(self, config: SonicConfig, on_payload_decoded: Optional[Callable[[bytes, float], None]] = None):
        self.config = config
        self.on_payload_decoded = on_payload_decoded
        self.filter = UltrasonicBandpassFilter(config)
        self.matched_filter = MatchedFilterDetector(config)
        self.fsk_demod = FSKDemodulator(config)
        
        # Internal circular buffer (keep ~10 seconds of filtered audio)
        self.buf_len = int(config.sample_rate * 10.0)
        self.raw_buffer = np.zeros(self.buf_len, dtype=np.float32)
        self.last_decoded_time_sample = -100000
        self.total_processed_samples = 0

    def process_block(self, block: np.ndarray):
        """Processes a new block of incoming PCM audio."""
        if len(block) == 0:
            return

        # Bandpass filter the new audio chunk
        filtered = self.filter.filter_block(block.flatten())
        block_len = len(filtered)
        self.total_processed_samples += block_len
        
        # Append to circular buffer
        if block_len >= self.buf_len:
            self.raw_buffer = filtered[-self.buf_len:].copy()
        else:
            self.raw_buffer = np.roll(self.raw_buffer, -block_len)
            self.raw_buffer[-block_len:] = filtered

        # Search in recent window (last 9.0 seconds)
        search_samples = min(len(self.raw_buffer), int(self.config.sample_rate * 9.0))
        search_window = self.raw_buffer[-search_samples:]
        peaks = self.matched_filter.find_peaks(search_window)
        
        barker_len = len(self.config.barker_code)
        header_bits_count = barker_len + 8

        for p_idx in peaks:
            gap_samples = int(self.config.sample_rate * 0.02)
            data_start = p_idx + gap_samples
            
            # 1. Need header samples (Barker 13 + Length 8)
            header_samples_needed = data_start + header_bits_count * self.fsk_demod.N_sym
            if len(search_window) < header_samples_needed:
                continue

            # 2. Decode header to check Barker sync and extract payload length
            header_bits, _ = self.fsk_demod.demodulate_stream(
                search_window, data_start, max_bits=header_bits_count
            )
            rec_barker = header_bits[:barker_len]
            exp_barker = [int(b) for b in self.config.barker_code]
            if sum(b != exp for b, exp in zip(rec_barker, exp_barker)) > 3:
                continue

            payload_len = 0
            for b in header_bits[barker_len : barker_len + 8]:
                payload_len = (payload_len << 1) | b

            if payload_len <= 0 or payload_len > 64:
                continue

            # 3. Check if all samples for full packet (Header + Payload + CRC) have arrived
            total_packet_bits = barker_len + 8 + (payload_len * 8) + 16
            full_samples_needed = data_start + total_packet_bits * self.fsk_demod.N_sym
            if len(search_window) < full_samples_needed:
                continue  # Wait for remaining symbols to arrive in subsequent audio blocks

            # Full packet is in buffer! Demodulate and validate CRC
            bits, snr = self.fsk_demod.demodulate_stream(
                search_window, data_start, max_bits=total_packet_bits
            )
            is_valid, payload, msg = parse_frame(bits, self.config)
            
            if is_valid and payload:
                # Debounce: prevent duplicate trigger for the same chirp
                curr_sample_pos = self.total_processed_samples - (len(search_window) - p_idx)
                if abs(curr_sample_pos - self.last_decoded_time_sample) > int(self.config.sample_rate * 1.5):
                    self.last_decoded_time_sample = curr_sample_pos
                    if self.on_payload_decoded:
                        self.on_payload_decoded(payload, snr)
