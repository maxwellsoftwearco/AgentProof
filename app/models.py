from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)

    receipt_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )

    agent_id: Mapped[str] = mapped_column(String(255))

    action: Mapped[str] = mapped_column(String(255))

    timestamp: Mapped[str] = mapped_column(String(64))

    authorization_status: Mapped[str] = mapped_column(
        String(50)
    )

    result_status: Mapped[str] = mapped_column(
        String(50)
    )

    metadata_json: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    record_hash: Mapped[str] = mapped_column(
        String(64)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )

    active: Mapped[bool] = mapped_column(
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )