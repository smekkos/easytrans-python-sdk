"""
Integration test: simple order import with all common fields.

Mirrors the 'simple' example from the official documentation:
  EasyTrans - JSON order import example - simple.json

Exercises all everyday request fields:
- Explicit collect_deliver on both destinations (0=pickup, 1=delivery)
- Full address block (houseno, addition, address2, country, telephone)
- customer_reference on delivery destination
- carrierno, vehicleno
- remark + remark_invoice
- email_receiver
- external_id (your own reference, round-tripped for correlation)
- One package line with amount, weight, length, width, height, description

Key risks this test catches:
- Exact field names in the serialized JSON match what the API expects
- collect_deliver integer values 0 and 1 are accepted
- Package fields are all transmitted with correct types (float, not int)
- external_id does not cause the API to reject the payload

Requires:
    EASYTRANS_TEST_PRODUCTNO   — a valid product number in your environment
    EASYTRANS_TEST_CUSTOMERNO  — required only for branch accounts (errorno 23)
"""

import pytest
from easytrans import Order
from easytrans.models import OrderResult

pytestmark = pytest.mark.integration


class TestSimpleOrderImport:
    """Full common-field order matching the 'simple' documentation example."""

    def test_simple_order_accepted(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """The complete simple order payload is accepted by the API."""
        order = Order(
            productno=productno,
            customerno=customerno,
            date="2026-06-01",
            time="14:45",
            status="submit",
            carrierno=0,
            vehicleno=0,
            remark="1 Euro pallet with brochures",
            remark_invoice="P/O Number: ABCD1234",
            email_receiver="info@example.com",
            external_id="integration-test-simple-001",
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert isinstance(result, OrderResult)
        assert result.mode == "test"
        assert result.total_orders == 1
        assert result.total_order_destinations == 2
        assert result.total_order_packages == 1

    def test_simple_order_counts_match_input(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """Destination and package counts in the response match what was sent."""
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.total_order_destinations == len(simple_destinations)
        assert result.total_order_packages == len(standard_packages)

    def test_simple_order_test_mode_creates_nothing(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """Test mode must return empty new_ordernos and empty order_tracktrace."""
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.new_ordernos == []
        assert result.order_tracktrace == {}

    def test_simple_order_with_status_save(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """status='save' (draft) is accepted by the API alongside 'submit'."""
        order = Order(
            productno=productno,
            customerno=customerno,
            status="save",
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.total_orders == 1

    def test_simple_order_default_mode_is_test(
        self, real_client, productno, customerno, simple_destinations
    ):
        """
        Client default_mode='test' is used when mode is not passed explicitly.
        Verifies the mode flows from client config through to the auth payload.
        """
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
        )

        # No explicit mode= argument; relies on client.default_mode
        result = real_client.import_orders([order])

        assert result.mode == "test"
