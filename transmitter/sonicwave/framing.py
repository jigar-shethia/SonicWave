"""
Packet Framing, Bit Serialization, Barker Synchronization, and CRC-16 for SonicWave.

This module converts raw payload bytes (such as "Hello world") into a robust
binary bitstream structured as follows:

   +-------------------------+--------------------+---------------------+-------------------+
   | Barker Sync (13 bits)   | Length (8 bits)    | Payload (N*8 bits)  | CRC-16 (16 bits)  |
   +-------------------------+--------------------+---------------------+-------------------+
   | 1 1 1 1 1 0 0 1 1 0 1 0 1 | 0..255 byte count  | UTF-8 ASCII bytes   | CCITT Checksum    |
   +-------------------------+--------------------+---------------------+-------------------+

Purpose of Each Field:
-----------------------
1. Barker Sync (13 bits):
   A known mathematical sequence (`1111100110101`) that provides a sharp autocorrelation
   peak. Even if ambient noise is present, the receiver detects this exact pattern to establish
   symbol boundary timing and bit synchronization.
2. Length Header (8 bits):
   An unsigned 8-bit integer (0-255) specifying how many payload bytes follow.
   Allows variable-length text messages without padding waste.
3. Payload (N * 8 bits):
   The serialized bytes of the user's message, transmitted MSB (Most Significant Bit) first.
4. CRC-16-CCITT (16 bits):
   Cyclic Redundancy Check error-detecting code calculated over the payload bytes.
   Guarantees that distorted or corrupted bits transmitted over acoustic air are rejected
   with 99.998% statistical certainty.
"""

from typing import Tuple, Optional, List
from .config import SonicConfig


def crc16_ccitt(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    """
    Computes a 16-bit CRC-CCITT checksum over input bytes.

    Algorithm & Math:
    -----------------
    - Polynomial: x^16 + x^12 + x^5 + 1 (hexadecimal 0x1021).
    - Initial Register: 0xFFFF.
    - Each byte is XORed into the top 8 bits of the register.
    - The register is shifted left bit-by-bit; if the MSB was 1, it is XORed with 0x1021.
    - Result is masked to 16 bits (0x0000 - 0xFFFF).

    Parameters
    ----------
    data : bytes
        The raw payload bytes to protect.
    poly : int, optional
        Generator polynomial (default: 0x1021).
    init : int, optional
        Initial shift register state (default: 0xFFFF).

    Returns
    -------
    int
        The 16-bit integer checksum.
    """
    crc = init
    for byte in data:
        # Align byte with upper 8 bits of 16-bit register
        crc ^= (byte << 8)
        for _ in range(8):
            # If highest bit is 1, shift and XOR with polynomial
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def build_frame(payload: bytes, config: SonicConfig) -> List[int]:
    """
    Builds the complete digital bitframe for transmission.

    Steps:
    1. Validates payload length (must fit in 8 bits: 1 to 255 bytes).
    2. Calculates CRC-16-CCITT checksum over the payload.
    3. Serializes Barker sync code bits.
    4. Serializes length byte (8 bits, MSB first).
    5. Serializes payload bytes (8 bits per byte, MSB first).
    6. Serializes CRC-16 checksum (16 bits, MSB first).

    Parameters
    ----------
    payload : bytes
        The raw bytes to transmit (e.g. b"Hello").
    config : SonicConfig
        The active configuration containing the Barker sync sequence.

    Returns
    -------
    List[int]
        A flat list of integers (0 and 1) representing the complete frame.
    """
    length = len(payload)
    if length > 255:
        raise ValueError(f"Payload length {length} exceeds maximum frame size (255 bytes)")

    # Compute CRC-16 checksum over payload
    crc = crc16_ccitt(payload)
    
    # -------------------------------------------------------------------------
    # Stage 1: Barker sync sequence (13 bits)
    # -------------------------------------------------------------------------
    bits: List[int] = [int(b) for b in config.barker_code]
    
    # -------------------------------------------------------------------------
    # Stage 2: Payload length header (8 bits, MSB first: bit 7 down to 0)
    # -------------------------------------------------------------------------
    for i in range(7, -1, -1):
        bits.append((length >> i) & 1)
        
    # -------------------------------------------------------------------------
    # Stage 3: Payload data bits (8 bits per byte, MSB first)
    # -------------------------------------------------------------------------
    for byte in payload:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
            
    # -------------------------------------------------------------------------
    # Stage 4: CRC-16 checksum bits (16 bits, MSB first: bit 15 down to 0)
    # -------------------------------------------------------------------------
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
