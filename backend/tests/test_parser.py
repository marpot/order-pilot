from datetime import date

from app.models.order import OrderStatus
from app.services.order_parser import DeterministicTextOrderParser


DEMO_TEXT = """Dzień dobry,

proszę o zamówienie:

20 x FILTR-X100
5 x POMPA-P20
10 x ZAWÓR-Z15

Dostawa do:
ABC Sp. z o.o.
ul. Przemysłowa 15
40-001 Katowice

Prosimy o dostawę do 30.09.2026.

Pozdrawiam
Jan Kowalski"""


def test_parser_extracts_demo_order() -> None:
    order = DeterministicTextOrderParser().parse(DEMO_TEXT)

    assert order.customer_name == "ABC Sp. z o.o."
    assert order.customer_email is None
    assert order.customer_tax_id is None
    assert order.delivery_address == "ul. Przemysłowa 15\n40-001 Katowice"
    assert order.delivery_date == date(2026, 9, 30)
    assert order.status == OrderStatus.NEW
    assert [(item.sku, item.quantity) for item in order.items] == [
        ("FILTR-X100", 20),
        ("POMPA-P20", 5),
        ("ZAWÓR-Z15", 10),
    ]


def test_parser_marks_incomplete_order_for_review() -> None:
    order = DeterministicTextOrderParser().parse("Dzień dobry, poproszę 2 x FILTR-X100")

    assert order.status == OrderStatus.NEEDS_REVIEW
    assert order.customer_name is None
    assert order.delivery_date is None


def test_parser_does_not_accept_invalid_date() -> None:
    order = DeterministicTextOrderParser().parse("Dostawa do:\nFirma X\nul. Testowa 1\n\nDostawa 31.02.2026")

    assert order.delivery_date is None
    assert order.status == OrderStatus.NEEDS_REVIEW

