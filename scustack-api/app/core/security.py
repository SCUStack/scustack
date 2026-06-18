import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from secrets import token_bytes
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt

from app.core.config import settings


def _get_secret_value() -> str:
    # Re-read env so tests and one-off scripts can override the key at runtime.
    raw_value = os.getenv('SCUSTACK_ENCRYPTION_KEY')
    value = (raw_value if raw_value is not None else settings.ENCRYPTION_KEY).strip()
    if not value:
        raise RuntimeError('ENCRYPTION_KEY must be set to a non-default value')
    return value


def _derive_key(purpose: str) -> bytes:
    secret = _get_secret_value()
    return hashlib.sha256(f'{purpose}:{secret}'.encode()).digest()


def encrypt_pii(plaintext: str) -> str:
    key = _derive_key('pii_encryption')
    nonce = token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return (nonce + ciphertext).hex()


def decrypt_pii(hex_data: str) -> str:
    key = _derive_key('pii_encryption')
    raw = bytes.fromhex(hex_data)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


def blind_index_pii(value: str) -> str:
    key = _derive_key('pii_lookup')
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


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


def hash_pii(value: str) -> str:
    """One-way hash for PII-safe audit logging. Not reversible."""
    return hashlib.sha256((value + _get_secret_value()).encode()).hexdigest()
