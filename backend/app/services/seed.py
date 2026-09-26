from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderSource, OrderStatus
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.orders import create_order


DEMO_ORDERS = [
    OrderCreate(
        customer_name="Nordex Polska Sp. z o.o.",
        customer_email="zamowienia@nordex.example",
        customer_tax_id="6342981234",
        delivery_address="ul. Magazynowa 8\n41-200 Sosnowiec",
        delivery_date=date(2026, 10, 2),
        source=OrderSource.EMAIL,
        status=OrderStatus.NEW,
        original_content="Prosimy o dostawę 12 szt. łożysk oraz 6 zestawów uszczelek.",
        items=[
            OrderItemCreate(sku="LOZ-6205", product_name="Łożysko 6205", quantity=12),
            OrderItemCreate(sku="USZ-P40", product_name="Zestaw uszczelek P40", quantity=6, unit="kpl."),
        ],
    ),
    OrderCreate(
        customer_name="Huta Silesia S.A.",
        customer_email="zakupy@silesia.example",
        delivery_address="Brama 4, ul. Hutnicza 22\n40-241 Katowice",
        delivery_date=date(2026, 10, 7),
        source=OrderSource.PDF,
        status=OrderStatus.NEEDS_REVIEW,
        original_content="Skan zamówienia ZP/441/2026 – adres dostawy wymaga potwierdzenia.",
        items=[OrderItemCreate(sku="FILTR-X100", product_name="Filtr przemysłowy X100", quantity=40)],
    ),
    OrderCreate(
        customer_name="Techmont Sp. z o.o.",
        customer_email="biuro@techmont.example",
        customer_tax_id="9542761180",
        delivery_address="ul. Stalowa 19\n43-100 Tychy",
        delivery_date=date(2026, 9, 29),
        source=OrderSource.XLSX,
        status=OrderStatus.APPROVED,
        original_content="Import z arkusza zamówień klienta.",
        items=[
            OrderItemCreate(sku="POMPA-P20", product_name="Pompa obiegowa P20", quantity=8),
            OrderItemCreate(sku="ZAWOR-Z15", product_name="Zawór Z15", quantity=24),
        ],
    ),
    OrderCreate(
        customer_name="Metal-Projekt s.c.",
        delivery_address="ul. Fabryczna 3\n44-100 Gliwice",
        source=OrderSource.MANUAL,
        status=OrderStatus.REJECTED,
        original_content="Zamówienie anulowane przez klienta.",
        items=[OrderItemCreate(sku="SRUBA-M12", product_name="Śruba M12", quantity=200)],
    ),
]


def seed_demo_data(db: Session) -> None:
    if (db.scalar(select(func.count(Order.id))) or 0) > 0:
        return
    for order in DEMO_ORDERS:
        create_order(db, order)

