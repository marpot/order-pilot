from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderHistory, OrderHistoryAction, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate

ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.NEW: {OrderStatus.APPROVED, OrderStatus.REJECTED},
    OrderStatus.NEEDS_REVIEW: {OrderStatus.APPROVED, OrderStatus.REJECTED},
    OrderStatus.APPROVED: set(),
    OrderStatus.REJECTED: set(),
}


class InvalidStatusTransition(Exception):
    pass


def record_order_history(
    db: Session,
    order: Order,
    action: OrderHistoryAction,
    details: str | None = None,
) -> None:
    db.add(OrderHistory(order=order, action=action, details=details))


def create_order(
    db: Session,
    payload: OrderCreate,
    history_action: OrderHistoryAction | None = None,
    history_details: str | None = None,
) -> Order:
    item_data = payload.items
    order_data = payload.model_dump(exclude={"items"})
    order = Order(**order_data)
    order.items = [OrderItem(**item.model_dump()) for item in item_data]
    db.add(order)
    if history_action:
        record_order_history(db, order, history_action, history_details)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.scalar(select(Order).where(Order.id == order_id))


def update_order(db: Session, order: Order, payload: OrderUpdate) -> Order:
    changes = payload.model_dump(exclude_unset=True)
    item_data = changes.pop("items", None)
    requested_status = changes.pop("status", None)
    if requested_status is not None and requested_status != order.status:
        raise InvalidStatusTransition("Use the approve or reject action to change order status")
    actual_changes = {
        field: value for field, value in changes.items() if getattr(order, field) != value
    }
    for field, value in actual_changes.items():
        setattr(order, field, value)
    current_items = [
        {
            "sku": item.sku,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit": item.unit,
        }
        for item in order.items
    ]
    items_changed = item_data is not None and item_data != current_items
    if items_changed:
        order.items = [OrderItem(**item) for item in item_data]
    changed_fields = list(actual_changes)
    if items_changed:
        changed_fields.append("items")
    if not changed_fields:
        return order
    changed_fields_text = ", ".join(changed_fields)
    details = f"Changed fields: {changed_fields_text}" if changed_fields_text else None
    record_order_history(db, order, OrderHistoryAction.EDITED, details)
    db.commit()
    db.refresh(order)
    return order


def set_order_status(
    db: Session,
    order: Order,
    new_status: OrderStatus,
    action: OrderHistoryAction,
) -> Order:
    if new_status not in ALLOWED_STATUS_TRANSITIONS[order.status]:
        raise InvalidStatusTransition(
            f"Order cannot transition from {order.status.value} to {new_status.value}"
        )
    order.status = new_status
    record_order_history(db, order, action)
    db.commit()
    db.refresh(order)
    return order
