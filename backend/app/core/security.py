from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
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

    try:
        return Fernet(key.encode())
    except Exception as exc:
        raise ValueError("ENCRYPTION_KEY must be a valid Fernet key") from exc


def encrypt_account_password(password: str) -> str:
    cipher = get_fernet_cipher()
    return cipher.encrypt(password.encode()).decode()


def decrypt_account_password(encrypted: str) -> str:
    cipher = get_fernet_cipher()
    return cipher.decrypt(encrypted.encode()).decode()


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def create_csrf_token_value() -> str:
    return secrets.token_urlsafe(32)


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
