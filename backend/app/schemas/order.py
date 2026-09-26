from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.order import OrderHistoryAction, OrderSource, OrderStatus


class OrderItemBase(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    product_name: str | None = Field(default=None, max_length=255)
    quantity: int = Field(gt=0)
    unit: str = Field(default="szt.", min_length=1, max_length=32)

    @field_validator("sku", "unit")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    id: int
    order_id: int
    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    customer_name: str | None = Field(default=None, max_length=255)
    customer_email: EmailStr | None = None
    customer_tax_id: str | None = Field(default=None, max_length=32)
    delivery_address: str | None = None
    delivery_date: date | None = None
    source: OrderSource = OrderSource.MANUAL
    status: OrderStatus = OrderStatus.NEW
    original_content: str | None = None


class OrderCreate(OrderBase):
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    customer_name: str | None = Field(default=None, max_length=255)
    customer_email: EmailStr | None = None
    customer_tax_id: str | None = Field(default=None, max_length=32)
    delivery_address: str | None = None
    delivery_date: date | None = None
    source: OrderSource | None = None
    status: OrderStatus | None = None
    original_content: str | None = None
    items: list[OrderItemCreate] | None = None


class OrderRead(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]
    model_config = ConfigDict(from_attributes=True)


class OrderHistoryRead(BaseModel):
    id: int
    order_id: int
    action: OrderHistoryAction
    timestamp: datetime
    details: str | None
    model_config = ConfigDict(from_attributes=True)


class TextImportRequest(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)


class DashboardStats(BaseModel):
    total: int
    new: int
    needs_review: int
    approved: int
    rejected: int
    recent_orders: list[OrderRead]
