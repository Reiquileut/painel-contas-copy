from datetime import timedelta

import pytest

from app.core import security


def test_password_hash_and_verify_roundtrip():
    password = "my-secret-password"
    hashed = security.get_password_hash(password)

    assert hashed != password
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrong-password", hashed) is False


def test_create_and_decode_token_success():
    token = security.create_access_token(
        {"sub": "admin"},
        expires_delta=timedelta(minutes=5)
    )

    payload = security.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"


def test_create_and_decode_token_with_default_expiration():
    token = security.create_access_token({"sub": "default-exp"})
    payload = security.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "default-exp"


def test_decode_token_invalid_returns_none():
    assert security.decode_token("not-a-valid-token") is None


def test_encrypt_decrypt_account_password_roundtrip(monkeypatch):
    monkeypatch.setattr(
        security.settings,
        "encryption_key",
        "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    )
    encrypted = security.encrypt_account_password("account-pass")

    assert encrypted != "account-pass"
    assert security.decrypt_account_password(encrypted) == "account-pass"


def test_get_fernet_cipher_without_key_raises(monkeypatch):
    monkeypatch.setattr(security.settings, "encryption_key", "")
    with pytest.raises(ValueError, match="ENCRYPTION_KEY not set"):
        security.get_fernet_cipher()


def test_get_fernet_cipher_invalid_key_raises(monkeypatch):
    monkeypatch.setattr(security.settings, "encryption_key", "invalid-short-key")
    with pytest.raises(ValueError, match="valid Fernet key"):
        security.get_fernet_cipher()
