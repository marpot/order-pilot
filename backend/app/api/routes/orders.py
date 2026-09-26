from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.order import Order, OrderHistory, OrderHistoryAction, OrderStatus
from app.schemas.order import OrderCreate, OrderHistoryRead, OrderRead, OrderUpdate
from app.services.orders import (
    InvalidStatusTransition,
    create_order,
    get_order,
    set_order_status,
    update_order,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[Order]:
    statement = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
    if status_filter:
        statement = statement.where(Order.status == status_filter)
    return list(db.scalars(statement).all())


@router.get("/{order_id}", response_model=OrderRead)
def read_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/{order_id}/history", response_model=list[OrderHistoryRead])
def read_order_history(order_id: int, db: Session = Depends(get_db)) -> list[OrderHistory]:
    if not get_order(db, order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    statement = (
        select(OrderHistory)
        .where(OrderHistory.order_id == order_id)
        .order_by(OrderHistory.timestamp.asc(), OrderHistory.id.asc())
    )
    return list(db.scalars(statement).all())


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def add_order(payload: OrderCreate, db: Session = Depends(get_db)) -> Order:
    return create_order(db, payload)


@router.patch("/{order_id}", response_model=OrderRead)
def edit_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)) -> Order:
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        return update_order(db, order, payload)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_order(order_id: int, db: Session = Depends(get_db)) -> Response:
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{order_id}/approve", response_model=OrderRead)
def approve_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not order.customer_name or not order.delivery_address or not order.delivery_date or not order.items:
        raise HTTPException(
            status_code=422,
            detail="Customer, delivery address, delivery date and at least one item are required",
        )
    try:
        return set_order_status(db, order, OrderStatus.APPROVED, OrderHistoryAction.APPROVED)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/reject", response_model=OrderRead)
def reject_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        return set_order_status(db, order, OrderStatus.REJECTED, OrderHistoryAction.REJECTED)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
