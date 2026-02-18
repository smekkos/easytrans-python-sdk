"""
Integration test: minimal order import.

Mirrors the 'minimal' example from the official documentation:
  EasyTrans - JSON order import example - minimal.json

This is the absolute minimum payload the API accepts — only company_name,
address, houseno, postal_code and city on each destination. No country,
no collect_deliver flag, no packages.

Key risks this test catches that unit tests cannot:
- _clean_dict() correctly strips None/empty fields so the API doesn't
  receive unknown/null keys it rejects
- The API really does accept destinations without collect_deliver
- Response parsing works when order_tracktrace is an empty dict
  (test mode never returns tracking numbers)

Requires:
    EASYTRANS_TEST_PRODUCTNO   — a valid product number in your environment
    EASYTRANS_TEST_CUSTOMERNO  — required only for branch accounts (errorno 23)
"""

import pytest
from easytrans import Order
from easytrans.models import OrderResult

pytestmark = pytest.mark.integration


class TestMinimalOrderImport:
    """Minimal two-destination order — just enough for the API to accept it."""

    def test_minimal_order_accepted_in_test_mode(
        self, real_client, productno, customerno, minimal_destinations
    ):
        """
        The API validates a minimal order and returns a successful test-mode result.

        In test mode:
        - result.mode == "test"
        - result.total_orders == 1
        - result.new_ordernos == []        (no order created)
        - result.order_tracktrace == {}    (no tracking in test mode)
        """
        order = Order(
            productno=productno,
            customerno=customerno,
            date="2026-06-01",
            time="14:45",
            status="submit",
            order_destinations=minimal_destinations,
        )

        result = real_client.import_orders([order], mode="test")

        assert isinstance(result, OrderResult)
        assert result.mode == "test"
        assert result.total_orders == 1
        assert result.total_order_destinations == 2
        assert result.total_order_packages == 0
        assert result.new_ordernos == []
        assert result.order_tracktrace == {}
        assert "test" in result.result_description.lower()

    def test_minimal_order_result_description_present(
        self, real_client, productno, customerno, minimal_destinations
    ):
        """The API always returns a human-readable result_description."""
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=minimal_destinations,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.result_description
        assert isinstance(result.result_description, str)
        assert len(result.result_description) > 0

    def test_minimal_order_no_rates_by_default(
        self, real_client, productno, customerno, minimal_destinations
    ):
        """Without return_rates=True the rates field is absent from the response."""
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=minimal_destinations,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.order_rates is None
