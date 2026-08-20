import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4


def normalize_timestamp(timestamp: datetime) -> str:
    """
    Convert a datetime into one consistent UTC representation.
    """

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    timestamp = timestamp.astimezone(timezone.utc)

    return timestamp.isoformat().replace("+00:00", "Z")


def create_receipt_id() -> str:
    """
    Create a unique public receipt identifier.
    """

    return f"AP-{uuid4().hex[:16].upper()}"


def canonicalize_record(
    receipt_id: str,
    agent_id: str,
    action: str,
    timestamp: str,
    authorization_status: str,
    result_status: str,
    metadata: dict,
) -> str:
    """
    Create a deterministic representation of a receipt.

    The same data should always produce the exact same string.
    """

    record = {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "agent_id": agent_id,
        "action": action,
        "timestamp": timestamp,
        "authorization_status": authorization_status,
        "result_status": result_status,
        "metadata": metadata,
    }

    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def calculate_hash(canonical_record: str) -> str:
    """
    Create a SHA-256 hash of the canonical record.
    """

    return hashlib.sha256(
        canonical_record.encode("utf-8")
    ).hexdigest()