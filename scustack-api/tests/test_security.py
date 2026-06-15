import os
import pytest
from app.core.security import encrypt_pii, decrypt_pii


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    monkeypatch.setenv('SCUSTACK_ENCRYPTION_KEY', 'test-key-32-bytes-long!!-xxxxx')


class TestPIIEncryption:
    def test_encrypt_and_decrypt_roundtrip(self):
        plain = '13800138000'
        encrypted = encrypt_pii(plain)
        assert encrypted != plain
        assert len(encrypted) > 24
        assert decrypt_pii(encrypted) == plain

    def test_encrypt_produces_different_ciphertexts(self):
        plain = '13800138000'
        c1 = encrypt_pii(plain)
        c2 = encrypt_pii(plain)
        assert c1 != c2

    def test_decrypt_returns_original_text(self):
        plain = '2024123456'
        encrypted = encrypt_pii(plain)
        assert decrypt_pii(encrypted) == plain

    def test_encrypt_empty_string(self):
        plain = ''
        encrypted = encrypt_pii(plain)
        assert decrypt_pii(encrypted) == plain

    def test_encrypt_chinese_text(self):
        plain = '测试学号'
        encrypted = encrypt_pii(plain)
        assert decrypt_pii(encrypted) == plain

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv('SCUSTACK_ENCRYPTION_KEY', raising=False)
        with pytest.raises(RuntimeError, match='ENCRYPTION_KEY'):
            encrypt_pii('test')
