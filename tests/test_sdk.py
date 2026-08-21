import sys
from pathlib import Path

import pytest

# Make the local SDK importable during tests.
SDK_PATH = Path(__file__).resolve().parents[1] / "sdk"
sys.path.insert(0, str(SDK_PATH))

from agentproof import AgentProof


def test_sdk_creates_receipt(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
    )

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "receipt_id": "AP-TEST123",
                "agent_id": "test-agent",
                "action": "test_action",
                "timestamp": "2026-01-01T00:00:00Z",
                "authorization_status": "authorized",
                "result_status": "success",
                "metadata": {},
                "record_hash": "abc123",
                "verification_url": "http://testserver/verify/AP-TEST123",
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "agentproof.client.requests.post",
        fake_post,
    )

    receipt = proof.record(
        agent_id="test-agent",
        action="test_action",
        authorization_status="authorized",
        result_status="success",
    )

    assert receipt.receipt_id == "AP-TEST123"
    assert receipt.agent_id == "test-agent"
    assert receipt.action == "test_action"


def test_sdk_returns_receipt_object(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
    )

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "receipt_id": "AP-OBJECT123",
                "agent_id": "test-agent",
                "action": "test_action",
                "timestamp": "2026-01-01T00:00:00Z",
                "authorization_status": "authorized",
                "result_status": "success",
                "metadata": {},
                "record_hash": "abc123",
                "verification_url": "http://testserver/verify/AP-OBJECT123",
            }

    monkeypatch.setattr(
        "agentproof.client.requests.post",
        lambda *args, **kwargs: FakeResponse(),
    )

    receipt = proof.record(
        agent_id="test-agent",
        action="test_action",
        authorization_status="authorized",
        result_status="success",
    )

    assert receipt.receipt_id == "AP-OBJECT123"
    assert receipt.result_status == "success"
    assert receipt.metadata == {}
    assert receipt.record_hash == "abc123"


def test_receipt_verify(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
    )

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "receipt_id": "AP-VERIFY123",
                "verified": True,
            }

    monkeypatch.setattr(
        "agentproof.client.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    result = proof.verify_receipt("AP-VERIFY123")

    assert result["receipt_id"] == "AP-VERIFY123"
    assert result["verified"] is True


def test_track_creates_success_receipt(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track("send_email")
    def send_email():
        return "email sent"

    result = send_email()

    assert result == "email sent"
    assert len(calls) == 1
    assert calls[0]["agent_id"] == "test-agent"
    assert calls[0]["action"] == "send_email"
    assert calls[0]["authorization_status"] == "authorized"
    assert calls[0]["result_status"] == "success"


def test_track_creates_failed_receipt(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track("dangerous_action")
    def dangerous_action():
        raise ValueError("Something went wrong")

    with pytest.raises(ValueError, match="Something went wrong"):
        dangerous_action()

    assert len(calls) == 1
    assert calls[0]["agent_id"] == "test-agent"
    assert calls[0]["action"] == "dangerous_action"
    assert calls[0]["authorization_status"] == "authorized"
    assert calls[0]["result_status"] == "failed"
    assert calls[0]["metadata"]["error"] == "Something went wrong"


def test_track_uses_configured_agent_id(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="customer-support-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track("answer_customer")
    def answer_customer():
        return "answered"

    answer_customer()

    assert calls[0]["agent_id"] == "customer-support-agent"


def test_track_preserves_function_return_value(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    monkeypatch.setattr(
        proof,
        "record",
        lambda **kwargs: "receipt",
    )

    @proof.track("calculate_total")
    def calculate_total():
        return 42

    result = calculate_total()

    assert result == 42


def test_track_preserves_function_arguments(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    monkeypatch.setattr(
        proof,
        "record",
        lambda **kwargs: "receipt",
    )

    @proof.track("add_numbers")
    def add_numbers(a, b):
        return a + b

    result = add_numbers(10, 5)

    assert result == 15


def test_track_uses_function_name_when_action_is_not_provided(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track()
    def send_email():
        return "email sent"

    result = send_email()

    assert result == "email sent"
    assert len(calls) == 1
    assert calls[0]["action"] == "send_email"
    assert calls[0]["agent_id"] == "test-agent"
    assert calls[0]["result_status"] == "success"


def test_track_records_duration(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track()
    def slow_action():
        import time

        time.sleep(0.05)
        return "done"

    result = slow_action()

    assert result == "done"
    assert len(calls) == 1
    assert calls[0]["action"] == "slow_action"
    assert calls[0]["result_status"] == "success"
    assert "duration_seconds" in calls[0]["metadata"]
    assert calls[0]["metadata"]["duration_seconds"] >= 0.05


def test_track_records_duration_when_action_fails(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track()
    def failing_action():
        import time

        time.sleep(0.05)
        raise RuntimeError("Agent failed")

    with pytest.raises(RuntimeError, match="Agent failed"):
        failing_action()

    assert len(calls) == 1
    assert calls[0]["action"] == "failing_action"
    assert calls[0]["result_status"] == "failed"
    assert calls[0]["metadata"]["error"] == "Agent failed"
    assert "duration_seconds" in calls[0]["metadata"]
    assert calls[0]["metadata"]["duration_seconds"] >= 0.05


def test_track_preserves_custom_metadata(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track(
        "send_email",
        metadata={
            "recipient": "customer@example.com",
            "priority": "high",
        },
    )
    def send_email():
        return "sent"

    send_email()

    assert calls[0]["metadata"]["recipient"] == "customer@example.com"
    assert calls[0]["metadata"]["priority"] == "high"
    assert "duration_seconds" in calls[0]["metadata"]


def test_track_respects_custom_authorization_status(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track(
        "refund_customer",
        authorization_status="pending",
    )
    def refund_customer():
        return "refund requested"

    refund_customer()

    assert calls[0]["authorization_status"] == "pending"


def test_track_uses_custom_action_when_provided(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    calls = []

    def fake_record(**kwargs):
        calls.append(kwargs)
        return "receipt"

    monkeypatch.setattr(proof, "record", fake_record)

    @proof.track("custom_action_name")
    def completely_different_function():
        return "done"

    completely_different_function()

    assert calls[0]["action"] == "custom_action_name"


def test_track_preserves_function_name(monkeypatch):
    proof = AgentProof(
        api_key="test-key",
        base_url="http://testserver",
        agent_id="test-agent",
    )

    monkeypatch.setattr(
        proof,
        "record",
        lambda **kwargs: "receipt",
    )

    @proof.track()
    def original_function():
        return "done"

    assert original_function.__name__ == "original_function"