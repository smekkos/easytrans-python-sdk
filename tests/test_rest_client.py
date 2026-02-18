"""
Unit tests for the REST transport layer of EasyTransClient.

All HTTP calls are intercepted by the ``responses`` library — no real
network calls are made. Tests verify:
  - Correct URL construction
  - Authorization: Basic header on every REST request
  - Query-parameter encoding (filters, includes, sort, page)
  - Response model parsing
  - HTTP 4xx → appropriate exception mapping
"""

import base64
import json

import pytest
import responses as rsps_lib
from responses import RequestsMock

from easytrans import EasyTransClient
from easytrans.exceptions import (
    EasyTransAuthError,
    EasyTransNotFoundError,
    EasyTransRateLimitError,
    EasyTransValidationError,
)
from easytrans.rest_models import (
    PagedResponse,
    RestCarrier,
    RestCustomer,
    RestFleetVehicle,
    RestInvoice,
    RestOrder,
    RestPackageType,
    RestProduct,
    RestSubstatus,
    RestVehicleType,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

SERVER = "mytrans.nl"
ENV = "demo"
USER = "testuser"
PASS = "testpass"
REST_BASE = f"https://{SERVER}/{ENV}/api/v1"

EXPECTED_AUTH_HEADER = "Basic " + base64.b64encode(
    f"{USER}:{PASS}".encode()
).decode()


@pytest.fixture
def client():
    return EasyTransClient(
        server_url=SERVER,
        environment_name=ENV,
        username=USER,
        password=PASS,
        default_mode="test",
    )


def _pagination_envelope(data, next_url=None):
    """Helper that wraps a data list in a standard pagination envelope."""
    return {
        "data": data,
        "links": {
            "first": f"{REST_BASE}/orders?page=1",
            "last": None,
            "prev": None,
            "next": next_url,
        },
        "meta": {
            "current_page": 1,
            "last_page": 1,
            "per_page": 100,
            "total": len(data),
            "from": 1 if data else None,
            "to": len(data) if data else None,
        },
    }


MINIMAL_ORDER = {
    "type": "order",
    "id": 35558,
    "createdAt": "2023-12-01T10:05:01+01:00",
    "updatedAt": "2023-12-01T10:05:01+01:00",
    "attributes": {
        "orderNo": 35558,
        "status": "planned",
        "customerNo": 2001,
        "branchNo": 0,
        "invoiceId": 0,
        "destinations": [],
        "goods": [],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper: assert Basic Auth header
# ─────────────────────────────────────────────────────────────────────────────


def _assert_basic_auth(request):
    assert request.headers.get("Authorization") == EXPECTED_AUTH_HEADER, (
        "REST request must carry Authorization: Basic header"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Client construction
# ─────────────────────────────────────────────────────────────────────────────


class TestClientConstruction:
    def test_rest_base_url(self, client):
        assert client._rest_base_url == REST_BASE

    def test_rest_session_has_basic_auth(self, client):
        assert client._rest_session.headers.get("Authorization") == EXPECTED_AUTH_HEADER

    def test_close_does_not_raise(self, client):
        client.close()


# ─────────────────────────────────────────────────────────────────────────────
# _build_rest_params
# ─────────────────────────────────────────────────────────────────────────────


class TestBuildRestParams:
    def test_simple_filter(self, client):
        params = client._build_rest_params(filter={"status": "planned"})
        assert params["filter[status]"] == "planned"

    def test_operator_filter(self, client):
        params = client._build_rest_params(filter={"date": {"gte": "2024-01-01"}})
        assert params["filter[date][gte]"] == "2024-01-01"

    def test_multi_operator_filter(self, client):
        params = client._build_rest_params(
            filter={"orderNo": {"gte": 1000, "lt": 2000}}
        )
        assert params["filter[orderNo][gte]"] == 1000
        assert params["filter[orderNo][lt]"] == 2000

    def test_sort_param(self, client):
        params = client._build_rest_params(sort="-date")
        assert params["sort"] == "-date"

    def test_page_param(self, client):
        params = client._build_rest_params(page=3)
        assert params["page"] == 3

    def test_extra_kwargs_included(self, client):
        params = client._build_rest_params(include_customer="true")
        assert params["include_customer"] == "true"

    def test_none_extras_excluded(self, client):
        params = client._build_rest_params(include_carrier=None)
        assert "include_carrier" not in params

    def test_false_extras_excluded(self, client):
        params = client._build_rest_params(include_track_history=False)
        assert "include_track_history" not in params

    def test_empty_returns_empty_dict(self, client):
        params = client._build_rest_params()
        assert params == {}


# ─────────────────────────────────────────────────────────────────────────────
# Error handling
# ─────────────────────────────────────────────────────────────────────────────


class TestRestErrorHandling:
    @rsps_lib.activate
    def test_401_raises_auth_error(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json={"message": "Unauthenticated."},
            status=401,
        )
        with pytest.raises(EasyTransAuthError, match="401"):
            client.get_orders()

    @rsps_lib.activate
    def test_404_raises_not_found(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders/999",
            json={"message": "Not found."},
            status=404,
        )
        with pytest.raises(EasyTransNotFoundError, match="404"):
            client.get_order(999)

    @rsps_lib.activate
    def test_422_raises_validation_error(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={
                "message": "The given data was invalid.",
                "errors": {"externalId": ["Too long."]},
            },
            status=422,
        )
        with pytest.raises(EasyTransValidationError, match="422"):
            client.update_order(35558, external_id="x" * 200)

    @rsps_lib.activate
    def test_422_includes_field_errors(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={
                "message": "The given data was invalid.",
                "errors": {"externalId": ["Max 50 characters."]},
            },
            status=422,
        )
        with pytest.raises(EasyTransValidationError, match="Max 50 characters"):
            client.update_order(35558, external_id="x" * 200)

    @rsps_lib.activate
    def test_429_raises_rate_limit_error(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json={"message": "Too Many Attempts."},
            status=429,
        )
        with pytest.raises(EasyTransRateLimitError):
            client.get_orders()

    @rsps_lib.activate
    def test_500_raises_api_error(self, client):
        from easytrans.exceptions import EasyTransAPIError

        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json={"message": "Server error"},
            status=500,
        )
        with pytest.raises(EasyTransAPIError, match="500"):
            client.get_orders()


# ─────────────────────────────────────────────────────────────────────────────
# get_orders
# ─────────────────────────────────────────────────────────────────────────────


class TestGetOrders:
    @rsps_lib.activate
    def test_returns_paged_response(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([MINIMAL_ORDER]),
            status=200,
        )
        result = client.get_orders()
        assert isinstance(result, PagedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], RestOrder)

    @rsps_lib.activate
    def test_basic_auth_header_sent(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_orders()
        _assert_basic_auth(rsps_lib.calls[0].request)

    @rsps_lib.activate
    def test_filter_status_in_query(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_orders(filter={"status": "planned"})
        assert "filter%5Bstatus%5D=planned" in rsps_lib.calls[0].request.url or \
               "filter[status]=planned" in rsps_lib.calls[0].request.url

    @rsps_lib.activate
    def test_include_customer_flag(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_orders(include_customer=True)
        assert "include_customer=true" in rsps_lib.calls[0].request.url

    @rsps_lib.activate
    def test_include_track_history_flag(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_orders(include_track_history=True)
        assert "include_track_history=true" in rsps_lib.calls[0].request.url

    @rsps_lib.activate
    def test_sort_param(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_orders(sort="-date")
        assert "sort=-date" in rsps_lib.calls[0].request.url

    @rsps_lib.activate
    def test_has_next_true(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([MINIMAL_ORDER], next_url=f"{REST_BASE}/orders?page=2"),
            status=200,
        )
        result = client.get_orders()
        assert result.has_next is True


# ─────────────────────────────────────────────────────────────────────────────
# get_order
# ─────────────────────────────────────────────────────────────────────────────


class TestGetOrder:
    @rsps_lib.activate
    def test_returns_rest_order(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        order = client.get_order(35558)
        assert isinstance(order, RestOrder)
        assert order.id == 35558
        assert order.attributes.order_no == 35558

    @rsps_lib.activate
    def test_correct_url(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        client.get_order(35558)
        assert "/orders/35558" in rsps_lib.calls[0].request.url

    @rsps_lib.activate
    def test_not_found_raises(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders/0",
            json={"message": "Not found."},
            status=404,
        )
        with pytest.raises(EasyTransNotFoundError):
            client.get_order(0)


# ─────────────────────────────────────────────────────────────────────────────
# update_order
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateOrder:
    @rsps_lib.activate
    def test_put_method_used(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        client.update_order(35558, waybill_notes="New notes")
        assert rsps_lib.calls[0].request.method == "PUT"

    @rsps_lib.activate
    def test_only_supplied_fields_in_body(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        client.update_order(35558, waybill_notes="New notes")
        body = json.loads(rsps_lib.calls[0].request.body)
        assert "waybillNotes" in body
        assert "invoiceNotes" not in body

    @rsps_lib.activate
    def test_carrier_no_in_body(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        client.update_order(35558, carrier_no=44)
        body = json.loads(rsps_lib.calls[0].request.body)
        assert body["carrierNo"] == 44

    @rsps_lib.activate
    def test_carrier_no_zero_removes_carrier(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        client.update_order(35558, carrier_no=0)
        body = json.loads(rsps_lib.calls[0].request.body)
        assert body["carrierNo"] == 0

    @rsps_lib.activate
    def test_destinations_in_body(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        dest_update = [{"stopNo": 2, "date": "2024-12-31"}]
        client.update_order(35558, destinations=dest_update)
        body = json.loads(rsps_lib.calls[0].request.body)
        assert body["destinations"] == dest_update

    @rsps_lib.activate
    def test_returns_rest_order(self, client):
        rsps_lib.add(
            rsps_lib.PUT,
            f"{REST_BASE}/orders/35558",
            json={"data": MINIMAL_ORDER},
            status=200,
        )
        order = client.update_order(35558, waybill_notes="x")
        assert isinstance(order, RestOrder)


# ─────────────────────────────────────────────────────────────────────────────
# Reference data — products, substatuses, package types, vehicle types
# ─────────────────────────────────────────────────────────────────────────────


class TestGetProducts:
    @rsps_lib.activate
    def test_returns_paged_response(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/products",
            json=_pagination_envelope(
                [{"type": "product", "id": 1, "attributes": {"productNo": 1, "name": "Direct"}}]
            ),
            status=200,
        )
        result = client.get_products()
        assert isinstance(result, PagedResponse)
        assert result.data[0].product_no == 1

    @rsps_lib.activate
    def test_filter_name_in_query(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/products",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_products(filter_name="Direct")
        assert "Direct" in rsps_lib.calls[0].request.url


class TestGetProduct:
    @rsps_lib.activate
    def test_returns_rest_product(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/products/1",
            json={"data": {"type": "product", "id": 1, "attributes": {"productNo": 1, "name": "Direct"}}},
            status=200,
        )
        product = client.get_product(1)
        assert isinstance(product, RestProduct)
        assert product.product_no == 1


class TestGetSubstatuses:
    @rsps_lib.activate
    def test_returns_paged_response(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/substatuses",
            json=_pagination_envelope(
                [{"type": "substatus", "id": 12, "attributes": {"substatusNo": 12, "name": "OFD"}}]
            ),
            status=200,
        )
        result = client.get_substatuses()
        assert len(result.data) == 1
        assert isinstance(result.data[0], RestSubstatus)


class TestGetPackageTypes:
    @rsps_lib.activate
    def test_returns_paged_response(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/packagetypes",
            json=_pagination_envelope(
                [{"type": "packagetype", "id": 18, "attributes": {"packageTypeNo": 18, "name": "Europallet"}}]
            ),
            status=200,
        )
        result = client.get_package_types()
        assert isinstance(result.data[0], RestPackageType)
        assert result.data[0].name == "Europallet"


class TestGetVehicleTypes:
    @rsps_lib.activate
    def test_returns_paged_response(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/vehicletypes",
            json=_pagination_envelope(
                [{"type": "vehicletype", "id": 2, "attributes": {"vehicleTypeNo": 2, "name": "Small Van"}}]
            ),
            status=200,
        )
        result = client.get_vehicle_types()
        assert isinstance(result.data[0], RestVehicleType)
        assert result.data[0].name == "Small Van"


# ─────────────────────────────────────────────────────────────────────────────
# Customers
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_CUSTOMER = {
    "type": "customer",
    "id": 2001,
    "createdAt": "2023-12-01T10:05:01+01:00",
    "updatedAt": "2023-12-01T10:05:01+01:00",
    "attributes": {
        "customerNo": 2001,
        "companyName": "EasyTrans B.V.",
        "contacts": [],
    },
}


class TestGetCustomers:
    @rsps_lib.activate
    def test_returns_rest_customer_list(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/customers",
            json=_pagination_envelope([MINIMAL_CUSTOMER]),
            status=200,
        )
        result = client.get_customers()
        assert isinstance(result.data[0], RestCustomer)
        assert result.data[0].customer_no == 2001

    @rsps_lib.activate
    def test_filter_by_company(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/customers",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_customers(filter={"companyName": "EasyTrans"})
        assert "companyName" in rsps_lib.calls[0].request.url


class TestGetCustomer:
    @rsps_lib.activate
    def test_single_customer(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/customers/2001",
            json={"data": MINIMAL_CUSTOMER},
            status=200,
        )
        customer = client.get_customer(2001)
        assert isinstance(customer, RestCustomer)
        assert customer.id == 2001


# ─────────────────────────────────────────────────────────────────────────────
# Carriers
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_CARRIER = {
    "type": "carrier",
    "id": 44,
    "createdAt": "2023-12-01T10:05:01+01:00",
    "updatedAt": "2023-12-01T10:05:01+01:00",
    "attributes": {
        "carrierNo": 44,
        "name": "External carrier",
        "contacts": [],
        "carrierAttributes": [],
    },
}


class TestGetCarriers:
    @rsps_lib.activate
    def test_returns_rest_carrier_list(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/carriers",
            json=_pagination_envelope([MINIMAL_CARRIER]),
            status=200,
        )
        result = client.get_carriers()
        assert isinstance(result.data[0], RestCarrier)
        assert result.data[0].carrier_no == 44


class TestGetCarrier:
    @rsps_lib.activate
    def test_single_carrier(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/carriers/44",
            json={"data": MINIMAL_CARRIER},
            status=200,
        )
        carrier = client.get_carrier(44)
        assert isinstance(carrier, RestCarrier)
        assert carrier.carrier_no == 44


# ─────────────────────────────────────────────────────────────────────────────
# Fleet
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_FLEET_VEHICLE = {
    "type": "fleet",
    "id": 5,
    "attributes": {
        "fleetNo": 5,
        "name": "Van 1",
        "licensePlate": "AB-123-C",
        "vehicleTypeNo": 2,
        "active": True,
    },
}


class TestGetFleet:
    @rsps_lib.activate
    def test_returns_fleet_list(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/fleet",
            json=_pagination_envelope([MINIMAL_FLEET_VEHICLE]),
            status=200,
        )
        result = client.get_fleet()
        assert isinstance(result.data[0], RestFleetVehicle)
        assert result.data[0].fleet_no == 5

    @rsps_lib.activate
    def test_filter_registration(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/fleet",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_fleet(filter_registration="AB-123-C")
        assert "AB-123-C" in rsps_lib.calls[0].request.url


class TestGetFleetVehicle:
    @rsps_lib.activate
    def test_single_vehicle(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/fleet/5",
            json={"data": MINIMAL_FLEET_VEHICLE},
            status=200,
        )
        vehicle = client.get_fleet_vehicle(5)
        assert isinstance(vehicle, RestFleetVehicle)
        assert vehicle.license_plate == "AB-123-C"


# ─────────────────────────────────────────────────────────────────────────────
# Invoices
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_INVOICE = {
    "type": "invoice",
    "id": 284,
    "attributes": {
        "invoiceId": 284,
        "invoiceNo": "2024-0001",
        "invoiceDate": "2024-05-30",
        "customerNo": 2001,
    },
}


class TestGetInvoices:
    @rsps_lib.activate
    def test_returns_invoice_list(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/invoices",
            json=_pagination_envelope([MINIMAL_INVOICE]),
            status=200,
        )
        result = client.get_invoices()
        assert isinstance(result.data[0], RestInvoice)
        assert result.data[0].invoice_id == 284

    @rsps_lib.activate
    def test_include_invoice_pdf_flag(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/invoices",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_invoices(include_invoice_pdf=True)
        assert "include_invoice=true" in rsps_lib.calls[0].request.url

    @rsps_lib.activate
    def test_filter_invoice_date_gte(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/invoices",
            json=_pagination_envelope([]),
            status=200,
        )
        client.get_invoices(filter={"invoiceDate": {"gte": "2024-01-01"}})
        assert "2024-01-01" in rsps_lib.calls[0].request.url


class TestGetInvoice:
    @rsps_lib.activate
    def test_single_invoice(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/invoices/284",
            json={"data": MINIMAL_INVOICE},
            status=200,
        )
        invoice = client.get_invoice(284)
        assert isinstance(invoice, RestInvoice)
        assert invoice.invoice_id == 284

    @rsps_lib.activate
    def test_not_found(self, client):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/invoices/0",
            json={"message": "Not found."},
            status=404,
        )
        with pytest.raises(EasyTransNotFoundError):
            client.get_invoice(0)


# ─────────────────────────────────────────────────────────────────────────────
# Context manager
# ─────────────────────────────────────────────────────────────────────────────


class TestContextManager:
    @rsps_lib.activate
    def test_context_manager_usage(self):
        rsps_lib.add(
            rsps_lib.GET,
            f"{REST_BASE}/orders",
            json=_pagination_envelope([]),
            status=200,
        )
        with EasyTransClient(SERVER, ENV, USER, PASS) as c:
            result = c.get_orders()
        assert isinstance(result, PagedResponse)
