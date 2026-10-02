"""
Configuration parameters and acoustic profiles for SonicWave.

This module defines all physical and digital signal processing (DSP) constants
used to transmit and receive data over acoustic sound waves.

Why Ultrasonic / 19.2 kHz?
---------------------------
- Standard human adult hearing drops off sharply above ~16 kHz - 17 kHz.
- Standard consumer microphones (smartphones, laptops) and DACs operate at 48 kHz sampling rate.
- According to the Nyquist-Shannon Sampling Theorem, a 48 kHz sampling rate can capture
  frequencies up to Nyquist = Fs / 2 = 24.0 kHz.
- Hardware anti-aliasing low-pass analog filters in iPhones roll off between 20.5 kHz - 22 kHz.
- Therefore, a center carrier at 19.2 kHz (with tones at 18.8 kHz and 19.6 kHz) lies
  in the "sweet spot": completely silent to adult human ears, yet perfectly within the
  linear capture range of iPhone microphones and MacBook Pro speakers without requiring
  special hardware.
"""

from dataclasses import dataclass
from enum import Enum


class ProfileType(Enum):
    """
    Supported audio hardware profiles.
    - UNIVERSAL_48K: Standard 48 kHz sampling rate. Compatible with all iOS devices,
      Macs, PCs, and standard soundcards. Carrier frequency: 19.2 kHz.
    - HD_96K: High-Definition 96 kHz sampling rate for pro-audio hardware capable of
      higher frequency reproduction. Carrier frequency: 24.0 kHz.
    """
    UNIVERSAL_48K = "universal_48k"
    HD_96K = "hd_96k"


@dataclass
class SonicConfig:
    """
    Acoustic and Modulation Parameters for SonicWave Transmitter & Receiver.
    """
    # -------------------------------------------------------------------------
    # 1. Hardware Sampling & Carrier Frequencies
    # -------------------------------------------------------------------------
    sample_rate: int = 48000
    """Audio sampling rate in Hertz (48,000 samples per second)."""

    carrier_freq: float = 19200.0
    """Center ultrasonic carrier frequency in Hz (silent to humans)."""

    # -------------------------------------------------------------------------
    # 2. 2-FSK (Frequency-Shift Keying) Tone Definitions
    # -------------------------------------------------------------------------
    f0: float = 18800.0
    """Tone frequency representing digital binary 0 (18.8 kHz)."""

    f1: float = 19600.0
    """Tone frequency representing digital binary 1 (19.6 kHz)."""

    # Tone separation: Delta_f = f1 - f0 = 800 Hz.
    # At a baud rate of 50 symbols/sec (T = 20 ms), the minimum orthogonal tone
    # spacing for non-coherent detection is 1/T = 50 Hz.
    # 800 Hz provides substantial margin against acoustic multipath Doppler spread and jitter.

    # -------------------------------------------------------------------------
    # 3. Symbol Timing & Pulse Shaping
    # -------------------------------------------------------------------------
    symbol_duration_sec: float = 0.020
    """Duration of one bit symbol in seconds (0.020s = 20 ms, yielding 50 bits/second)."""

    pulse_shape_alpha: float = 0.35
    """
    Roll-off factor for the Raised-Cosine / Tukey transition window.
    Softens sharp phase/amplitude transitions between consecutive symbols,
    preventing high-frequency spectral splatter that causes audible clicking.
    """

    # -------------------------------------------------------------------------
    # 4. Synchronization Preamble (Linear Frequency Modulation / Chirp)
    # -------------------------------------------------------------------------
    chirp_duration_sec: float = 0.060
    """Duration of the synchronization up-chirp (60 ms = 2,880 samples at 48 kHz)."""

    chirp_f_start: float = 18500.0
    """Starting frequency of the preamble chirp in Hz."""

    chirp_f_end: float = 19900.0
    """Ending frequency of the preamble chirp in Hz (sweeps upward across 1.4 kHz)."""

    # -------------------------------------------------------------------------
    # 5. Frame Synchronization Code
    # -------------------------------------------------------------------------
    barker_code: str = "1111100110101"
    """
    13-bit Barker sequence.
    Barker codes have optimal mathematical autocorrelation properties: the peak
    correlation is 13, while all side-lobes are <= 1. This prevents false frame locks.
    """

    # -------------------------------------------------------------------------
    # 6. Filtering & Bandpass Boundaries
    # -------------------------------------------------------------------------
    filter_lowcut: float = 18400.0
    """Lower cutoff frequency in Hz for the ultrasonic bandpass filter."""

    filter_highcut: float = 20000.0
    """Upper cutoff frequency in Hz for the ultrasonic bandpass filter."""

    filter_order: int = 6
    """Order of the Butterworth bandpass filter (steep attenuation of audible music)."""

    # -------------------------------------------------------------------------
    # 7. Audio Mixing & Normalization
    # -------------------------------------------------------------------------
    ultrasonic_gain_db: float = -20.0
    """
    Ultrasonic signal gain relative to the background music in decibels (-20 dB).
    -20 dB corresponds to an amplitude multiplier of 0.10 (10% of music volume),
    ensuring it does not distort the music or cause speaker coil intermodulation.
    """

    peak_limit: float = 0.95
    """Maximum output amplitude ceiling (0.95 = -0.45 dBFS) to prevent DAC digital clipping."""

    @classmethod
    def get_profile(cls, profile: ProfileType = ProfileType.UNIVERSAL_48K) -> "SonicConfig":
        """
        Factory helper to retrieve a pre-tuned SonicConfig instance for a specific profile.

        Parameters
        ----------
        profile : ProfileType
            The target audio hardware profile (UNIVERSAL_48K or HD_96K).

        Returns
        -------
        SonicConfig
            A fully initialized configuration object with optimal tuned parameters.
        """
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
                peak_limit=0.95,
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
                peak_limit=0.95,
            )
        else:
            raise ValueError(f"Unknown profile: {profile}")
