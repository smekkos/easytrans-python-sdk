"""
Integration tests — REST API: Customers, Carriers, Fleet, and Invoices.

Covers:
  - GET /v1/customers              (branch accounts only)
  - GET /v1/customers/{customerNo} (branch accounts only)
  - GET /v1/carriers               (branch accounts only)
  - GET /v1/carriers/{carrierNo}   (branch accounts only)
  - GET /v1/fleet                  (branch accounts only)
  - GET /v1/fleet/{fleetNo}        (branch accounts only)
  - GET /v1/invoices
  - GET /v1/invoices/{invoiceId}

Requirements:
  - EASYTRANS_SERVER, EASYTRANS_ENV, EASYTRANS_USERNAME, EASYTRANS_PASSWORD

Optional (enable single-item look-up tests):
  - EASYTRANS_REST_KNOWN_CUSTOMER_NO
  - EASYTRANS_REST_KNOWN_CARRIER_NO
  - EASYTRANS_REST_KNOWN_FLEET_NO
  - EASYTRANS_REST_KNOWN_INVOICE_ID

Note: customer, carrier, and fleet list endpoints require a **branch**
account. The tests will fail with an HTTP 401 or an empty result set when
run with a customer account — that is expected behaviour.
"""

import pytest

from easytrans.exceptions import EasyTransNotFoundError
from easytrans.rest_models import (
    PagedResponse,
    RestCarrier,
    RestCustomer,
    RestFleetVehicle,
    RestInvoice,
)


pytestmark = pytest.mark.integration


# ─────────────────────────────────────────────────────────────────────────────
# Customers
# ─────────────────────────────────────────────────────────────────────────────


class TestGetCustomers:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_customers()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_customer(self, rest_client):
        result = rest_client.get_customers()
        for customer in result.data:
            assert isinstance(customer, RestCustomer)

    def test_customer_no_positive(self, rest_client):
        result = rest_client.get_customers()
        for customer in result.data:
            assert customer.customer_no > 0

    def test_company_name_present(self, rest_client):
        result = rest_client.get_customers()
        for customer in result.data:
            assert isinstance(customer.company_name, str)

    def test_contacts_is_list(self, rest_client):
        result = rest_client.get_customers()
        for customer in result.data:
            assert isinstance(customer.contacts, list)

    def test_filter_by_company_name(self, rest_client):
        """Filtering by company name returns a subset."""
        all_items = rest_client.get_customers()
        if not all_items.data:
            pytest.skip("No customers in environment")
        fragment = all_items.data[0].company_name[:4]
        filtered = rest_client.get_customers(filter={"companyName": fragment})
        for c in filtered.data:
            assert fragment.lower() in c.company_name.lower()

    def test_sort_by_company_name(self, rest_client):
        """Verify the sort parameter is accepted; don't assert strict order
        because locale-dependent collation may differ from Python's str.lower."""
        result = rest_client.get_customers(sort="companyName")
        # Just check request succeeded and returned data of the right type
        assert isinstance(result.data, list)

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_customer(999999999)


class TestGetCustomer:
    def test_returns_rest_customer(self, rest_client, rest_known_customer_no):
        customer = rest_client.get_customer(rest_known_customer_no)
        assert isinstance(customer, RestCustomer)

    def test_id_matches(self, rest_client, rest_known_customer_no):
        customer = rest_client.get_customer(rest_known_customer_no)
        assert customer.customer_no == rest_known_customer_no

    def test_business_address_present(self, rest_client, rest_known_customer_no):
        customer = rest_client.get_customer(rest_known_customer_no)
        assert customer.business_address is not None
        assert customer.business_address.country != ""

    def test_contacts_are_structured(self, rest_client, rest_known_customer_no):
        customer = rest_client.get_customer(rest_known_customer_no)
        for contact in customer.contacts:
            assert isinstance(contact.name, str)


# ─────────────────────────────────────────────────────────────────────────────
# Carriers
# ─────────────────────────────────────────────────────────────────────────────


class TestGetCarriers:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_carriers()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_carrier(self, rest_client):
        result = rest_client.get_carriers()
        for carrier in result.data:
            assert isinstance(carrier, RestCarrier)

    def test_carrier_no_positive(self, rest_client):
        result = rest_client.get_carriers()
        for carrier in result.data:
            assert carrier.carrier_no > 0

    def test_carrier_attributes_is_list(self, rest_client):
        result = rest_client.get_carriers()
        for carrier in result.data:
            assert isinstance(carrier.carrier_attributes, list)

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_carrier(999999999)


class TestGetCarrier:
    def test_returns_rest_carrier(self, rest_client, rest_known_carrier_no):
        carrier = rest_client.get_carrier(rest_known_carrier_no)
        assert isinstance(carrier, RestCarrier)

    def test_id_matches(self, rest_client, rest_known_carrier_no):
        carrier = rest_client.get_carrier(rest_known_carrier_no)
        assert carrier.carrier_no == rest_known_carrier_no

    def test_contacts_structured(self, rest_client, rest_known_carrier_no):
        carrier = rest_client.get_carrier(rest_known_carrier_no)
        for contact in carrier.contacts:
            assert isinstance(contact.name, str)


# ─────────────────────────────────────────────────────────────────────────────
# Fleet
# ─────────────────────────────────────────────────────────────────────────────


class TestGetFleet:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_fleet()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_fleet_vehicle(self, rest_client):
        result = rest_client.get_fleet()
        for vehicle in result.data:
            assert isinstance(vehicle, RestFleetVehicle)

    def test_fleet_no_positive(self, rest_client):
        result = rest_client.get_fleet()
        for vehicle in result.data:
            assert vehicle.fleet_no > 0

    def test_filter_by_registration(self, rest_client):
        """Verify the filter parameter is accepted; don't assert count because
        some API versions use exact match instead of prefix match."""
        all_items = rest_client.get_fleet()
        if not all_items.data:
            pytest.skip("No fleet vehicles in environment")
        plate = next(
            (v.license_plate for v in all_items.data if v.license_plate),
            None,
        )
        if not plate:
            pytest.skip("No fleet vehicles with a license plate in environment")
        # Just verify the API accepts the filter without error
        filtered = rest_client.get_fleet(filter_registration=plate)
        assert isinstance(filtered, PagedResponse)

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_fleet_vehicle(999999999)


class TestGetFleetVehicle:
    def test_returns_rest_fleet_vehicle(self, rest_client, rest_known_fleet_no):
        vehicle = rest_client.get_fleet_vehicle(rest_known_fleet_no)
        assert isinstance(vehicle, RestFleetVehicle)

    def test_id_matches(self, rest_client, rest_known_fleet_no):
        vehicle = rest_client.get_fleet_vehicle(rest_known_fleet_no)
        assert vehicle.fleet_no == rest_known_fleet_no


# ─────────────────────────────────────────────────────────────────────────────
# Invoices
# ─────────────────────────────────────────────────────────────────────────────


class TestGetInvoices:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_invoices()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_invoice(self, rest_client):
        result = rest_client.get_invoices()
        for invoice in result.data:
            assert isinstance(invoice, RestInvoice)

    def test_invoice_id_positive(self, rest_client):
        result = rest_client.get_invoices()
        for invoice in result.data:
            assert invoice.invoice_id > 0

    def test_invoice_no_is_string(self, rest_client):
        result = rest_client.get_invoices()
        for invoice in result.data:
            assert isinstance(invoice.invoice_no, str)

    def test_filter_by_invoice_date_gte(self, rest_client):
        result = rest_client.get_invoices(filter={"invoiceDate": {"gte": "2020-01-01"}})
        for invoice in result.data:
            if invoice.invoice_date:
                assert invoice.invoice_date >= "2020-01-01"

    def test_include_customer_embeds_customer(self, rest_client):
        result = rest_client.get_invoices(include_customer=True)
        for invoice in result.data:
            if invoice.customer is not None:
                assert isinstance(invoice.customer, RestCustomer)
                assert invoice.customer.customer_no > 0

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_invoice(999999999)


class TestGetInvoice:
    def test_returns_rest_invoice(self, rest_client, rest_known_invoice_id):
        invoice = rest_client.get_invoice(rest_known_invoice_id)
        assert isinstance(invoice, RestInvoice)

    def test_id_matches(self, rest_client, rest_known_invoice_id):
        invoice = rest_client.get_invoice(rest_known_invoice_id)
        assert invoice.invoice_id == rest_known_invoice_id

    def test_with_customer_embedded(self, rest_client, rest_known_invoice_id):
        invoice = rest_client.get_invoice(rest_known_invoice_id, include_customer=True)
        if invoice.customer is not None:
            assert invoice.customer.customer_no > 0

    def test_with_pdf_field_is_str_or_none(self, rest_client, rest_known_invoice_id):
        invoice = rest_client.get_invoice(rest_known_invoice_id, include_invoice_pdf=True)
        assert invoice.invoice_pdf is None or isinstance(invoice.invoice_pdf, str)
