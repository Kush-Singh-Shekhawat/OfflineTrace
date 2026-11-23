"""Simple repetition-based error correction for watermark payloads."""

def encode_payload(payload: bytes) -> bytes:
    """Repeat each byte three times to allow single-byte error recovery."""
    if not isinstance(payload, bytes):
        raise TypeError("Payload must be bytes.")

    return b"".join(bytes([byte]) * 3 for byte in payload)


def decode_payload(encoded: bytes) -> bytes:
    """Decode triplicated bytes using majority voting."""
    if not isinstance(encoded, bytes):
        raise TypeError("Encoded payload must be bytes.")

    if len(encoded) % 3 != 0:
        raise ValueError("Encoded payload length must be divisible by 3.")

    decoded = bytearray()

    for index in range(0, len(encoded), 3):
        a, b, c = encoded[index:index + 3]

        if a == b or a == c:
            decoded.append(a)
        elif b == c:
            decoded.append(b)
        else:
            raise ValueError("Unable to correct corrupted payload.")

    return bytes(decoded)