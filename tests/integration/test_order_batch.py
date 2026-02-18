"""
Integration test: batch order import (multiple orders in one request).

The 'extended' documentation example submits TWO orders in the same POST
body under the top-level "orders" array. This tests the client's
import_orders([order1, order2]) path end-to-end.

Key risks this test catches:
- total_orders == 2 (not 1) when two orders are sent
- total_order_destinations correctly sums across both orders
- total_order_packages correctly sums across both orders
- Both orders pass validation independently — the API doesn't short-circuit
  after the first one succeeds

Requires:
    EASYTRANS_TEST_PRODUCTNO   — a valid product number in your environment
    EASYTRANS_TEST_CUSTOMERNO  — required only for branch accounts (errorno 23)
"""

import pytest
from easytrans import Order
from easytrans.models import OrderResult

pytestmark = pytest.mark.integration


class TestBatchOrderImport:
    """Multiple orders submitted in a single import_orders() call."""

    def test_two_orders_accepted(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """Two orders in one batch are both validated successfully."""
        order1 = Order(
            productno=productno,
            customerno=customerno,
            date="2026-06-01",
            time="14:45",
            status="submit",
            remark="Batch order 1",
            external_id="integration-test-batch-001-a",
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )
        order2 = Order(
            productno=productno,
            customerno=customerno,
            date="2026-06-02",
            time="09:00",
            status="submit",
            remark="Batch order 2",
            external_id="integration-test-batch-001-b",
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order1, order2], mode="test")

        assert isinstance(result, OrderResult)
        assert result.mode == "test"
        assert result.total_orders == 2

    def test_batch_destination_count_is_sum_of_all_orders(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """
        total_order_destinations must equal the sum across all orders:
        2 destinations × 2 orders = 4.
        """
        order1 = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )
        order2 = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order1, order2], mode="test")

        assert result.total_order_destinations == 4

    def test_batch_package_count_is_sum_of_all_orders(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """
        total_order_packages must equal the sum across all orders:
        1 package line × 2 orders = 2.
        """
        order1 = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )
        order2 = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )

        result = real_client.import_orders([order1, order2], mode="test")

        assert result.total_order_packages == 2

    def test_batch_test_mode_creates_nothing(
        self, real_client, productno, customerno, simple_destinations, standard_packages
    ):
        """Test mode for a batch must still return empty new_ordernos."""
        orders = [
            Order(productno=productno, customerno=customerno, order_destinations=simple_destinations, order_packages=standard_packages),
            Order(productno=productno, customerno=customerno, order_destinations=simple_destinations, order_packages=standard_packages),
        ]

        result = real_client.import_orders(orders, mode="test")

        assert result.new_ordernos == []
        assert result.order_tracktrace == {}

    def test_mixed_status_batch_accepted(
        self, real_client, productno, customerno,
        simple_destinations, standard_packages, minimal_destinations
    ):
        """
        A batch containing one 'submit' order and one 'save' order is accepted.
        Also verifies that minimal and full-field destinations can coexist in
        the same batch request.
        """
        order_submit = Order(
            productno=productno,
            customerno=customerno,
            status="submit",
            order_destinations=simple_destinations,
            order_packages=standard_packages,
        )
        order_save = Order(
            productno=productno,
            customerno=customerno,
            status="save",
            order_destinations=minimal_destinations,
        )

        result = real_client.import_orders([order_submit, order_save], mode="test")

        assert result.total_orders == 2
