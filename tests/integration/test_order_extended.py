"""
Integration test: extended multi-destination order with rates and documents.

Mirrors the 'extended' example from the official documentation:
  EasyTrans - JSON order import example - extended.json

This is the most important integration test because it exercises three
features that the unit-test mock responses only *assume* work correctly:

1. collect_deliver=2 (BOTH — pickup AND delivery at same stop)
2. Package routing via collect_destinationno / deliver_destinationno
3. return_rates=True — the real field names in OrderRate are verified
4. return_documents="label10x15" — the API accepts the parameter

Key risks caught that unit tests cannot:
- OrderRate field names: the mock has {"description": ..., "price": ...}
  but if the real API uses different keys the model would silently fail
- collect_deliver=2 (BOTH) may not be accepted in all demo environments
- ratetypeno=1 on a package must refer to a valid rate type
- Routed packages (collect_destinationno/deliver_destinationno) must
  reference destinationno values that actually exist in the same order

Requires:
    EASYTRANS_TEST_PRODUCTNO   — a valid product number in your environment
    EASYTRANS_TEST_CUSTOMERNO  — required only for branch accounts (errorno 23)
"""

import pytest
from easytrans import Order
from easytrans.models import OrderResult, OrderRate

pytestmark = pytest.mark.integration


class TestExtendedOrderImport:
    """Three-destination multi-stop order with routed packages."""

    def test_extended_order_accepted(
        self, real_client, productno, customerno, extended_destinations, routed_packages
    ):
        """A three-destination order with routed packages is accepted."""
        order = Order(
            productno=productno,
            customerno=customerno,
            date="2026-06-01",
            time="12:00",
            status="save",
            remark="Multi-stop integration test order",
            external_id="integration-test-extended-001",
            order_destinations=extended_destinations,
            order_packages=routed_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert isinstance(result, OrderResult)
        assert result.mode == "test"
        assert result.total_orders == 1
        assert result.total_order_destinations == 3
        assert result.total_order_packages == 2

    def test_collect_deliver_both_is_accepted(
        self, real_client, productno, customerno, extended_destinations, routed_packages
    ):
        """
        collect_deliver=2 (BOTH) on destination 2 must not cause a validation error.

        The unit tests never send a real payload with BOTH — this is the only
        test that confirms the integer value 2 is accepted by the server.
        """
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=extended_destinations,
            order_packages=routed_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.total_order_destinations == 3

    def test_return_rates_response_structure(
        self, real_client, productno, customerno, extended_destinations, routed_packages
    ):
        """
        return_rates=True causes the API to include rate information.

        Verifies the REAL field names inside OrderRate match what OrderRate.from_dict()
        expects. A mismatch here would raise a TypeError invisible in unit tests.
        """
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=extended_destinations,
            order_packages=routed_packages,
        )

        result = real_client.import_orders([order], mode="test", return_rates=True)

        if result.order_rates:
            for _orderno, rate in result.order_rates.items():
                assert isinstance(rate, OrderRate)
                assert isinstance(rate.order_total_excluding_vat, float)
                assert isinstance(rate.order_total_including_vat, float)
                assert rate.order_total_including_vat >= rate.order_total_excluding_vat
                assert isinstance(rate.rates, list)
                assert len(rate.rates) >= 1
                for rate_line in rate.rates:
                    assert "description" in rate_line
                    assert "price" in rate_line

    def test_return_documents_parameter_accepted(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """
        return_documents='label10x15' must not be rejected by the API.

        Uses the simpler two-destination fixture here because document
        generation depends on carrier configuration — we only verify the
        parameter is accepted without a validation error.
        """
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders(
            [order],
            mode="test",
            return_documents="label10x15",
        )

        assert result.total_orders == 1

    def test_delivery_time_window_fields_accepted(
        self, real_client, productno, customerno, extended_destinations, routed_packages
    ):
        """
        delivery_date, delivery_time, delivery_time_from on destinations
        are all accepted without rejection.
        """
        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=extended_destinations,
            order_packages=routed_packages,
        )

        result = real_client.import_orders([order], mode="test")

        assert result.mode == "test"
        assert result.total_orders == 1
