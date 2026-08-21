import requests
import time
from datetime import datetime, timezone
from functools import wraps

from .receipt import Receipt


class AgentProofError(Exception):
    """Base exception for AgentProof SDK errors."""


class AgentProof:
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:8000",
        agent_id: str = "unknown-agent",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id

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

    def track(
        self,
        action: str | None = None,
        authorization_status: str = "authorized",
        metadata: dict | None = None,
    ):
        """
        Automatically create an AgentProof receipt
        whenever the decorated function runs.
        """

        def decorator(func):
            tracked_action = action or func.__name__

            @wraps(func)
            def wrapper(*args, **kwargs):
                timestamp = (
                    datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)

                    duration = round(
                        time.perf_counter() - start_time,
                        4,
                    )

                    self.record(
                        agent_id=self.agent_id,
                        action=tracked_action,
                        authorization_status=authorization_status,
                        result_status="success",
                        metadata={
                            **(metadata or {}),
                            "duration_seconds": duration,
                        },
                        timestamp=timestamp,
                    )

                    return result

                except Exception as error:
                    duration = round(
                        time.perf_counter() - start_time,
                        4,
                    )

                    self.record(
                        agent_id=self.agent_id,
                        action=tracked_action,
                        authorization_status=authorization_status,
                        result_status="failed",
                        metadata={
                            **(metadata or {}),
                            "error": str(error),
                            "duration_seconds": duration,
                        },
                        timestamp=timestamp,
                    )

                    raise

            return wrapper

        return decorator

    def verify_receipt(self, receipt_id: str):
        response = requests.get(
            f"{self.base_url}/receipts/{receipt_id}",
            headers={},
        )

        if response.status_code >= 400:
            raise AgentProofError(
                f"AgentProof API returned "
                f"{response.status_code}: "
                f"{response.text}"
            )

        return response.json()