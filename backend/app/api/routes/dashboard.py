from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.schemas.order import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    counts = dict(
        db.execute(select(Order.status, func.count(Order.id)).group_by(Order.status)).all()
    )
    recent = list(db.scalars(select(Order).order_by(Order.created_at.desc(), Order.id.desc()).limit(5)).all())
    return DashboardStats(
        total=sum(counts.values()),
        new=counts.get(OrderStatus.NEW, 0),
        needs_review=counts.get(OrderStatus.NEEDS_REVIEW, 0),
        approved=counts.get(OrderStatus.APPROVED, 0),
        rejected=counts.get(OrderStatus.REJECTED, 0),
        recent_orders=recent,
    )

