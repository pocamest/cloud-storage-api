from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$/XfrP46+"
    "evRrhMwxiezf1Q$Tt5aC731snsO50khGAqqoZUJX51OSjdd5qWwk3IzVBI"
)


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    return _password_hash.verify(raw_password, password_hash)


def dummy_verify(raw_password: str) -> None:
    _password_hash.verify(raw_password, _DUMMY_HASH)
