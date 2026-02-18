"""
Integration tests — REST API: Orders.

Tests the ``GET /v1/orders``, ``GET /v1/orders/{orderNo}``, and
``PUT /v1/orders/{orderNo}`` endpoints against a live EasyTrans environment.

Requirements:
  - EASYTRANS_SERVER, EASYTRANS_ENV, EASYTRANS_USERNAME, EASYTRANS_PASSWORD
    must be set.
  - EASYTRANS_REST_KNOWN_ORDER_NO must be set to run single-order and
    include-flag tests.

All write tests (update_order) are strictly non-destructive: they only
assert the shape of the response, and use read-only flags (no status changes).
"""

import pytest

from easytrans import EasyTransClient
from easytrans.exceptions import EasyTransNotFoundError
from easytrans.rest_models import PagedResponse, RestOrder, RestDestination, RestGoodsLine


pytestmark = pytest.mark.integration


# ─────────────────────────────────────────────────────────────────────────────
# List orders
# ─────────────────────────────────────────────────────────────────────────────


class TestGetOrders:
    def test_returns_paged_response(self, rest_client):
        """A plain list call returns a valid PagedResponse."""
        result = rest_client.get_orders()
        assert isinstance(result, PagedResponse)

    def test_data_contains_rest_orders(self, rest_client):
        """Every item in data is a RestOrder."""
        result = rest_client.get_orders()
        for order in result.data:
            assert isinstance(order, RestOrder)

    def test_meta_fields_present(self, rest_client):
        """Pagination metadata is populated."""
        result = rest_client.get_orders()
        assert result.meta.per_page == 100
        assert result.meta.current_page >= 1
        assert result.meta.total >= 0

    def test_has_next_is_bool(self, rest_client):
        result = rest_client.get_orders()
        assert isinstance(result.has_next, bool)

    def test_filter_by_status_planned(self, rest_client):
        """Filtering by status=planned returns only planned orders (if any exist)."""
        result = rest_client.get_orders(filter={"status": "planned"})
        for order in result.data:
            assert order.attributes.status == "planned"

    def test_filter_by_status_finished(self, rest_client):
        """Filter by 'finished' — skip if this environment doesn't support that value."""
        from easytrans.exceptions import EasyTransAPIError
        try:
            result = rest_client.get_orders(filter={"status": "finished"})
        except EasyTransAPIError as exc:
            pytest.skip(f"Environment does not support filter[status]=finished: {exc}")
        for order in result.data:
            assert order.attributes.status == "finished"

    def test_sort_descending_order_no(self, rest_client):
        """Sorting by -orderNo returns orders in descending ID order."""
        result = rest_client.get_orders(sort="-orderNo")
        ids = [o.id for o in result.data]
        assert ids == sorted(ids, reverse=True) or len(ids) <= 1

    def test_include_customer_embeds_customer(self, rest_client):
        """include_customer=True embeds a customer record in each order."""
        result = rest_client.get_orders(include_customer=True)
        for order in result.data:
            if order.attributes.customer is not None:
                assert order.attributes.customer.customer_no > 0

    def test_include_track_history_embeds_list(self, rest_client):
        """include_track_history=True embeds an array (possibly empty)."""
        result = rest_client.get_orders(include_track_history=True)
        for order in result.data:
            assert isinstance(order.attributes.track_history, list)

    def test_include_sales_rates_embeds_list(self, rest_client):
        result = rest_client.get_orders(include_sales_rates=True)
        for order in result.data:
            assert isinstance(order.attributes.sales_rates, list)

    def test_destinations_are_rest_destination(self, rest_client):
        """Each destination inside an order is a RestDestination."""
        result = rest_client.get_orders()
        for order in result.data:
            for dest in order.attributes.destinations:
                assert isinstance(dest, RestDestination)

    def test_goods_are_rest_goods_line(self, rest_client):
        result = rest_client.get_orders()
        for order in result.data:
            for goods in order.attributes.goods:
                assert isinstance(goods, RestGoodsLine)

    def test_page_2_accessible_when_more_than_100(self, rest_client):
        """When there are more than 100 orders, page 2 returns results."""
        first_page = rest_client.get_orders()
        if first_page.meta.total > 100:
            second_page = rest_client.get_orders(page=2)
            assert len(second_page.data) > 0
            # IDs on page 2 should not overlap page 1
            page1_ids = {o.id for o in first_page.data}
            page2_ids = {o.id for o in second_page.data}
            assert page1_ids.isdisjoint(page2_ids)


# ─────────────────────────────────────────────────────────────────────────────
# Single order
# ─────────────────────────────────────────────────────────────────────────────


class TestGetOrder:
    def test_returns_rest_order(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no)
        assert isinstance(order, RestOrder)

    def test_id_matches_requested_number(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no)
        assert order.attributes.order_no == rest_known_order_no

    def test_created_at_present(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no)
        assert order.created_at is not None

    def test_with_track_history(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no, include_track_history=True)
        assert isinstance(order.attributes.track_history, list)

    def test_with_sales_rates(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no, include_sales_rates=True)
        assert isinstance(order.attributes.sales_rates, list)

    def test_with_customer_embedded(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no, include_customer=True)
        # Customer may or may not be present depending on account type
        if order.attributes.customer is not None:
            assert order.attributes.customer.customer_no > 0

    def test_destinations_have_stop_nos(self, rest_client, rest_known_order_no):
        order = rest_client.get_order(rest_known_order_no)
        for dest in order.attributes.destinations:
            assert dest.stop_no is not None

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_order(999999999)


# ─────────────────────────────────────────────────────────────────────────────
# Filter operators
# ─────────────────────────────────────────────────────────────────────────────


class TestOrderFilters:
    def test_filter_date_gte(self, rest_client):
        """filter[date][gte] returns only orders on or after the given date."""
        result = rest_client.get_orders(filter={"date": {"gte": "2020-01-01"}})
        for order in result.data:
            if order.attributes.date:
                assert order.attributes.date >= "2020-01-01"

    def test_filter_order_no_range(self, rest_client, rest_known_order_no):
        """filter[orderNo][gte] + filter[orderNo][lte] returns a bounded range."""
        result = rest_client.get_orders(
            filter={"orderNo": {"gte": rest_known_order_no, "lte": rest_known_order_no}}
        )
        assert any(o.attributes.order_no == rest_known_order_no for o in result.data)
