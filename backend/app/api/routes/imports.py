from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.order import Order, OrderHistoryAction
from app.schemas.extraction import ExtractionOutcome
from app.schemas.order import OrderRead, TextImportRequest
from app.services.extraction import HybridOrderExtractionService, LangflowExtractor
from app.services.file_import import (
    FileImportError,
    FileImportService,
    PDFTextExtractor,
    SpreadsheetOrderExtractor,
)
from app.services.metrics import IMPORTS
from app.services.order_parser import DeterministicTextOrderParser, OrderParser
from app.services.orders import create_order

router = APIRouter(prefix="/import", tags=["import"])
parser: OrderParser = DeterministicTextOrderParser()
settings = get_settings()
text_extraction = HybridOrderExtractionService(
    deterministic_parser=parser,
    ai_extractor=LangflowExtractor(settings),
    confidence_threshold=settings.ai_confidence_threshold,
)
file_import_service = FileImportService(
    settings=settings,
    spreadsheet_extractor=SpreadsheetOrderExtractor(settings),
    pdf_extractor=PDFTextExtractor(settings),
    text_extraction=text_extraction,
)


def persist_import(
    db: Session,
    outcome: ExtractionOutcome,
    filename: str | None = None,
) -> Order:
    details = [f"Source: {outcome.order.source.value}"]
    if filename:
        details.append(f"File: {filename}")
    if outcome.used_ai:
        details.append("AI: used")
    if outcome.warnings:
        details.append("Warnings: " + " | ".join(outcome.warnings))
    return create_order(
        db,
        outcome.order,
        history_action=OrderHistoryAction.IMPORTED,
        history_details="; ".join(details),
    )


@router.post("/text", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def import_text(payload: TextImportRequest, db: Session = Depends(get_db)) -> Order:
    try:
        order = persist_import(db, text_extraction.extract(payload.content))
        IMPORTS.labels(source="EMAIL", result="success").inc()
        return order
    except Exception:
        IMPORTS.labels(source="EMAIL", result="failure").inc()
        raise


@router.post("/file", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Order:
    filename = file.filename or "upload"
    source = filename.rsplit(".", 1)[-1].upper() if "." in filename else "UNKNOWN"
    try:
        content = await file.read(settings.max_upload_size_bytes + 1)
        outcome = file_import_service.extract(content, filename)
        order = persist_import(db, outcome, filename)
        IMPORTS.labels(source=outcome.order.source.value, result="success").inc()
        return order
    except FileImportError as exc:
        IMPORTS.labels(source=source, result="failure").inc()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()
