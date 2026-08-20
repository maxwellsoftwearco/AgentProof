from datetime import datetime

from pydantic import BaseModel, Field


class ReceiptCreate(BaseModel):
    agent_id: str = Field(min_length=1, max_length=255)
    action: str = Field(min_length=1, max_length=255)
    timestamp: datetime
    authorization_status: str = Field(
        min_length=1,
        max_length=50,
    )
    result_status: str = Field(
        min_length=1,
        max_length=50,
    )
    metadata: dict = Field(default_factory=dict)


class ReceiptResponse(BaseModel):
    receipt_id: str
    agent_id: str
    action: str
    timestamp: str
    authorization_status: str
    result_status: str
    metadata: dict
    record_hash: str
    verification_url: str