from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.api_keys import create_api_key


client = TestClient(app)


def test_receipts_require_api_key():
    response = client.post(
        "/receipts",
        json={
            "agent_id": "auth-test",
            "action": "test_action",
            "timestamp": "2026-08-19T04:00:00Z",
            "authorization_status": "authorized",
            "result_status": "success",
            "metadata": {},
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "API key required"


def test_invalid_api_key_is_rejected():
    response = client.post(
        "/receipts",
        headers={
            "X-API-Key": "ap_this_is_not_a_real_key"
        },
        json={
            "agent_id": "auth-test",
            "action": "test_action",
            "timestamp": "2026-08-19T04:00:00Z",
            "authorization_status": "authorized",
            "result_status": "success",
            "metadata": {},
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"