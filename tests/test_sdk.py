import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.services.api_keys import create_api_key


SDK_PATH = Path(__file__).resolve().parent.parent / "sdk"

sys.path.insert(0, str(SDK_PATH))


from agentproof import AgentProof


client = TestClient(app)


def get_test_api_key():
    db = SessionLocal()

    try:
        return create_api_key(
            db,
            "test-sdk-key",
        )
    finally:
        db.close()


def test_sdk_creates_receipt():
    api_key = get_test_api_key()

    sdk = AgentProof(
        api_key=api_key,
        base_url="http://127.0.0.1:8000",
    )

    receipt = sdk.record(
        agent_id="sdk-test-agent",
        action="send_email",
        authorization_status="authorized",
        result_status="success",
        metadata={
            "test": True,
        },
    )

    assert receipt.receipt_id.startswith("AP-")
    assert receipt.agent_id == "sdk-test-agent"
    assert receipt.action == "send_email"
    assert receipt.record_hash
    assert receipt.verification_url


def test_sdk_returns_receipt_object():
    api_key = get_test_api_key()

    sdk = AgentProof(
        api_key=api_key,
        base_url="http://127.0.0.1:8000",
    )

    receipt = sdk.record(
        agent_id="object-test-agent",
        action="test_action",
        authorization_status="authorized",
        result_status="success",
    )

    assert receipt.receipt_id.startswith("AP-")
    assert receipt.agent_id == "object-test-agent"
    assert receipt.action == "test_action"
    assert receipt.timestamp
    assert receipt.record_hash
    assert receipt.verification_url

    assert repr(receipt).startswith("Receipt(")

def test_receipt_verify():
    api_key = get_test_api_key()

    sdk = AgentProof(
        api_key=api_key,
        base_url="http://127.0.0.1:8000",
    )

    receipt = sdk.record(
        agent_id="verify-test-agent",
        action="test_action",
        authorization_status="authorized",
        result_status="success",
    )

    verification = receipt.verify()

    assert verification["verified"] is True
    assert (
        verification["record_hash"]
        == verification["calculated_hash"]
    )