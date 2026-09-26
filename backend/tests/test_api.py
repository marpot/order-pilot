from fastapi.testclient import TestClient

from tests.test_parser import DEMO_TEXT


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_import_review_and_approve_flow(client: TestClient) -> None:
    imported = client.post("/api/import/text", json={"content": DEMO_TEXT})
    assert imported.status_code == 201
    order = imported.json()
    assert order["customer_name"] == "ABC Sp. z o.o."
    assert len(order["items"]) == 3

    updated = client.patch(
        f"/api/orders/{order['id']}",
        json={"customer_email": "orders@abc.example", "items": order["items"]},
    )
    assert updated.status_code == 200
    assert updated.json()["customer_email"] == "orders@abc.example"

    approved = client.post(f"/api/orders/{order['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert [entry["action"] for entry in client.get(f"/api/orders/{order['id']}/history").json()] == [
        "IMPORTED",
        "EDITED",
        "APPROVED",
    ]

    listed = client.get("/api/orders")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    stats = client.get("/api/dashboard/stats")
    assert stats.status_code == 200
    assert stats.json()["approved"] == 1


def test_incomplete_order_cannot_be_approved(client: TestClient) -> None:
    created = client.post(
        "/api/orders",
        json={"customer_name": "Incomplete", "status": "NEEDS_REVIEW", "items": []},
    )
    assert created.status_code == 201
    response = client.post(f"/api/orders/{created.json()['id']}/approve")
    assert response.status_code == 422


def test_delete_order(client: TestClient) -> None:
    created = client.post(
        "/api/orders",
        json={
            "customer_name": "Delete me",
            "delivery_date": "2026-10-01",
            "items": [{"sku": "TEST-1", "quantity": 1, "unit": "szt."}],
        },
    )
    order_id = created.json()["id"]
    assert client.delete(f"/api/orders/{order_id}").status_code == 204
    assert client.get(f"/api/orders/{order_id}").status_code == 404


def test_history_records_workflow_in_chronological_order(client: TestClient) -> None:
    imported = client.post("/api/import/text", json={"content": DEMO_TEXT})
    order_id = imported.json()["id"]

    initial_history = client.get(f"/api/orders/{order_id}/history")
    assert initial_history.status_code == 200
    assert [entry["action"] for entry in initial_history.json()] == ["IMPORTED"]
    assert initial_history.json()[0]["details"] == "Source: EMAIL"

    edited = client.patch(
        f"/api/orders/{order_id}",
        json={"customer_email": "orders@abc.example"},
    )
    assert edited.status_code == 200
    assert client.post(f"/api/orders/{order_id}/reject").status_code == 200

    history = client.get(f"/api/orders/{order_id}/history")
    assert history.status_code == 200
    entries = history.json()
    assert [entry["action"] for entry in entries] == [
        "IMPORTED",
        "EDITED",
        "REJECTED",
    ]
    assert entries[1]["details"] == "Changed fields: customer_email"
    assert [entry["id"] for entry in entries] == sorted(entry["id"] for entry in entries)


def test_history_returns_not_found_for_missing_order(client: TestClient) -> None:
    response = client.get("/api/orders/999/history")
    assert response.status_code == 404


def test_status_transition_rules_and_patch_bypass(client: TestClient) -> None:
    imported = client.post("/api/import/text", json={"content": DEMO_TEXT})
    order_id = imported.json()["id"]

    assert client.patch(f"/api/orders/{order_id}", json={"status": "APPROVED"}).status_code == 409
    assert client.post(f"/api/orders/{order_id}/approve").status_code == 200
    assert client.post(f"/api/orders/{order_id}/approve").status_code == 409
    assert client.post(f"/api/orders/{order_id}/reject").status_code == 409

    history = client.get(f"/api/orders/{order_id}/history").json()
    assert [entry["action"] for entry in history] == ["IMPORTED", "APPROVED"]


def test_noop_edit_does_not_create_history_entry(client: TestClient) -> None:
    imported = client.post("/api/import/text", json={"content": DEMO_TEXT})
    order_id = imported.json()["id"]
    assert client.patch(f"/api/orders/{order_id}", json={}).status_code == 200
    history = client.get(f"/api/orders/{order_id}/history").json()
    assert [entry["action"] for entry in history] == ["IMPORTED"]
