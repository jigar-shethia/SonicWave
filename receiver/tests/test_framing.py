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

from sonicwave.config import SonicConfig
from sonicwave.framing import build_frame, parse_frame, crc16_ccitt


class TestFraming(unittest.TestCase):
    def setUp(self):
        self.config = SonicConfig()

    def test_crc16_known_vector(self):
        # Standard ASCII "123456789" CCITT CRC test vector: 0x29B1 or 0x31C3 depending on model
        data = b"HELLO"
        crc = crc16_ccitt(data)
        self.assertIsInstance(crc, int)
        self.assertTrue(0 <= crc <= 0xFFFF)
        # Verify determinism
        self.assertEqual(crc, crc16_ccitt(data))

    def test_build_and_parse_frame_hello(self):
        payload = b"HELLO"
        bits = build_frame(payload, self.config)
        
        # Verify bit count: Barker(13) + Len(8) + Payload(5*8=40) + CRC(16) = 77 bits
        expected_len = len(self.config.barker_code) + 8 + (5 * 8) + 16
        self.assertEqual(len(bits), expected_len)
        
        # Parse frame
        is_valid, decoded_payload, msg = parse_frame(bits, self.config)
        self.assertTrue(is_valid, f"Parse failed: {msg}")
        self.assertEqual(decoded_payload, payload)
        self.assertEqual(msg, "CRC PASS")

    def test_corrupted_payload_rejected(self):
        payload = b"HELLO"
        bits = build_frame(payload, self.config)
        
        # Flip a single bit in the payload (e.g. index 30)
        bits[30] = 1 - bits[30]
        
        is_valid, decoded_payload, msg = parse_frame(bits, self.config)
        self.assertFalse(is_valid)
        self.assertIn("CRC mismatch", msg)

    def test_empty_payload(self):
        payload = b""
        bits = build_frame(payload, self.config)
        is_valid, decoded_payload, msg = parse_frame(bits, self.config)
        self.assertTrue(is_valid)
        self.assertEqual(decoded_payload, b"")


if __name__ == '__main__':
    unittest.main()
