import io

from fastapi.testclient import TestClient
from openpyxl import Workbook
from reportlab.pdfgen import canvas


CSV_CONTENT = """customer,delivery_address,delivery_date,sku,quantity,unit
ABC Sp. z o.o.,ul. Przemyslowa 15 Katowice,2026-09-30,FILTR-X100,20,szt.
ABC Sp. z o.o.,ul. Przemyslowa 15 Katowice,2026-09-30,POMPA-P20,5,szt.
"""


def test_csv_import_creates_structured_order(client: TestClient) -> None:
    response = client.post(
        "/api/import/file",
        files={"file": ("order.csv", CSV_CONTENT.encode(), "text/csv")},
    )

    assert response.status_code == 201
    order = response.json()
    assert order["source"] == "CSV"
    assert order["status"] == "NEW"
    assert [(item["sku"], item["quantity"]) for item in order["items"]] == [
        ("FILTR-X100", 20),
        ("POMPA-P20", 5),
    ]
    history = client.get(f"/api/orders/{order['id']}/history").json()
    assert history[0]["action"] == "IMPORTED"
    assert "Source: CSV" in history[0]["details"]


def test_incomplete_csv_requires_review(client: TestClient) -> None:
    content = "sku,quantity\nFILTR-X100,2\n"
    response = client.post(
        "/api/import/file",
        files={"file": ("incomplete.csv", content.encode(), "text/csv")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "NEEDS_REVIEW"
    assert response.json()["customer_name"] is None


def test_xlsx_import(client: TestClient) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["customer", "delivery_address", "delivery_date", "sku", "quantity"])
    sheet.append(["ABC Sp. z o.o.", "ul. Przemyslowa 15", "2026-09-30", "ZAWOR-Z15", 10])
    stream = io.BytesIO()
    workbook.save(stream)

    response = client.post(
        "/api/import/file",
        files={
            "file": (
                "order.xlsx",
                stream.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["source"] == "XLSX"
    assert response.json()["items"][0]["sku"] == "ZAWOR-Z15"


def test_pdf_import(client: TestClient) -> None:
    stream = io.BytesIO()
    document = canvas.Canvas(stream)
    lines = [
        "20 x FILTR-X100",
        "Dostawa do:",
        "ABC Sp. z o.o.",
        "ul. Przemyslowa 15",
        "40-001 Katowice",
        "Dostawa do 30.09.2026.",
    ]
    for index, line in enumerate(lines):
        document.drawString(72, 780 - index * 20, line)
    document.save()

    response = client.post(
        "/api/import/file",
        files={"file": ("order.pdf", stream.getvalue(), "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["source"] == "PDF"
    assert response.json()["items"][0]["quantity"] == 20


def test_invalid_and_unreadable_files_return_controlled_errors(client: TestClient) -> None:
    unsupported = client.post(
        "/api/import/file",
        files={"file": ("order.txt", b"not supported", "text/plain")},
    )
    malformed_xlsx = client.post(
        "/api/import/file",
        files={"file": ("order.xlsx", b"not a workbook", "application/octet-stream")},
    )
    blank_pdf = client.post(
        "/api/import/file",
        files={"file": ("scan.pdf", _blank_pdf(), "application/pdf")},
    )

    assert unsupported.status_code == 415
    assert malformed_xlsx.status_code == 422
    assert blank_pdf.status_code == 422
    assert "OCR" in blank_pdf.json()["detail"]


def _blank_pdf() -> bytes:
    stream = io.BytesIO()
    document = canvas.Canvas(stream)
    document.showPage()
    document.save()
    return stream.getvalue()
