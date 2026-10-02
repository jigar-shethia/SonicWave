"""
SonicWave: Ultrasonic Audio Data Transmission System
"""

from .config import SonicConfig, ProfileType
from .framing import build_frame, parse_frame, crc16_ccitt
from .modulation import SonicModulator
from .demodulation import UltrasonicBandpassFilter, MatchedFilterDetector, FSKDemodulator, StreamReceiver
from .mixer import mix_music_and_data, generate_ambient_music_sample

__all__ = [
    "SonicConfig",
    "ProfileType",
    "build_frame",
    "parse_frame",
    "crc16_ccitt",
    "SonicModulator",
    "UltrasonicBandpassFilter",
    "MatchedFilterDetector",
    "FSKDemodulator",
    "StreamReceiver",
    "mix_music_and_data",
    "generate_ambient_music_sample",
]
