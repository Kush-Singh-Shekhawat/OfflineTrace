"""Secure watermark token generation."""

import secrets


def generate_token() -> str:
    """Generate a cryptographically secure 256-bit watermark token."""
    return secrets.token_urlsafe(32)