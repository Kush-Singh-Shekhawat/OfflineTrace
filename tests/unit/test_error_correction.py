import pytest

from backend.app.watermark.error_correction import (
    encode_payload,
    decode_payload,
)


def test_encode_decode_round_trip():
    payload = b"OfflineTrace"
    assert decode_payload(encode_payload(payload)) == payload


def test_recovers_one_corrupted_byte():
    encoded = bytearray(encode_payload(b"ABC"))
    encoded[1] = ord("X")

    assert decode_payload(bytes(encoded)) == b"ABC"


def test_rejects_invalid_encoded_length():
    with pytest.raises(ValueError):
        decode_payload(b"ABCDE")


def test_rejects_non_bytes():
    with pytest.raises(TypeError):
        encode_payload("OfflineTrace")


def test_empty_payload():
    assert encode_payload(b"") == b""
    assert decode_payload(b"") == b""