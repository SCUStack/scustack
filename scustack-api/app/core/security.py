import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    key = os.getenv('SCUSTACK_ENCRYPTION_KEY')
    if not key:
        raise RuntimeError('SCUSTACK_ENCRYPTION_KEY environment variable is required')
    return hashlib.sha256(key.encode()).digest()


def encrypt_pii(plaintext: str) -> str:
    key = _get_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return (nonce + ciphertext).hex()


def decrypt_pii(hex_data: str) -> str:
    key = _get_key()
    raw = bytes.fromhex(hex_data)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
