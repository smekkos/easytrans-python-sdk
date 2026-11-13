"""Regressions for the official JSON order import v5.4 contract."""

from easytrans import Document


def test_current_official_webhook_retains_scheduling_and_pod_documents():
    import json
    from pathlib import Path

    from easytrans import EasyTransClient

    payload = json.loads((Path(__file__).parent / "fixtures/webhook_v54.json").read_text())
    webhook = EasyTransClient.parse_webhook(payload)
    pickup, delivery = webhook.order.destinations
    assert pickup.date == "2026-02-04"
    assert pickup.fromTime == "09:30"
    assert pickup.toTime == "16:30"
    assert delivery.fromTime is None
    assert delivery.toTime is None
    assert pickup.taskResult.documents == []
    assert delivery.taskResult.documents == [
        {"name": "Document_1234_2.pdf", "base64EncodedDocument": "xxx"}
    ]


def test_document_category_is_optional_and_preserves_old_positional_shape():
    assert Document("pdf", "ZGF0YQ==", "Invoice").to_dict() == {
        "type": "pdf",
        "base64_content": "ZGF0YQ==",
        "name": "Invoice",
    }
    doc = Document.from_dict({"type": "pdf", "base64_content": "ZGF0YQ==", "category": "invoice"})
    assert doc.category == "invoice"
    assert doc.to_dict()["category"] == "invoice"


def test_destination_delivery_date_from_round_trip():
    from easytrans import Destination

    destination = Destination.from_dict(
        {"delivery_date_from": "2026-01-01", "delivery_date": "2026-01-02"}
    )
    assert destination.delivery_date_from == "2026-01-01"
    assert destination.to_dict()["delivery_date_from"] == "2026-01-01"
    assert "delivery_date_from" not in Destination().to_dict()


def test_order_customer_contact_userid_reaches_import_request():
    import json

    import responses

    from easytrans import Destination, EasyTransClient, Order

    with responses.RequestsMock() as http:
        http.post(
            "https://example.invalid/demo/import_json.php",
            json={
                "result": {
                    "mode": "test",
                    "total_orders": 1,
                    "total_order_destinations": 2,
                    "total_order_packages": 0,
                    "result_description": "Validated",
                    "new_ordernos": [],
                }
            },
        )
        client = EasyTransClient("example.invalid", "demo", "dummy", "dummy")
        order = Order(
            1,
            [
                Destination(
                    delivery_date_from="2026-01-01",
                    documents=[Document("pdf", "ZGF0YQ==", category="invoice")],
                ),
                Destination(),
            ],
            userid=123,
        )
        client.import_orders([order], mode="test")
        payload = json.loads(http.calls[0].request.body)
        assert payload["orders"][0]["userid"] == 123
        destination = payload["orders"][0]["order_destinations"][0]
        assert destination["delivery_date_from"] == "2026-01-01"
        assert destination["documents"][0]["category"] == "invoice"
        assert payload["authentication"]["mode"] == "test"
        assert "userid" not in Order(1, [Destination(), Destination()]).to_dict()
