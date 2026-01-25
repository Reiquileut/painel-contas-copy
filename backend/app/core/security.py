from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import os
from app.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# JWT Token
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


# Account password encryption (Fernet)
def get_fernet_cipher() -> Fernet:
    key = settings.encryption_key
    if not key:
        raise ValueError("ENCRYPTION_KEY not set")

    # Ensure key is valid Fernet key (32 url-safe base64-encoded bytes)
    try:
        return Fernet(key.encode())
    except Exception:
        # If key is not valid Fernet format, derive one
        key_bytes = key.encode()[:32].ljust(32, b'0')
        key_b64 = base64.urlsafe_b64encode(key_bytes)
        return Fernet(key_b64)


def encrypt_account_password(password: str) -> str:
    cipher = get_fernet_cipher()
    return cipher.encrypt(password.encode()).decode()


def decrypt_account_password(encrypted: str) -> str:
    cipher = get_fernet_cipher()
    return cipher.decrypt(encrypted.encode()).decode()
