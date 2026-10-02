"""
Configuration parameters and profiles for SonicWave.
"""

from dataclasses import dataclass
from enum import Enum


class ProfileType(Enum):
    UNIVERSAL_48K = "universal_48k"  # 19.2 kHz carrier @ 48 kHz Fs (iPhone/Mac compatible)
    HD_96K = "hd_96k"                # 24.0 kHz carrier @ 96 kHz Fs (HD Pro audio)


@dataclass
class SonicConfig:
    sample_rate: int = 48000
    carrier_freq: float = 19200.0        # Center frequency in Hz
    
    # 2-FSK Tone frequencies
    f0: float = 18800.0                 # Bit 0 frequency in Hz
    f1: float = 19600.0                 # Bit 1 frequency in Hz
    
    # Timing & Modulation
    symbol_duration_sec: float = 0.020  # 20 ms per symbol (50 baud/bps)
    pulse_shape_alpha: float = 0.35     # Raised Cosine roll-off factor
    
    # Preamble Chirp
    chirp_duration_sec: float = 0.060   # 60 ms linear frequency up-chirp
    chirp_f_start: float = 18500.0      # Start of sweep in Hz
    chirp_f_end: float = 19900.0        # End of sweep in Hz
    
    # Framing & Barker Sync
    barker_code: str = "1111100110101"  # 13-bit Barker sequence
    
    # Receiver Bandpass Filter
    filter_lowcut: float = 18400.0      # Bandpass lower cutoff in Hz
    filter_highcut: float = 20000.0     # Bandpass upper cutoff in Hz
    filter_order: int = 6               # Butterworth order (SOS)
    
    # Gain & Mixing
    ultrasonic_gain_db: float = -20.0   # Relative gain for ultrasonic channel in music mix
    peak_limit: float = 0.95            # Max output amplitude before soft limiting

    @classmethod
    def get_profile(cls, profile: ProfileType = ProfileType.UNIVERSAL_48K) -> "SonicConfig":
        if profile == ProfileType.UNIVERSAL_48K:
            return cls(
                sample_rate=48000,
                carrier_freq=19200.0,
                f0=18800.0,
                f1=19600.0,
                symbol_duration_sec=0.020,
                pulse_shape_alpha=0.35,
                chirp_duration_sec=0.060,
                chirp_f_start=18500.0,
                chirp_f_end=19900.0,
                filter_lowcut=18400.0,
                filter_highcut=20000.0,
                filter_order=6,
                ultrasonic_gain_db=-20.0,
            )
        elif profile == ProfileType.HD_96K:
            return cls(
                sample_rate=96000,
                carrier_freq=24000.0,
                f0=23500.0,
                f1=24500.0,
                symbol_duration_sec=0.015,
                pulse_shape_alpha=0.35,
                chirp_duration_sec=0.060,
                chirp_f_start=23000.0,
                chirp_f_end=25000.0,
                filter_lowcut=22800.0,
                filter_highcut=25200.0,
                filter_order=6,
                ultrasonic_gain_db=-20.0,
            )
        else:
            raise ValueError(f"Unknown profile: {profile}")
