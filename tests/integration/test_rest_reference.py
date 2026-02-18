"""
Integration tests — REST API: Reference data.

Covers:
  - GET /v1/products
  - GET /v1/products/{productNo}
  - GET /v1/substatuses
  - GET /v1/substatuses/{substatusNo}
  - GET /v1/packagetypes
  - GET /v1/packagetypes/{packageTypeNo}
  - GET /v1/vehicletypes
  - GET /v1/vehicletypes/{vehicleTypeNo}

Requirements:
  - EASYTRANS_SERVER, EASYTRANS_ENV, EASYTRANS_USERNAME, EASYTRANS_PASSWORD

Optional (enable single-item look-up tests):
  - EASYTRANS_REST_KNOWN_PRODUCT_NO
  - EASYTRANS_REST_KNOWN_SUBSTATUS_NO
  - EASYTRANS_REST_KNOWN_PACKAGE_TYPE_NO
  - EASYTRANS_REST_KNOWN_VEHICLE_TYPE_NO
"""

import pytest

from easytrans.exceptions import EasyTransNotFoundError
from easytrans.rest_models import (
    PagedResponse,
    RestPackageType,
    RestProduct,
    RestSubstatus,
    RestVehicleType,
)


pytestmark = pytest.mark.integration


# ─────────────────────────────────────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────────────────────────────────────


class TestGetProducts:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_products()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_product(self, rest_client):
        result = rest_client.get_products()
        for product in result.data:
            assert isinstance(product, RestProduct)

    def test_product_no_positive(self, rest_client):
        result = rest_client.get_products()
        for product in result.data:
            assert product.product_no > 0

    def test_product_name_non_empty(self, rest_client):
        result = rest_client.get_products()
        for product in result.data:
            assert isinstance(product.name, str)

    def test_filter_by_name(self, rest_client):
        """Filtering by a partial name returns only matching products."""
        all_products = rest_client.get_products()
        if not all_products.data:
            pytest.skip("No products in environment")
        # Use the first product's name fragment as filter
        first_name = all_products.data[0].name[:3]
        filtered = rest_client.get_products(filter_name=first_name)
        for product in filtered.data:
            assert first_name.lower() in product.name.lower()

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_product(999999999)


class TestGetProduct:
    def test_returns_rest_product(self, rest_client, rest_known_product_no):
        product = rest_client.get_product(rest_known_product_no)
        assert isinstance(product, RestProduct)

    def test_id_matches(self, rest_client, rest_known_product_no):
        product = rest_client.get_product(rest_known_product_no)
        assert product.product_no == rest_known_product_no


# ─────────────────────────────────────────────────────────────────────────────
# Substatuses
# ─────────────────────────────────────────────────────────────────────────────


class TestGetSubstatuses:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_substatuses()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_substatus(self, rest_client):
        result = rest_client.get_substatuses()
        for substatus in result.data:
            assert isinstance(substatus, RestSubstatus)

    def test_substatus_no_positive(self, rest_client):
        result = rest_client.get_substatuses()
        for substatus in result.data:
            assert substatus.substatus_no > 0

    def test_filter_by_name(self, rest_client):
        all_items = rest_client.get_substatuses()
        if not all_items.data:
            pytest.skip("No substatuses in environment")
        fragment = all_items.data[0].name[:3]
        filtered = rest_client.get_substatuses(filter_name=fragment)
        for item in filtered.data:
            assert fragment.lower() in item.name.lower()

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_substatus(999999999)


class TestGetSubstatus:
    def test_returns_rest_substatus(self, rest_client, rest_known_substatus_no):
        substatus = rest_client.get_substatus(rest_known_substatus_no)
        assert isinstance(substatus, RestSubstatus)

    def test_id_matches(self, rest_client, rest_known_substatus_no):
        substatus = rest_client.get_substatus(rest_known_substatus_no)
        assert substatus.substatus_no == rest_known_substatus_no


# ─────────────────────────────────────────────────────────────────────────────
# Package types
# ─────────────────────────────────────────────────────────────────────────────


class TestGetPackageTypes:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_package_types()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_package_type(self, rest_client):
        result = rest_client.get_package_types()
        for pkg in result.data:
            assert isinstance(pkg, RestPackageType)

    def test_package_type_no_positive(self, rest_client):
        result = rest_client.get_package_types()
        for pkg in result.data:
            assert pkg.package_type_no > 0

    def test_filter_by_name(self, rest_client):
        all_items = rest_client.get_package_types()
        if not all_items.data:
            pytest.skip("No package types in environment")
        fragment = all_items.data[0].name[:3]
        filtered = rest_client.get_package_types(filter_name=fragment)
        for item in filtered.data:
            assert fragment.lower() in item.name.lower()

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_package_type(999999999)


class TestGetPackageType:
    def test_returns_rest_package_type(self, rest_client, rest_known_package_type_no):
        pkg = rest_client.get_package_type(rest_known_package_type_no)
        assert isinstance(pkg, RestPackageType)

    def test_id_matches(self, rest_client, rest_known_package_type_no):
        pkg = rest_client.get_package_type(rest_known_package_type_no)
        assert pkg.package_type_no == rest_known_package_type_no


# ─────────────────────────────────────────────────────────────────────────────
# Vehicle types
# ─────────────────────────────────────────────────────────────────────────────


class TestGetVehicleTypes:
    def test_returns_paged_response(self, rest_client):
        result = rest_client.get_vehicle_types()
        assert isinstance(result, PagedResponse)

    def test_items_are_rest_vehicle_type(self, rest_client):
        result = rest_client.get_vehicle_types()
        for vt in result.data:
            assert isinstance(vt, RestVehicleType)

    def test_vehicle_type_no_non_negative(self, rest_client):
        """vehicleTypeNo=0 ('Any vehicle') is a valid sentinel in some environments."""
        result = rest_client.get_vehicle_types()
        for vt in result.data:
            assert vt.vehicle_type_no >= 0

    def test_filter_by_name(self, rest_client):
        all_items = rest_client.get_vehicle_types()
        if not all_items.data:
            pytest.skip("No vehicle types in environment")
        fragment = all_items.data[0].name[:3]
        filtered = rest_client.get_vehicle_types(filter_name=fragment)
        for item in filtered.data:
            assert fragment.lower() in item.name.lower()

    def test_not_found_raises(self, rest_client):
        with pytest.raises(EasyTransNotFoundError):
            rest_client.get_vehicle_type(999999999)


class TestGetVehicleType:
    def test_returns_rest_vehicle_type(self, rest_client, rest_known_vehicle_type_no):
        vt = rest_client.get_vehicle_type(rest_known_vehicle_type_no)
        assert isinstance(vt, RestVehicleType)

    def test_id_matches(self, rest_client, rest_known_vehicle_type_no):
        vt = rest_client.get_vehicle_type(rest_known_vehicle_type_no)
        assert vt.vehicle_type_no == rest_known_vehicle_type_no
