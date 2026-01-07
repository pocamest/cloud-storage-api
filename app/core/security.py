from passlib.context import CryptContext

_password_context = CryptContext(schemes=["pbkdf2_sha256"])


def hash_password(password: str) -> str:
    return _password_context.hash(secret=password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    return _password_context.verify(secret=raw_password, hash=password_hash)
