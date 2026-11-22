"""Key metadata and lifecycle management placeholder. Never log private key material."""

class KeyManager:
    def create_key_record(self, recipient_id: str) -> dict:
        raise NotImplementedError("Member A: define safe key lifecycle and persistence.")
