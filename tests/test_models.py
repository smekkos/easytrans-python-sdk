"""
Unit tests for data models.

Tests serialization, deserialization, and validation of all dataclass models.
"""

import pytest
from easytrans.models import (
    Order,
    Destination,
    Package,
    Document,
    Customer,
    CustomerContact,
    OrderResult,
    CustomerResult,
    OrderTrackTrace,
    WebhookPayload,
)
from easytrans.constants import CollectDeliver


class TestDestination:
    """Test Destination model."""

    def test_destination_to_dict(self):
        """Test Destination serialization."""
        dest = Destination(
            company_name="Test Company",
            address="Test Street",
            houseno="123",
            postal_code="1234AB",
            city="Amsterdam",
            country="NL",
            collect_deliver=CollectDeliver.PICKUP.value,
        )

        data = dest.to_dict()
        assert data["company_name"] == "Test Company"
        assert data["address"] == "Test Street"
        assert data["collect_deliver"] == 0

    def test_destination_from_dict(self):
        """Test Destination deserialization."""
        data = {
            "company_name": "Test Company",
            "address": "Test Street",
            "houseno": "123",
            "postal_code": "1234AB",
            "city": "Amsterdam",
        }

        dest = Destination.from_dict(data)
        assert dest.company_name == "Test Company"
        assert dest.address == "Test Street"

    def test_destination_with_documents(self):
        """Test Destination with uploaded documents."""
        dest = Destination(
            company_name="Test",
            documents=[
                Document(
                    name="Invoice",
                    type="pdf",
                    base64_content="base64encodedcontent==",
                )
            ],
        )

        data = dest.to_dict()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["type"] == "pdf"


class TestPackage:
    """Test Package model."""

    def test_package_to_dict(self):
        """Test Package serialization."""
        pkg = Package(
            amount=2.0,
            weight=150.0,
            length=120.0,
            width=80.0,
            height=50.0,
            description="Euro pallet",
        )

        data = pkg.to_dict()
        assert data["amount"] == 2.0
        assert data["weight"] == 150.0
        assert data["description"] == "Euro pallet"

    def test_package_from_dict(self):
        """Test Package deserialization."""
        data = {"amount": 3.0, "weight": 10.0, "description": "Boxes"}

        pkg = Package.from_dict(data)
        assert pkg.amount == 3.0
        assert pkg.weight == 10.0


class TestOrder:
    """Test Order model."""

    def test_order_validation_requires_destinations(self):
        """Test Order requires minimum 2 destinations."""
        with pytest.raises(ValueError) as exc_info:
            Order(productno=2, order_destinations=[])

        assert "minimum of 2 destinations" in str(exc_info.value)

    def test_order_to_dict(self, sample_destinations, sample_packages):
        """Test Order serialization."""
        order = Order(
            productno=2,
            date="2026-02-18",
            status="submit",
            external_id="test-123",
            order_destinations=sample_destinations,
            order_packages=sample_packages,
        )

        data = order.to_dict()
        assert data["productno"] == 2
        assert data["date"] == "2026-02-18"
        assert data["external_id"] == "test-123"
        assert len(data["order_destinations"]) == 2
        assert len(data["order_packages"]) == 1

    def test_order_from_dict(self):
        """Test Order deserialization."""
        data = {
            "productno": 2,
            "order_destinations": [
                {"company_name": "A", "postal_code": "1234AB", "city": "Amsterdam"},
                {"company_name": "B", "postal_code": "5678CD", "city": "Utrecht"},
            ],
            "order_packages": [{"amount": 1.0, "weight": 10.0}],
        }

        order = Order.from_dict(data)
        assert order.productno == 2
        assert len(order.order_destinations) == 2
        assert len(order.order_packages) == 1


class TestCustomer:
    """Test Customer model."""

    def test_customer_to_dict(self, sample_customer_contacts):
        """Test Customer serialization."""
        customer = Customer(
            company_name="Test Company",
            address="Main Street",
            houseno="1",
            postal_code="1234AB",
            city="Amsterdam",
            country="NL",
            external_id="cust-123",
            customer_contacts=sample_customer_contacts,
        )

        data = customer.to_dict()
        assert data["company_name"] == "Test Company"
        assert data["external_id"] == "cust-123"
        assert len(data["customer_contacts"]) == 1

    def test_customer_from_dict(self):
        """Test Customer deserialization."""
        data = {
            "company_name": "Test Company",
            "address": "Street",
            "customer_contacts": [
                {"contact_name": "John", "email": "john@test.com"}
            ],
        }

        customer = Customer.from_dict(data)
        assert customer.company_name == "Test Company"
        assert len(customer.customer_contacts) == 1


class TestOrderResult:
    """Test OrderResult model."""

    def test_order_result_from_dict(self, success_order_response):
        """Test OrderResult deserialization."""
        result = OrderResult.from_dict(success_order_response["result"])

        assert result.mode == "effect"
        assert result.total_orders == 1
        assert len(result.new_ordernos) == 1
        assert result.new_ordernos[0] == 29145
        assert "29145" in result.order_tracktrace

    def test_order_result_with_rates(self, success_order_response_with_rates):
        """Test OrderResult with rate information."""
        result = OrderResult.from_dict(success_order_response_with_rates["result"])

        assert result.order_rates is not None
        assert "29145" in result.order_rates
        rates = result.order_rates["29145"]
        assert rates.order_total_excluding_vat == 158.74


class TestCustomerResult:
    """Test CustomerResult model."""

    def test_customer_result_from_dict(self, success_customer_response):
        """Test CustomerResult deserialization."""
        result = CustomerResult.from_dict(success_customer_response["result"])

        assert result.mode == "effect"
        assert result.total_customers == 1
        assert len(result.new_customernos) == 1
        assert result.new_customernos[0] == 12345
        assert 12345 in result.new_userids


class TestWebhookPayload:
    """Test WebhookPayload model."""

    def test_webhook_from_dict(self, webhook_payload_finished):
        """Test WebhookPayload deserialization."""
        webhook = WebhookPayload.from_dict(webhook_payload_finished)

        assert webhook.companyId == 2000
        assert webhook.order.orderNo == 1234
        assert webhook.order.status == "finished"
        assert len(webhook.order.destinations) == 2

    def test_webhook_get_event_datetime(self, webhook_payload_finished):
        """Test parsing event datetime."""
        webhook = WebhookPayload.from_dict(webhook_payload_finished)
        
        dt = webhook.get_event_datetime()
        assert dt.year == 2026
        assert dt.month == 2
        assert dt.day == 18
