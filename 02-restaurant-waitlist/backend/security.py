import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def generate_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"
