import re
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.models.order import OrderSource, OrderStatus
from app.schemas.order import OrderCreate, OrderItemCreate


class OrderParser(Protocol):
    def parse(self, content: str) -> OrderCreate: ...


@dataclass(frozen=True)
class ParsedAddress:
    customer_name: str | None
    delivery_address: str | None


class DeterministicTextOrderParser:
    """Small rule-based parser for the predictable email format used by the MVP."""

    item_pattern = re.compile(
        r"^\s*(?P<quantity>\d+)\s*(?:x|×|szt\.?|sztuk)\s+(?P<sku>[\wĄĆĘŁŃÓŚŹŻąćęłńóśźż.-]+)\s*$",
        re.IGNORECASE,
    )
    date_pattern = re.compile(r"\b(?P<day>\d{1,2})[.\-/](?P<month>\d{1,2})[.\-/](?P<year>\d{4})\b")
    email_pattern = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
    tax_id_pattern = re.compile(r"(?:NIP|VAT)\s*[:#]?\s*(\d[\d -]{7,13}\d)", re.IGNORECASE)

    def parse(self, content: str) -> OrderCreate:
        normalized = content.strip()
        items = self._parse_items(normalized)
        address = self._parse_delivery_block(normalized)
        delivery_date = self._parse_date(normalized)
        email_match = self.email_pattern.search(normalized)
        tax_match = self.tax_id_pattern.search(normalized)

        is_complete = bool(address.customer_name and address.delivery_address and delivery_date and items)
        return OrderCreate(
            customer_name=address.customer_name,
            customer_email=email_match.group(0) if email_match else None,
            customer_tax_id=self._clean_tax_id(tax_match.group(1)) if tax_match else None,
            delivery_address=address.delivery_address,
            delivery_date=delivery_date,
            source=OrderSource.EMAIL,
            status=OrderStatus.NEW if is_complete else OrderStatus.NEEDS_REVIEW,
            original_content=normalized,
            items=items,
        )

    def _parse_items(self, content: str) -> list[OrderItemCreate]:
        items: list[OrderItemCreate] = []
        for line in content.splitlines():
            match = self.item_pattern.match(line)
            if match:
                sku = match.group("sku").upper()
                items.append(
                    OrderItemCreate(
                        sku=sku,
                        product_name=sku,
                        quantity=int(match.group("quantity")),
                        unit="szt.",
                    )
                )
        return items

    def _parse_delivery_block(self, content: str) -> ParsedAddress:
        lines = [line.strip() for line in content.splitlines()]
        start = next(
            (index for index, line in enumerate(lines) if re.match(r"^dostawa\s+do\s*:", line, re.I)),
            None,
        )
        if start is None:
            return ParsedAddress(None, None)

        block: list[str] = []
        for line in lines[start + 1 :]:
            if not line:
                if block:
                    break
                continue
            if self.date_pattern.search(line) or re.match(r"^(prosimy|pozdrawiam)", line, re.I):
                break
            block.append(line)

        if not block:
            return ParsedAddress(None, None)
        customer_name = block[0]
        delivery_address = "\n".join(block[1:]) or None
        return ParsedAddress(customer_name, delivery_address)

    def _parse_date(self, content: str) -> date | None:
        match = self.date_pattern.search(content)
        if not match:
            return None
        try:
            return date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
        except ValueError:
            return None

    @staticmethod
    def _clean_tax_id(value: str) -> str:
        return re.sub(r"[ -]", "", value)
