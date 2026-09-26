from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.order import OrderCreate, OrderItemCreate


class AIExtractionResult(BaseModel):
    customer_name: str | None = Field(default=None, max_length=255)
    customer_email: EmailStr | None = None
    customer_tax_id: str | None = Field(default=None, max_length=32)
    delivery_address: str | None = None
    delivery_date: date | None = None
    items: list[OrderItemCreate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

    @field_validator("customer_name", "customer_tax_id", "delivery_address")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ExtractionOutcome(BaseModel):
    order: OrderCreate
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    used_ai: bool = False
