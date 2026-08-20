from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def get_test_api_key():
    response = client.post(
        "/dev/create-api-key"
    )

    assert response.status_code == 200

    return response.json()["api_key"]


def test_create_receipt():
    api_key = get_test_api_key()

    response = client.post(
        "/receipts",
        headers={
            "X-API-Key": api_key
        },
        json={
            "agent_id": "test-agent-api",
            "action": "send_email",
            "timestamp": "2026-08-19T03:30:00Z",
            "authorization_status": "authorized",
            "result_status": "success",
            "metadata": {
                "test": True
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["receipt_id"].startswith("AP-")
    assert data["agent_id"] == "test-agent-api"
    assert data["action"] == "send_email"
    assert data["record_hash"]
    assert data["verification_url"]


def test_get_receipt_and_verify():
    api_key = get_test_api_key()

    create_response = client.post(
        "/receipts",
        headers={
            "X-API-Key": api_key
        },
        json={
            "agent_id": "verification-test",
            "action": "test_action",
            "timestamp": "2026-08-19T03:30:00Z",
            "authorization_status": "authorized",
            "result_status": "success",
            "metadata": {
                "test": True
            },
        },
    )

    assert create_response.status_code == 200

    receipt_id = create_response.json()["receipt_id"]

    response = client.get(
        f"/receipts/{receipt_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["verified"] is True
    assert (
        data["record_hash"]
        == data["calculated_hash"]
    )


def test_missing_receipt_returns_404():
    response = client.get(
        "/receipts/AP-DOES-NOT-EXIST"
    )

    assert response.status_code == 404