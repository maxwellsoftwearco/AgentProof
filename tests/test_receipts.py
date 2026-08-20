from datetime import datetime, timezone

from app.services.receipts import (
    calculate_hash,
    canonicalize_record,
    create_receipt_id,
    normalize_timestamp,
)


def test_receipt_id_is_created():
    receipt_id = create_receipt_id()

    assert receipt_id.startswith("AP-")
    assert len(receipt_id) == 19


def test_timestamp_is_normalized():
    timestamp = datetime(
        2026,
        8,
        19,
        3,
        30,
        tzinfo=timezone.utc,
    )

    result = normalize_timestamp(timestamp)

    assert result == "2026-08-19T03:30:00Z"


def test_same_record_produces_same_hash():
    record = canonicalize_record(
        receipt_id="AP-TEST1234567890",
        agent_id="test-agent",
        action="send_email",
        timestamp="2026-08-19T03:30:00Z",
        authorization_status="authorized",
        result_status="success",
        metadata={"test": True},
    )

    hash_one = calculate_hash(record)
    hash_two = calculate_hash(record)

    assert hash_one == hash_two


def test_changed_record_produces_different_hash():
    record_one = canonicalize_record(
        receipt_id="AP-TEST1234567890",
        agent_id="test-agent",
        action="send_email",
        timestamp="2026-08-19T03:30:00Z",
        authorization_status="authorized",
        result_status="success",
        metadata={"test": True},
    )

    record_two = canonicalize_record(
        receipt_id="AP-TEST1234567890",
        agent_id="test-agent",
        action="DELETE_DATABASE",
        timestamp="2026-08-19T03:30:00Z",
        authorization_status="authorized",
        result_status="success",
        metadata={"test": True},
    )

    hash_one = calculate_hash(record_one)
    hash_two = calculate_hash(record_two)

    assert hash_one != hash_two