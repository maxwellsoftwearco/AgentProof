import hashlib
import secrets

from sqlalchemy.orm import Session

from ..models import APIKey


def generate_api_key() -> str:
    return "ap_" + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def create_api_key(
    db: Session,
    name: str,
) -> str:

    api_key = generate_api_key()

    key_hash = hash_api_key(api_key)

    record = APIKey(
        key_hash=key_hash,
        name=name,
        active=True,
    )

    db.add(record)
    db.commit()

    return api_key


def verify_api_key(
    db: Session,
    api_key: str,
) -> bool:

    key_hash = hash_api_key(api_key)

    record = (
        db.query(APIKey)
        .filter(
            APIKey.key_hash == key_hash,
            APIKey.active == True,
        )
        .first()
    )

    return record is not None