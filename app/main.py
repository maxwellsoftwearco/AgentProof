from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse
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


# Create database tables when the application starts.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AgentProof",
    description="Verifiable receipts for AI-agent actions.",
    version="0.1.0",
    docs_url="/api-docs",
    redoc_url=None,
)

templates = Jinja2Templates(
    directory="app/templates"
)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )


# ---------------------------------------------------------
# QUICK START
# ---------------------------------------------------------

@app.get("/quickstart")
def quickstart(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="quickstart.html",
        context={},
    )


# ---------------------------------------------------------
# USER-FRIENDLY DOCUMENTATION
# ---------------------------------------------------------

@app.get("/docs", response_class=HTMLResponse)
def docs(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="docs.html",
        context={},
    )


# ---------------------------------------------------------
# API KEY AUTHENTICATION
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# CREATE API KEY
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# CREATE RECEIPT
# ---------------------------------------------------------

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
    receipt_id = create_receipt_id()

    timestamp = normalize_timestamp(
        receipt.timestamp
    )

    canonical_record = canonicalize_record(
        receipt_id=receipt_id,
        agent_id=receipt.agent_id,
        action=receipt.action,
        timestamp=timestamp,
        authorization_status=receipt.authorization_status,
        result_status=receipt.result_status,
        metadata=receipt.metadata,
    )

    record_hash = calculate_hash(
        canonical_record
    )

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

    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)

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


# ---------------------------------------------------------
# GET RECEIPT DATA
# ---------------------------------------------------------

@app.get("/receipts/{receipt_id}")
def get_receipt(
    receipt_id: str,
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

    verified = (
        calculated_hash == receipt.record_hash
    )

    return {
        "receipt_id": receipt.receipt_id,
        "agent_id": receipt.agent_id,
        "action": receipt.action,
        "timestamp": receipt.timestamp,
        "authorization_status": receipt.authorization_status,
        "result_status": receipt.result_status,
        "metadata": receipt.metadata_json,
        "record_hash": receipt.record_hash,
        "calculated_hash": calculated_hash,
        "verified": verified,
    }


# ---------------------------------------------------------
# PUBLIC VERIFICATION PAGE
# ---------------------------------------------------------

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
            "authorization_status": receipt.authorization_status,
            "result_status": receipt.result_status,
            "record_hash": receipt.record_hash,
            "calculated_hash": calculated_hash,
            "verified": verified,
        },
    )