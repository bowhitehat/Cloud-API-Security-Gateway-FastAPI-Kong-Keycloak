from datetime import datetime, timedelta, timezone
from typing import Any

import json
from urllib.request import urlopen

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Keycloak configs
KEYCLOAK_URL = "http://localhost:8081" # Dùng chung cho frontend và backend để khớp issuer
REALM = "capstone"
JWKS_URL = f"http://keycloak:8080/realms/{REALM}/protocol/openid-connect/certs"

_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        try:
            with urlopen(JWKS_URL) as response:
                _jwks_cache = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print("Failed to fetch JWKS:", e)
    return _jwks_cache

def decode_access_token(token: str) -> dict[str, Any]:
    jwks = get_jwks()
    if not jwks:
        raise ValueError("Could not fetch Keycloak public keys")

    try:
        # Giải mã unverified header để lấy kid
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if not rsa_key:
            raise ValueError("Public key not found in JWKS")

        # Giải mã với RSA public key
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience="account",
            issuer=f"{KEYCLOAK_URL}/realms/{REALM}",
            options={"verify_aud": False}
        )
        return payload
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
