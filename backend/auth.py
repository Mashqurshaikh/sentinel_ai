"""
Authentication.

Password hashing via bcrypt (through passlib), sessions as JWTs so the
FastAPI backend stays stateless - no server-side session store to manage.

SENTINEL_JWT_SECRET should be set via environment variable in any real
deployment. A fallback is generated at import time so the app still runs
out of the box for local/demo use, but that means tokens won't survive a
server restart - expected and fine for a student project, not fine for
production.
"""

import os
import datetime
import secrets
import bcrypt
import jwt

JWT_SECRET = os.environ.get("SENTINEL_JWT_SECRET") or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 12


def hash_password(password: str) -> str:
    # bcrypt has a hard 72-byte input limit; truncate rather than error on
    # unusually long passwords.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except Exception:
        return False


def create_token(user_id: int, username: str, role: str, department: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "department": department,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TokenError(Exception):
    pass


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenError("Session expired, please log in again.")
    except jwt.InvalidTokenError:
        raise TokenError("Invalid session token.")
