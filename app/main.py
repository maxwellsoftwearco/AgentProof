from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Receipt
from .schemas import (
    APIKeyCreate,
    ReceiptCreate,
    ReceiptResponse,
)
from .services.receipts import (
    calculate_hash,
    canonicalize_record,
    create_receipt_id,
    normalize_timestamp,
)
from .services.api_keys import (
    create_api_key,
    verify_api_key,
)


# Create the database tables when the application starts.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AgentProof",
    description="Verifiable receipts for AI-agent actions.",
    version="0.1.0",
)

templates = Jinja2Templates(
    directory="app/templates"
)


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )

def require_api_key(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
        )

    if not verify_api_key(db, x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return x_api_key

@app.post("/api-keys")
def create_new_api_key(
    data: APIKeyCreate,
    db: Session = Depends(get_db),
):
    api_key = create_api_key(
        db,
        data.name,
    )

    return {
        "api_key": api_key,
        "name": data.name,
        "warning": "Store this API key securely. It cannot be retrieved later.",
    }

@app.post(
    "/receipts",
    response_model=ReceiptResponse,
)
def create_receipt(
    receipt: ReceiptCreate,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(require_api_key),
):
    # Generate a unique ID for this receipt.
    receipt_id = create_receipt_id()

    # Convert the timestamp into our standard format.
    timestamp = normalize_timestamp(
        receipt.timestamp
    )

    # Create the exact record that will be hashed.
    canonical_record = canonicalize_record(
        receipt_id=receipt_id,
        agent_id=receipt.agent_id,
        action=receipt.action,
        timestamp=timestamp,
        authorization_status=receipt.authorization_status,
        result_status=receipt.result_status,
        metadata=receipt.metadata,
    )

    # Calculate the SHA-256 hash.
    record_hash = calculate_hash(
        canonical_record
    )

    # Create the database object.
    db_receipt = Receipt(
        receipt_id=receipt_id,
        agent_id=receipt.agent_id,
        action=receipt.action,
        timestamp=timestamp,
        authorization_status=receipt.authorization_status,
        result_status=receipt.result_status,
        metadata_json=receipt.metadata,
        record_hash=record_hash,
    )

    # Save it to the database.
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)

    # Send the receipt back to the person who created it.
    return ReceiptResponse(
        receipt_id=db_receipt.receipt_id,
        agent_id=db_receipt.agent_id,
        action=db_receipt.action,
        timestamp=db_receipt.timestamp,
        authorization_status=db_receipt.authorization_status,
        result_status=db_receipt.result_status,
        metadata=db_receipt.metadata_json,
        record_hash=db_receipt.record_hash,
        verification_url=str(
            request.base_url
        ).rstrip("/") + f"/verify/{db_receipt.receipt_id}",
    )


@app.get("/receipts/{receipt_id}")
def get_receipt(
    receipt_id: str,
    db: Session = Depends(get_db),
):
    # Look for the receipt in the database.
    receipt = (
        db.query(Receipt)
        .filter(
            Receipt.receipt_id == receipt_id
        )
        .first()
    )

    # If it doesn't exist, return an error.
    if receipt is None:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    # Recreate the original record.
    canonical_record = canonicalize_record(
        receipt_id=receipt.receipt_id,
        agent_id=receipt.agent_id,
        action=receipt.action,
        timestamp=receipt.timestamp,
        authorization_status=receipt.authorization_status,
        result_status=receipt.result_status,
        metadata=receipt.metadata_json,
    )

    # Calculate the hash again.
    calculated_hash = calculate_hash(
        canonical_record
    )

    # Compare the newly calculated hash
    # against the hash stored in the database.
    verified = (
        calculated_hash == receipt.record_hash
    )

    return {
        "receipt_id": receipt.receipt_id,
        "agent_id": receipt.agent_id,
        "action": receipt.action,
        "timestamp": receipt.timestamp,
        "authorization_status": (
            receipt.authorization_status
        ),
        "result_status": receipt.result_status,
        "metadata": receipt.metadata_json,
        "record_hash": receipt.record_hash,
        "calculated_hash": calculated_hash,
        "verified": verified,
    }

@app.get("/verify/{receipt_id}")
def verify_page(
    receipt_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    receipt = (
        db.query(Receipt)
        .filter(
            Receipt.receipt_id == receipt_id
        )
        .first()
    )

    if receipt is None:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    canonical_record = canonicalize_record(
        receipt_id=receipt.receipt_id,
        agent_id=receipt.agent_id,
        action=receipt.action,
        timestamp=receipt.timestamp,
        authorization_status=receipt.authorization_status,
        result_status=receipt.result_status,
        metadata=receipt.metadata_json,
    )

    calculated_hash = calculate_hash(
        canonical_record
    )

@app.get("/quickstart")
def quickstart(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="quickstart.html",
        context={},
    )

    verified = (
        calculated_hash == receipt.record_hash
    )

    return templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={
            "receipt_id": receipt.receipt_id,
            "agent_id": receipt.agent_id,
            "action": receipt.action,
            "timestamp": receipt.timestamp,
            "authorization_status": (
                receipt.authorization_status
            ),
            "result_status": receipt.result_status,
            "record_hash": receipt.record_hash,
            "calculated_hash": calculated_hash,
            "verified": verified,
        },
    )