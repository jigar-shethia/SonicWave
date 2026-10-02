"""
Framing, serialization, Barker sync, and CRC-16-CCITT for SonicWave packets.
"""

from typing import Tuple, Optional, List
from .config import SonicConfig


def crc16_ccitt(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    """
    Computes CRC-16-CCITT over data bytes.
    Polynomial: x^16 + x^12 + x^5 + 1 (0x1021)
    """
    crc = init
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def build_frame(payload: bytes, config: SonicConfig) -> List[int]:
    """
    Constructs a complete bitframe:
    [Barker Sync Code] + [Length Header (8 bits)] + [Payload (N*8 bits)] + [CRC16 (16 bits)]
    """
    length = len(payload)
    if length > 255:
        raise ValueError(f"Payload length {length} exceeds maximum frame size (255 bytes)")

    crc = crc16_ccitt(payload)
    
    # 1. Barker sync code bits
    bits: List[int] = [int(b) for b in config.barker_code]
    
    # 2. Length header (8 bits, MSB first)
    for i in range(7, -1, -1):
        bits.append((length >> i) & 1)
        
    # 3. Payload bits (MSB first for each byte)
    for byte in payload:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
            
    # 4. CRC-16 (16 bits, MSB first)
    for i in range(15, -1, -1):
        bits.append((crc >> i) & 1)
        
    return bits


def parse_frame(bits: List[int], config: SonicConfig) -> Tuple[bool, Optional[bytes], str]:
    """
    Parses a bitstream, checks Barker sync, extracts length & payload, and validates CRC-16.
    Returns: (is_valid, payload_bytes, status_message)
    """
    barker_len = len(config.barker_code)
    min_bits = barker_len + 8 + 16  # Barker + Length + CRC (empty payload)
    
    if len(bits) < min_bits:
        return False, None, f"Bitstream too short ({len(bits)} < {min_bits})"
        
    # Check Barker sync
    received_barker = "".join(str(b) for b in bits[:barker_len])
    if received_barker != config.barker_code:
        # Check bit error count in barker
        errors = sum(1 for a, b in zip(received_barker, config.barker_code) if a != b)
        if errors > 2:  # Allow max 2 bit flips in Barker
            return False, None, f"Barker sync mismatch (errors: {errors})"
            
    # Read length (8 bits)
    idx = barker_len
    length = 0
    for i in range(8):
        length = (length << 1) | bits[idx + i]
    idx += 8
    
    total_expected_bits = barker_len + 8 + (length * 8) + 16
    if len(bits) < total_expected_bits:
        return False, None, f"Incomplete packet: expected {total_expected_bits} bits, got {len(bits)}"
        
    # Read payload bytes
    payload_byte_list = []
    for _ in range(length):
        byte_val = 0
        for _ in range(8):
            byte_val = (byte_val << 1) | bits[idx]
            idx += 1
        payload_byte_list.append(byte_val)
    payload_bytes = bytes(payload_byte_list)
    
    # Read CRC16
    received_crc = 0
    for _ in range(16):
        received_crc = (received_crc << 1) | bits[idx]
        idx += 1
        
    # Verify CRC
    computed_crc = crc16_ccitt(payload_bytes)
    if received_crc != computed_crc:
        return False, payload_bytes, f"CRC mismatch: received 0x{received_crc:04X}, computed 0x{computed_crc:04X}"
        
    return True, payload_bytes, "CRC PASS"
