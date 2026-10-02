import unittest
import os
import sys

# Ensure receiver and root are in sys.path
test_dir = os.path.dirname(os.path.abspath(__file__))
receiver_dir = os.path.abspath(os.path.join(test_dir, '..'))
root_dir = os.path.abspath(os.path.join(receiver_dir, '..'))
for d in (receiver_dir, root_dir):
    if d not in sys.path:
        sys.path.insert(0, d)

import numpy as np
from sonicwave.config import SonicConfig, ProfileType
from sonicwave.modulation import SonicModulator
from sonicwave.demodulation import UltrasonicBandpassFilter, MatchedFilterDetector, FSKDemodulator
from sonicwave.framing import parse_frame
from sonicwave.mixer import generate_ambient_music_sample, mix_music_and_data


class TestDSPLoopback(unittest.TestCase):
    def test_loopback_clean_channel_48k(self):
        config = SonicConfig.get_profile(ProfileType.UNIVERSAL_48K)
        modulator = SonicModulator(config)
        bp_filter = UltrasonicBandpassFilter(config)
        detector = MatchedFilterDetector(config)
        demodulator = FSKDemodulator(config)

        payload = b"HELLO"
        tx_audio = modulator.modulate_packet(payload)
        
        # Simulate transmission with a 0.1s silence lead-in
        lead_in = np.zeros(int(config.sample_rate * 0.1), dtype=np.float32)
        channel_audio = np.concatenate([lead_in, tx_audio, lead_in])
        
        # Receiver stage 1: Bandpass filter
        filtered_audio = bp_filter.filter_all(channel_audio)
        
        # Receiver stage 2: Matched filter preamble sync
        peaks = detector.find_peaks(filtered_audio)
        self.assertGreaterEqual(len(peaks), 1, "Preamble chirp was not detected")
        
        # Peak index is the end of the chirp
        chirp_end = peaks[0]
        gap_samples = int(config.sample_rate * 0.02)
        data_start = chirp_end + gap_samples
        
        # Receiver stage 3: FSK Demodulation
        bits, snr = demodulator.demodulate_stream(filtered_audio, data_start, max_bits=100)
        
        # Receiver stage 4: Framing & CRC-16 check
        is_valid, decoded_payload, msg = parse_frame(bits, config)
        self.assertTrue(is_valid, f"Decoding failed: {msg}")
        self.assertEqual(decoded_payload, payload)
        self.assertGreater(snr, 10.0, f"Expected high SNR, got {snr:.1f} dB")

    def test_loopback_with_music_and_noise(self):
        config = SonicConfig.get_profile(ProfileType.UNIVERSAL_48K)
        modulator = SonicModulator(config)
        bp_filter = UltrasonicBandpassFilter(config)
        detector = MatchedFilterDetector(config)
        demodulator = FSKDemodulator(config)

        payload = b"HELLO"
        tx_audio = modulator.modulate_packet(payload)
        
        # Generate 5s of ambient music
        music = generate_ambient_music_sample(duration_sec=5.0, sample_rate=config.sample_rate)
        
        # Mix ultrasonic data onto music at -20 dB
        mixed_audio = mix_music_and_data(music, tx_audio, config, offset_sec=1.0)
        
        # Add random room noise (AWGN)
        np.random.seed(42)
        noise = np.random.normal(0, 0.005, len(mixed_audio)).astype(np.float32)
        received_audio = mixed_audio + noise
        
        # Receiver stage 1: Bandpass filter
        filtered_audio = bp_filter.filter_all(received_audio)
        
        # Receiver stage 2: Matched filter preamble sync
        peaks = detector.find_peaks(filtered_audio)
        self.assertGreaterEqual(len(peaks), 1, "Preamble chirp was not detected in music mix")
        
        chirp_end = peaks[0]
        gap_samples = int(config.sample_rate * 0.02)
        data_start = chirp_end + gap_samples
        
        # Receiver stage 3: FSK Demodulation
        bits, snr = demodulator.demodulate_stream(filtered_audio, data_start, max_bits=100)
        
        # Receiver stage 4: Framing & CRC-16 check
        is_valid, decoded_payload, msg = parse_frame(bits, config)
        self.assertTrue(is_valid, f"Decoding failed under music: {msg}")
        self.assertEqual(decoded_payload, payload)

    def test_loopback_hd_96k_mode(self):
        config = SonicConfig.get_profile(ProfileType.HD_96K)
        modulator = SonicModulator(config)
        bp_filter = UltrasonicBandpassFilter(config)
        detector = MatchedFilterDetector(config)
        demodulator = FSKDemodulator(config)

        payload = b"HELLO"
        tx_audio = modulator.modulate_packet(payload)
        
        lead_in = np.zeros(int(config.sample_rate * 0.1), dtype=np.float32)
        channel_audio = np.concatenate([lead_in, tx_audio, lead_in])
        
        filtered_audio = bp_filter.filter_all(channel_audio)
        peaks = detector.find_peaks(filtered_audio)
        self.assertGreaterEqual(len(peaks), 1, "24 kHz chirp was not detected")
        
        data_start = peaks[0] + int(config.sample_rate * 0.02)
        bits, snr = demodulator.demodulate_stream(filtered_audio, data_start, max_bits=100)
        
        is_valid, decoded_payload, msg = parse_frame(bits, config)
        self.assertTrue(is_valid, f"96k decoding failed: {msg}")
        self.assertEqual(decoded_payload, payload)


if __name__ == '__main__':
    unittest.main()
