import requests
from datetime import datetime, timezone

from .receipt import Receipt


class AgentProofError(Exception):
    """Base exception for AgentProof SDK errors."""


class AgentProof:
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:8000",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def record(
        self,
        agent_id: str,
        action: str,
        authorization_status: str,
        result_status: str,
        metadata: dict | None = None,
        timestamp: str | None = None,
    ):
        payload = {
            "agent_id": agent_id,
            "action": action,
            "authorization_status": authorization_status,
            "result_status": result_status,
            "metadata": metadata or {},
        }

        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace(
                "+00:00",
                "Z",
            )

        payload["timestamp"] = timestamp

        response = requests.post(
            f"{self.base_url}/receipts",
            headers={
                "X-API-Key": self.api_key,
            },
            json=payload,
        )

        if response.status_code >= 400:
            raise AgentProofError(
                f"AgentProof API returned "
                f"{response.status_code}: "
                f"{response.text}"
            )

        return Receipt(
            response.json(),
            self,
        )
    def verify_receipt(self, receipt_id: str):
        response = requests.get(
            f"{self.base_url}/receipts/{receipt_id}",
            headers={
                "X-API-Key": self.api_key,
            },
        )

        if response.status_code >= 400:
            raise AgentProofError(
                f"AgentProof API returned "
                f"{response.status_code}: "
                f"{response.text}"
            )

        return response.json()