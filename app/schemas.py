from datetime import datetime

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        description="A name to identify what this API key is used for.",
        examples=["My AI Agent"],
    )


class ReceiptCreate(BaseModel):
    agent_id: str = Field(
        min_length=1,
        max_length=255,
        description="The unique name or ID of the AI agent that performed the action.",
        examples=["customer-support-agent"],
    )

    action: str = Field(
        min_length=1,
        max_length=255,
        description="What the AI agent did.",
        examples=["send_email"],
    )

    timestamp: datetime = Field(
        description="When the AI agent performed the action.",
        examples=["2026-08-20T23:15:32Z"],
    )

    authorization_status: str = Field(
        min_length=1,
        max_length=50,
        description="Whether the action was authorized.",
        examples=["authorized"],
    )

    result_status: str = Field(
        min_length=1,
        max_length=50,
        description="The result of the action.",
        examples=["success"],
    )

    metadata: dict = Field(
        default_factory=dict,
        description="Optional additional information about the action.",
        examples=[{"email": "customer@example.com"}],
    )


class ReceiptResponse(BaseModel):
    receipt_id: str = Field(
        description="Unique AgentProof receipt ID.",
        examples=["AP-4ABB768D705A4391"],
    )

    agent_id: str
    action: str
    timestamp: str
    authorization_status: str
    result_status: str
    metadata: dict

    record_hash: str = Field(
        description="SHA-256 hash used to verify the receipt's integrity.",
    )

    verification_url: str = Field(
        description="Public URL where anyone can verify this receipt.",
        examples=[
            "https://agentproof-dydt.onrender.com/verify/AP-4ABB768D705A4391"
        ],
    )