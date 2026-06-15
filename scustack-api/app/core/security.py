import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt

from app.core.config import settings


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


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user_id,
        'role': role,
        'iat': now,
        'exp': now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        'jti': uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    return uuid4().hex + uuid4().hex


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
