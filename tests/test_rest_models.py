"""
Unit tests for easytrans.rest_models.

These tests exercise the ``from_dict()`` deserialisation of every REST
response model using example payloads drawn directly from the OpenAPI spec.
No network calls are made.
"""

import pytest

from easytrans.rest_models import (
    PagedResponse,
    PaginationLinks,
    PaginationMeta,
    RestAddress,
    RestCarrier,
    RestCarrierContact,
    RestCustomer,
    RestCustomerContact,
    RestDestination,
    RestFleetVehicle,
    RestGoodsLine,
    RestInvoice,
    RestLocation,
    RestMailingAddress,
    RestOrder,
    RestOrderAttributes,
    RestPackageType,
    RestProduct,
    RestRate,
    RestSubstatus,
    RestTrackHistoryEntry,
    RestVehicleType,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures (OpenAPI example data)
# ─────────────────────────────────────────────────────────────────────────────

ADDRESS_DATA = {
    "address": "Keulenstraat",
    "houseno": "1",
    "address2": "Kantoor A3.5",
    "postcode": "7418 ET",
    "city": "DEVENTER",
    "country": "NL",
}

MAILING_ADDRESS_DATA = {**ADDRESS_DATA, "attn": "Accounts Payable"}

LOCATION_DATA = {"latitude": 6.1941298, "longitude": 52.2366999}

DESTINATION_DATA = {
    "addressId": 28416,
    "stopNo": 1,
    "taskType": "pickup",
    "company": "Demo customer",
    "contact": "Mr. Johnson",
    "address": "Keulenstraat",
    "houseno": "1",
    "address2": "Office A3.5",
    "postcode": "7418 ET",
    "city": "DEVENTER",
    "country": "NL",
    "location": LOCATION_DATA,
    "phone": "+3185 - 0479 475",
    "notes": "",
    "customerReference": "ABCDE12345",
    "waybillNo": "",
    "date": "2024-12-31",
    "fromTime": "10:00",
    "toTime": "10:00",
    "eta": None,
    "deliveryDate": None,
    "deliveryTime": None,
    "departureTime": None,
    "deliveryName": "",
    "signatureUrl": False,
    "photos": [],
    "documents": [],
    "carrierNotes": "",
}

GOODS_LINE_DATA = {
    "packageId": 21370,
    "packageNo": 1,
    "pickupDestination": 1,
    "deliveryDestination": 2,
    "amount": 16,
    "packageTypeNo": 1,
    "packageTypeName": "Colli",
    "weight": 10.0,
    "length": 50.0,
    "width": 40.0,
    "height": 30.0,
    "description": "Describe the contents of the box.",
}

RATE_DATA = {
    "rateNo": 388,
    "description": "Distance Small Van",
    "ratePerUnit": "0.51000",
    "subTotal": "50.49",
    "isMinimumAmount": False,
    "isPercentage": False,
}

TRACK_HISTORY_DATA = {
    "trackId": 6094,
    "name": "Order created",
    "location": "Deventer",
    "date": "2024-06-05",
    "time": "08:15",
}

CUSTOMER_CONTACT_DATA = {
    "userId": 271,
    "contactNo": 1,
    "salutation": 0,
    "name": "Demo user",
    "phone": "+3185 - 0479 475",
    "mobile": "+316 - 123 456 78",
    "email": "info@easytrans.nl",
    "useEmailForInvoice": False,
    "useEmailForReminder": False,
    "notes": "Head of logistics",
    "username": "klant",
}

CUSTOMER_DATA = {
    "type": "customer",
    "id": 2001,
    "createdAt": "2023-12-01T10:05:01+01:00",
    "updatedAt": "2023-12-01T10:05:01+01:00",
    "attributes": {
        "customerNo": 2001,
        "companyName": "EasyTrans Software B.V.",
        "businessAddress": ADDRESS_DATA,
        "mailingAddress": MAILING_ADDRESS_DATA,
        "website": "www.easytrans.nl",
        "debtorNo": "123475",
        "paymentReference": "ABCD1234",
        "paymentPeriod": 21,
        "paymentPeriodEndOfMonth": False,
        "ibanNo": "NL63INGB0004511811",
        "bicCode": "INGBNL2A",
        "bankNo": "",
        "ukSortCode": "",
        "vatNo": "NL864120576B01",
        "vatLiable": True,
        "vatLiableCode": 1,
        "chamberOfCommerceNo": "86861239",
        "eoriNo": "",
        "language": "en",
        "notes": "Register at reception before loading",
        "crmNotes": "Agreed rates based on 50 orders per month",
        "invoiceSurcharge": 5.5,
        "active": True,
        "contacts": [CUSTOMER_CONTACT_DATA],
        "externalId": "550e8400-e29b-41d4-a716-446655440000",
    },
}

CARRIER_CONTACT_DATA = {
    "userId": 5,
    "name": "Contact one",
    "phone": "+3185 - 0479 475",
    "mobile": "",
    "email": "info@easytrans.nl",
    "notes": "Available Mon-Thu",
    "username": "import",
}

CARRIER_DATA = {
    "type": "carrier",
    "id": 44,
    "createdAt": "2023-12-01T10:05:01+01:00",
    "updatedAt": "2023-12-01T10:05:01+01:00",
    "attributes": {
        "carrierNo": 44,
        "name": "External carrier",
        "businessAddress": ADDRESS_DATA,
        "mailingAddress": MAILING_ADDRESS_DATA,
        "phone": "+3185 - 0479 475",
        "mobile": "",
        "email": "info@easytrans.nl",
        "emailPurchaseInvoice": "",
        "website": "www.easytrans.nl",
        "notes": "Available Mon-Thu",
        "creditorNo": "123475",
        "paymentPeriod": 30,
        "paymentPeriodEndOfMonth": False,
        "ibanNo": "NL63INGB0004511811",
        "bicCode": "INGBNL2A",
        "bankNo": "",
        "ukSortCode": "",
        "vatNo": "NL864120576B01",
        "vatLiable": True,
        "vatLiableCode": 1,
        "chamberOfCommerceNo": "86861239",
        "licenseNo": "123456789",
        "carrierAttributes": ["charter_regular", "refrigerated"],
        "language": "nl",
        "active": True,
        "contacts": [CARRIER_CONTACT_DATA],
        "externalId": "18aa59a6-7eef-4491-837a-8ac2f04c0b6e",
    },
}

ORDER_DATA = {
    "type": "order",
    "id": 35558,
    "createdAt": "2023-12-01T10:05:01+01:00",
    "updatedAt": "2023-12-01T10:05:01+01:00",
    "attributes": {
        "orderNo": 35558,
        "date": "2023-12-01",
        "time": "08:00",
        "status": "planned",
        "substatusNo": 12,
        "substatusName": "Out for delivery",
        "collected": True,
        "productNo": 1,
        "productName": "Direct transport",
        "customerNo": 2001,
        "customerUserId": 271,
        "carrierNo": 44,
        "carrierUserId": 5,
        "branchNo": 0,
        "vehicleTypeNo": 2,
        "vehicleTypeName": "Small Van",
        "fleetNo": 5,
        "waybillNotes": "3 pallets and 16 boxes",
        "invoiceNotes": "P/O number: A12345",
        "purchaseInvoiceNotes": "Payment period 30 days",
        "internalNotes": "Upload POD before signing-off",
        "recipientEmail": "info@example.com",
        "distance": 99,
        "orderPrice": "132.48",
        "orderPurchasePrice": "294.82",
        "prepaidAmount": "0.00",
        "readyForPurchaseInvoice": True,
        "usernameCreated": "Demo planner",
        "usernameAssigned": "Demo planner",
        "invoiceId": 0,
        "trackingId": "GIYDAMJNGM2TKNJY",
        "externalId": "550e8400-e29b-41d4-a716-446655440000",
        "destinations": [DESTINATION_DATA],
        "goods": [GOODS_LINE_DATA],
        "customer": CUSTOMER_DATA,
        "carrier": CARRIER_DATA,
        "salesRates": [RATE_DATA],
        "purchaseRates": [],
        "trackHistory": [TRACK_HISTORY_DATA],
    },
}

ORDER_LIST_RESPONSE = {
    "data": [ORDER_DATA],
    "links": {
        "first": "http://localhost/v1/orders?page=1",
        "last": "http://localhost/v1/orders?page=1",
        "prev": None,
        "next": None,
    },
    "meta": {
        "current_page": 1,
        "from": 1,
        "last_page": 1,
        "per_page": 100,
        "to": 1,
        "total": 1,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Pagination models
# ─────────────────────────────────────────────────────────────────────────────


class TestPaginationLinks:
    def test_from_dict_all_fields(self):
        links = PaginationLinks.from_dict(
            {
                "first": "http://example.com?page=1",
                "last": "http://example.com?page=5",
                "prev": "http://example.com?page=2",
                "next": "http://example.com?page=4",
            }
        )
        assert links.first == "http://example.com?page=1"
        assert links.last == "http://example.com?page=5"
        assert links.prev == "http://example.com?page=2"
        assert links.next == "http://example.com?page=4"

    def test_from_dict_last_page(self):
        links = PaginationLinks.from_dict(
            {"first": "http://x?page=1", "last": "http://x?page=1", "prev": None, "next": None}
        )
        assert links.next is None
        assert links.prev is None

    def test_from_dict_empty(self):
        links = PaginationLinks.from_dict({})
        assert links.first is None
        assert links.next is None


class TestPaginationMeta:
    def test_from_dict(self):
        meta = PaginationMeta.from_dict(
            {"current_page": 3, "last_page": 10, "per_page": 100, "total": 950, "from": 201, "to": 300}
        )
        assert meta.current_page == 3
        assert meta.last_page == 10
        assert meta.per_page == 100
        assert meta.total == 950
        assert meta.from_record == 201
        assert meta.to_record == 300

    def test_from_dict_defaults(self):
        meta = PaginationMeta.from_dict({})
        assert meta.current_page == 1
        assert meta.total == 0


class TestPagedResponse:
    def test_has_next_false_when_no_next_link(self):
        response = PagedResponse.from_dict(ORDER_LIST_RESPONSE, RestOrder)
        assert response.has_next is False
        assert response.links.next is None

    def test_has_next_true_when_next_link_present(self):
        data = {
            **ORDER_LIST_RESPONSE,
            "links": {**ORDER_LIST_RESPONSE["links"], "next": "http://localhost/v1/orders?page=2"},
        }
        response = PagedResponse.from_dict(data, RestOrder)
        assert response.has_next is True
        assert "page=2" in response.links.next

    def test_data_count(self):
        response = PagedResponse.from_dict(ORDER_LIST_RESPONSE, RestOrder)
        assert len(response.data) == 1

    def test_meta_total(self):
        response = PagedResponse.from_dict(ORDER_LIST_RESPONSE, RestOrder)
        assert response.meta.total == 1

    def test_empty_data_list(self):
        raw = {
            "data": [],
            "links": {"first": None, "last": None, "prev": None, "next": None},
            "meta": {"current_page": 1, "last_page": 1, "per_page": 100, "total": 0},
        }
        response = PagedResponse.from_dict(raw, RestOrder)
        assert response.data == []
        assert response.has_next is False


# ─────────────────────────────────────────────────────────────────────────────
# Shared sub-models
# ─────────────────────────────────────────────────────────────────────────────


class TestRestAddress:
    def test_from_dict(self):
        addr = RestAddress.from_dict(ADDRESS_DATA)
        assert addr.address == "Keulenstraat"
        assert addr.houseno == "1"
        assert addr.postcode == "7418 ET"
        assert addr.city == "DEVENTER"
        assert addr.country == "NL"

    def test_from_dict_none(self):
        assert RestAddress.from_dict(None) is None


class TestRestMailingAddress:
    def test_attn_field(self):
        addr = RestMailingAddress.from_dict(MAILING_ADDRESS_DATA)
        assert addr.attn == "Accounts Payable"
        assert addr.city == "DEVENTER"

    def test_from_dict_none(self):
        assert RestMailingAddress.from_dict(None) is None


class TestRestLocation:
    def test_from_dict(self):
        loc = RestLocation.from_dict(LOCATION_DATA)
        assert loc.latitude == pytest.approx(6.1941298)
        assert loc.longitude == pytest.approx(52.2366999)

    def test_from_dict_none(self):
        assert RestLocation.from_dict(None) is None

    def test_from_dict_empty_dict(self):
        assert RestLocation.from_dict({}) is None


class TestRestDestination:
    def test_basic_fields(self):
        dest = RestDestination.from_dict(DESTINATION_DATA)
        assert dest.address_id == 28416
        assert dest.stop_no == 1
        assert dest.task_type == "pickup"
        assert dest.company == "Demo customer"
        assert dest.customer_reference == "ABCDE12345"

    def test_location_nested(self):
        dest = RestDestination.from_dict(DESTINATION_DATA)
        assert dest.location is not None
        assert dest.location.latitude == pytest.approx(6.1941298)

    def test_signature_url_false(self):
        dest = RestDestination.from_dict(DESTINATION_DATA)
        assert dest.signature_url is False

    def test_signature_url_string(self):
        data = {**DESTINATION_DATA, "signatureUrl": "https://example.com/sig.png"}
        dest = RestDestination.from_dict(data)
        assert dest.signature_url == "https://example.com/sig.png"

    def test_empty_lists(self):
        dest = RestDestination.from_dict(DESTINATION_DATA)
        assert dest.photos == []
        assert dest.documents == []


class TestRestGoodsLine:
    def test_from_dict(self):
        goods = RestGoodsLine.from_dict(GOODS_LINE_DATA)
        assert goods.package_id == 21370
        assert goods.package_no == 1
        assert goods.amount == 16
        assert goods.package_type_name == "Colli"
        assert goods.weight == pytest.approx(10.0)


class TestRestRate:
    def test_from_dict(self):
        rate = RestRate.from_dict(RATE_DATA)
        assert rate.rate_no == 388
        assert rate.description == "Distance Small Van"
        assert rate.rate_per_unit == "0.51000"
        assert rate.sub_total == "50.49"
        assert rate.is_percentage is False

    def test_percentage_rate(self):
        data = {**RATE_DATA, "isPercentage": True, "rateNo": 391}
        rate = RestRate.from_dict(data)
        assert rate.is_percentage is True


class TestRestTrackHistoryEntry:
    def test_from_dict(self):
        entry = RestTrackHistoryEntry.from_dict(TRACK_HISTORY_DATA)
        assert entry.track_id == 6094
        assert entry.name == "Order created"
        assert entry.location == "Deventer"
        assert entry.date == "2024-06-05"
        assert entry.time == "08:15"


# ─────────────────────────────────────────────────────────────────────────────
# Customer
# ─────────────────────────────────────────────────────────────────────────────


class TestRestCustomerContact:
    def test_from_dict(self):
        contact = RestCustomerContact.from_dict(CUSTOMER_CONTACT_DATA)
        assert contact.user_id == 271
        assert contact.name == "Demo user"
        assert contact.email == "info@easytrans.nl"
        assert contact.use_email_for_invoice is False


class TestRestCustomer:
    def test_top_level_ids(self):
        customer = RestCustomer.from_dict(CUSTOMER_DATA)
        assert customer.id == 2001
        assert customer.created_at == "2023-12-01T10:05:01+01:00"

    def test_attributes_unpacked(self):
        customer = RestCustomer.from_dict(CUSTOMER_DATA)
        assert customer.customer_no == 2001
        assert customer.company_name == "EasyTrans Software B.V."
        assert customer.vat_no == "NL864120576B01"
        assert customer.language == "en"
        assert customer.external_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_business_address(self):
        customer = RestCustomer.from_dict(CUSTOMER_DATA)
        assert customer.business_address is not None
        assert customer.business_address.city == "DEVENTER"

    def test_mailing_address_attn(self):
        customer = RestCustomer.from_dict(CUSTOMER_DATA)
        assert customer.mailing_address is not None
        assert customer.mailing_address.attn == "Accounts Payable"

    def test_contacts_list(self):
        customer = RestCustomer.from_dict(CUSTOMER_DATA)
        assert len(customer.contacts) == 1
        assert customer.contacts[0].name == "Demo user"

    def test_invoice_surcharge(self):
        customer = RestCustomer.from_dict(CUSTOMER_DATA)
        assert customer.invoice_surcharge == pytest.approx(5.5)


# ─────────────────────────────────────────────────────────────────────────────
# Carrier
# ─────────────────────────────────────────────────────────────────────────────


class TestRestCarrierContact:
    def test_from_dict(self):
        contact = RestCarrierContact.from_dict(CARRIER_CONTACT_DATA)
        assert contact.user_id == 5
        assert contact.name == "Contact one"


class TestRestCarrier:
    def test_top_level_ids(self):
        carrier = RestCarrier.from_dict(CARRIER_DATA)
        assert carrier.id == 44
        assert carrier.carrier_no == 44

    def test_attributes(self):
        carrier = RestCarrier.from_dict(CARRIER_DATA)
        assert carrier.name == "External carrier"
        assert carrier.license_no == "123456789"
        assert carrier.language == "nl"

    def test_carrier_attributes_list(self):
        carrier = RestCarrier.from_dict(CARRIER_DATA)
        assert "charter_regular" in carrier.carrier_attributes
        assert "refrigerated" in carrier.carrier_attributes

    def test_contacts(self):
        carrier = RestCarrier.from_dict(CARRIER_DATA)
        assert len(carrier.contacts) == 1
        assert carrier.contacts[0].username == "import"


# ─────────────────────────────────────────────────────────────────────────────
# Order
# ─────────────────────────────────────────────────────────────────────────────


class TestRestOrderAttributes:
    def test_basic_fields(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert attrs.order_no == 35558
        assert attrs.status == "planned"
        assert attrs.tracking_id == "GIYDAMJNGM2TKNJY"
        assert attrs.collected is True

    def test_branch_only_fields(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert attrs.carrier_no == 44
        assert attrs.fleet_no == 5
        assert attrs.purchase_invoice_notes == "Payment period 30 days"

    def test_destinations_parsed(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert len(attrs.destinations) == 1
        assert attrs.destinations[0].task_type == "pickup"

    def test_goods_parsed(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert len(attrs.goods) == 1
        assert attrs.goods[0].amount == 16

    def test_embedded_customer(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert attrs.customer is not None
        assert attrs.customer.company_name == "EasyTrans Software B.V."

    def test_embedded_carrier(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert attrs.carrier is not None
        assert attrs.carrier.name == "External carrier"

    def test_sales_rates(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert len(attrs.sales_rates) == 1
        assert attrs.sales_rates[0].rate_no == 388

    def test_empty_purchase_rates(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert attrs.purchase_rates == []

    def test_track_history(self):
        attrs = RestOrderAttributes.from_dict(ORDER_DATA["attributes"])
        assert len(attrs.track_history) == 1
        assert attrs.track_history[0].name == "Order created"


class TestRestOrder:
    def test_from_dict(self):
        order = RestOrder.from_dict(ORDER_DATA)
        assert order.id == 35558
        assert order.created_at == "2023-12-01T10:05:01+01:00"

    def test_attributes_accessible(self):
        order = RestOrder.from_dict(ORDER_DATA)
        assert order.attributes.order_no == 35558
        assert order.attributes.external_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_no_embedded_customer_when_absent(self):
        bare_order_data = {
            **ORDER_DATA,
            "attributes": {**ORDER_DATA["attributes"], "customer": None, "carrier": None},
        }
        order = RestOrder.from_dict(bare_order_data)
        assert order.attributes.customer is None
        assert order.attributes.carrier is None


# ─────────────────────────────────────────────────────────────────────────────
# Reference data
# ─────────────────────────────────────────────────────────────────────────────


class TestRestProduct:
    def test_from_dict(self):
        data = {
            "type": "product",
            "id": 1,
            "attributes": {"productNo": 1, "name": "Direct transport"},
        }
        product = RestProduct.from_dict(data)
        assert product.id == 1
        assert product.product_no == 1
        assert product.name == "Direct transport"
        assert product.is_deleted is None


class TestRestSubstatus:
    def test_from_dict(self):
        data = {
            "type": "substatus",
            "id": 12,
            "attributes": {"substatusNo": 12, "name": "Out for delivery"},
        }
        substatus = RestSubstatus.from_dict(data)
        assert substatus.substatus_no == 12
        assert substatus.name == "Out for delivery"


class TestRestPackageType:
    def test_from_dict(self):
        data = {
            "type": "packagetype",
            "id": 18,
            "attributes": {"packageTypeNo": 18, "name": "Europallet"},
        }
        pkg = RestPackageType.from_dict(data)
        assert pkg.package_type_no == 18
        assert pkg.name == "Europallet"

    def test_is_deleted_present(self):
        data = {
            "type": "packagetype",
            "id": 18,
            "attributes": {"packageTypeNo": 18, "name": "Old type", "isDeleted": True},
        }
        pkg = RestPackageType.from_dict(data)
        assert pkg.is_deleted is True


class TestRestVehicleType:
    def test_from_dict(self):
        data = {
            "type": "vehicletype",
            "id": 2,
            "attributes": {"vehicleTypeNo": 2, "name": "Small Van"},
        }
        vt = RestVehicleType.from_dict(data)
        assert vt.vehicle_type_no == 2
        assert vt.name == "Small Van"


class TestRestFleetVehicle:
    def test_from_dict(self):
        data = {
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
        vehicle = RestFleetVehicle.from_dict(data)
        assert vehicle.fleet_no == 5
        assert vehicle.name == "Van 1"
        assert vehicle.license_plate == "AB-123-C"
        assert vehicle.vehicle_type_no == 2
        assert vehicle.active is True

    def test_registration_fallback(self):
        """API may return 'registration' instead of 'licensePlate'."""
        data = {
            "type": "fleet",
            "id": 5,
            "attributes": {
                "fleetNo": 5,
                "name": "Van 1",
                "registration": "VH-357-V",
                "vehicleTypeNo": 2,
                "active": True,
            },
        }
        vehicle = RestFleetVehicle.from_dict(data)
        assert vehicle.license_plate == "VH-357-V"


# ─────────────────────────────────────────────────────────────────────────────
# Invoice
# ─────────────────────────────────────────────────────────────────────────────


class TestRestInvoice:
    def test_from_dict_basic(self):
        data = {
            "type": "invoice",
            "id": 284,
            "attributes": {
                "invoiceId": 284,
                "invoiceNo": "2024-0001",
                "invoiceDate": "2024-05-30",
                "customerNo": 2001,
                "totalAmount": "132.48",
                "vatAmount": "27.82",
                "paid": True,
                "paidDate": "2025-08-09",
                "exported": False,
            },
        }
        invoice = RestInvoice.from_dict(data)
        assert invoice.id == 284
        assert invoice.invoice_id == 284
        assert invoice.invoice_no == "2024-0001"
        assert invoice.invoice_date == "2024-05-30"
        assert invoice.customer_no == 2001
        assert invoice.total_amount == "132.48"
        assert invoice.paid is True

    def test_no_embedded_customer(self):
        data = {
            "type": "invoice",
            "id": 284,
            "attributes": {"invoiceId": 284, "invoiceNo": 20240001, "customerNo": 2001},
        }
        invoice = RestInvoice.from_dict(data)
        assert invoice.customer is None

    def test_embedded_customer(self):
        data = {
            "type": "invoice",
            "id": 284,
            "attributes": {
                "invoiceId": 284,
                "invoiceNo": "2024-0001",
                "customerNo": 2001,
                "customer": CUSTOMER_DATA,
            },
        }
        invoice = RestInvoice.from_dict(data)
        assert invoice.customer is not None
        assert invoice.customer.company_name == "EasyTrans Software B.V."

    def test_invoice_no_coerced_to_str(self):
        """invoiceNo can be an integer in the API response."""
        data = {
            "type": "invoice",
            "id": 284,
            "attributes": {"invoiceId": 284, "invoiceNo": 20240001, "customerNo": 2001},
        }
        invoice = RestInvoice.from_dict(data)
        assert isinstance(invoice.invoice_no, str)
        assert invoice.invoice_no == "20240001"

    def test_pdf_field(self):
        data = {
            "type": "invoice",
            "id": 284,
            "attributes": {
                "invoiceId": 284,
                "invoiceNo": "2024-0001",
                "customerNo": 2001,
                "invoicePdf": "JVBERi0xLjQ...",
            },
        }
        invoice = RestInvoice.from_dict(data)
        assert invoice.invoice_pdf == "JVBERi0xLjQ..."
