import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

PASSWORD_HASHER = PasswordHash.recommended()
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return PASSWORD_HASHER.verify(password, password_hash)


def new_refresh_token(session_id: str) -> str:
    return f"{session_id}.{secrets.token_urlsafe(48)}"


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: str, session_id: str) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=get_settings().access_token_minutes)
    payload = {"sub": user_id, "sid": session_id, "iat": now, "exp": expires}
    return jwt.encode(payload, get_settings().session_signing_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_settings().session_signing_key, algorithms=[JWT_ALGORITHM])


def csrf_token() -> str:
    return secrets.token_urlsafe(32)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
