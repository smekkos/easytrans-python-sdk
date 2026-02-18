#!/usr/bin/env python3
"""
Convert the intermediate api_intermediate.json into a full OpenAPI 3.1 YAML spec.

Usage:
    python scripts/intermediate_to_openapi.py
"""

import json
import re
import sys
from pathlib import Path
from collections import OrderedDict

import yaml

INTERMEDIATE_FILE = Path("EasyTrans Documentation/api_intermediate.json")
OUTPUT_FILE = Path("EasyTrans Documentation/openapi.yaml")


# ---------------------------------------------------------------------------
# YAML helpers — preserve key insertion order and produce clean output
# ---------------------------------------------------------------------------

class _OrderedDumper(yaml.Dumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


_OrderedDumper.add_representer(dict, _dict_representer)
_OrderedDumper.add_representer(OrderedDict, _dict_representer)


def dump_yaml(data) -> str:
    return yaml.dump(
        data,
        Dumper=_OrderedDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
        width=120,
    )


# ---------------------------------------------------------------------------
# Schema inference from JSON example values
# ---------------------------------------------------------------------------

def infer_schema(value, name: str = "") -> dict:
    """Recursively infer an OpenAPI schema from a Python value."""
    if value is None:
        return {"nullable": True, "type": "string"}  # OpenAPI 3.0 compat null
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number", "format": "float"}
    if isinstance(value, str):
        # Detect common formats
        if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
            return {"type": "string", "format": "date-time", "example": value}
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return {"type": "string", "format": "date", "example": value}
        if re.match(r"^\d{2}:\d{2}(:\d{2})?$", value):
            return {"type": "string", "format": "time", "example": value}
        return {"type": "string", "example": value}
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        # Use first element to infer item schema
        item_schema = infer_schema(value[0], name)
        return {"type": "array", "items": item_schema}
    if isinstance(value, dict):
        props = {}
        for k, v in value.items():
            props[k] = infer_schema(v, k)
        return {"type": "object", "properties": props}
    return {}


def schema_from_response_body(body: dict | list) -> dict:
    """Turn a full response body example into a schema."""
    return infer_schema(body)


# ---------------------------------------------------------------------------
# Extract well-known reusable schemas from the Orders GET example
# ---------------------------------------------------------------------------

SCHEMA_REFS = {
    "Address": None,
    "Location": None,
    "Destination": None,
    "GoodsLine": None,
    "CustomerContact": None,
    "Customer": None,
    "CarrierContact": None,
    "Carrier": None,
    "Rate": None,
    "TrackHistoryEntry": None,
    "Order": None,
    "OrderListResponse": None,
    "OrderSingleResponse": None,
    "PaginationLinks": None,
    "PaginationMeta": None,
    "PaginationMetaLink": None,
    "Product": None,
    "ProductListResponse": None,
    "ProductSingleResponse": None,
    "Substatus": None,
    "SubstatusListResponse": None,
    "SubstatusSingleResponse": None,
    "PackageType": None,
    "PackageTypeListResponse": None,
    "PackageTypeSingleResponse": None,
    "VehicleType": None,
    "VehicleTypeListResponse": None,
    "VehicleTypeSingleResponse": None,
    "Invoice": None,
    "InvoiceListResponse": None,
    "InvoiceSingleResponse": None,
    "CustomerListResponse": None,
    "CustomerSingleResponse": None,
    "CarrierListResponse": None,
    "CarrierSingleResponse": None,
    "FleetVehicle": None,
    "FleetListResponse": None,
    "FleetSingleResponse": None,
    "ErrorResponse": None,
    "ValidationErrorResponse": None,
}


def build_address_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "address": {"type": "string", "example": "Keulenstraat"},
            "houseno": {"type": "string", "example": "1"},
            "address2": {"type": "string", "example": "Kantoor A3.5"},
            "postcode": {"type": "string", "example": "7418 ET"},
            "city": {"type": "string", "example": "DEVENTER"},
            "country": {"type": "string", "example": "NL"},
        },
    }


def build_mailing_address_schema() -> dict:
    s = build_address_schema()
    s["properties"]["attn"] = {"type": "string", "example": "Accounts Payable"}
    return s


def build_location_schema() -> dict:
    return {
        "type": "object",
        "nullable": True,
        "properties": {
            "latitude": {"type": "number", "format": "float", "example": 6.1941298},
            "longitude": {"type": "number", "format": "float", "example": 52.2366999},
        },
    }


def build_destination_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "addressId": {"type": "integer", "example": 28416},
            "stopNo": {"type": "integer", "example": 1},
            "taskType": {
                "type": "string",
                "enum": ["pickup", "delivery"],
                "example": "pickup",
            },
            "company": {"type": "string", "example": "Demo customer"},
            "contact": {"type": "string", "example": "Mr. Johnson"},
            "address": {"type": "string", "example": "Keulenstraat"},
            "houseno": {"type": "string", "example": "1"},
            "address2": {"type": "string", "example": ""},
            "postcode": {"type": "string", "example": "7418 ET"},
            "city": {"type": "string", "example": "DEVENTER"},
            "country": {"type": "string", "example": "NL"},
            "location": {"$ref": "#/components/schemas/Location"},
            "phone": {"type": "string", "example": "+3185 - 0479 475"},
            "notes": {"type": "string", "example": ""},
            "customerReference": {"type": "string", "example": "ABCDE12345"},
            "waybillNo": {"type": "string", "example": "123456"},
            "date": {"type": "string", "format": "date", "example": "2024-12-31"},
            "fromTime": {"type": "string", "format": "time", "example": "10:00"},
            "toTime": {"type": "string", "format": "time", "example": "10:00"},
            "eta": {"type": "string", "nullable": True, "example": "00:00"},
            "deliveryDate": {"type": "string", "format": "date", "nullable": True},
            "deliveryTime": {"type": "string", "nullable": True, "example": "16:48"},
            "departureTime": {"type": "string", "nullable": True, "example": "17:06"},
            "deliveryName": {"type": "string", "example": "Mr. Johnson"},
            "signatureUrl": {
                "oneOf": [
                    {"type": "string", "format": "uri"},
                    {"type": "boolean"},
                ],
                "description": "URL to signature image, or false if no signature.",
                "example": False,
            },
            "photos": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of photo URLs.",
            },
            "documents": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of document URLs.",
            },
            "carrierNotes": {"type": "string", "example": "Delivered at the neighbours"},
        },
    }


def build_goods_line_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "packageId": {"type": "integer", "example": 21370},
            "packageNo": {"type": "integer", "example": 1},
            "pickupDestination": {"type": "integer", "example": 1},
            "deliveryDestination": {"type": "integer", "example": 2},
            "amount": {"type": "integer", "example": 16},
            "packageTypeNo": {"type": "integer", "example": 1},
            "packageTypeName": {"type": "string", "example": "Colli"},
            "weight": {"type": "number", "example": 10},
            "length": {"type": "number", "example": 50},
            "width": {"type": "number", "example": 40},
            "height": {"type": "number", "example": 30},
            "description": {"type": "string", "example": "Describe the contents of the box."},
        },
    }


def build_rate_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "rateNo": {"type": "integer", "example": 388},
            "description": {"type": "string", "example": "Distance Small Van"},
            "ratePerUnit": {"type": "string", "example": "0.51000"},
            "subTotal": {"type": "string", "example": "50.49"},
            "isMinimumAmount": {"type": "boolean", "example": False},
            "isPercentage": {"type": "boolean", "example": False},
        },
    }


def build_track_history_entry_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "trackId": {"type": "integer", "example": 6094},
            "name": {"type": "string", "example": "Order created"},
            "location": {"type": "string", "example": "Deventer"},
            "date": {"type": "string", "format": "date", "example": "2024-06-05"},
            "time": {"type": "string", "format": "time", "example": "08:15"},
        },
    }


def build_customer_contact_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "userId": {"type": "integer", "example": 271},
            "contactNo": {"type": "integer", "example": 1},
            "salutation": {"type": "integer", "example": 0},
            "name": {"type": "string", "example": "Demo user"},
            "phone": {"type": "string", "example": "+3185 - 0479 475"},
            "mobile": {"type": "string", "example": "+316 - 123 456 78"},
            "email": {"type": "string", "format": "email", "example": "info@easytrans.nl"},
            "useEmailForInvoice": {"type": "boolean", "example": False},
            "useEmailForReminder": {"type": "boolean", "example": False},
            "notes": {"type": "string", "example": "Head of logistics"},
            "username": {"type": "string", "example": "klant"},
        },
    }


def build_customer_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "customer"},
            "id": {"type": "integer", "example": 2001},
            "createdAt": {"type": "string", "format": "date-time"},
            "updatedAt": {"type": "string", "format": "date-time"},
            "attributes": {
                "type": "object",
                "properties": {
                    "customerNo": {"type": "integer", "example": 2001},
                    "companyName": {"type": "string", "example": "EasyTrans Software B.V."},
                    "businessAddress": {"$ref": "#/components/schemas/Address"},
                    "mailingAddress": {"$ref": "#/components/schemas/MailingAddress"},
                    "website": {"type": "string", "example": "www.easytrans.nl"},
                    "debtorNo": {"type": "string", "example": "123475"},
                    "paymentReference": {"type": "string", "example": "ABCD1234"},
                    "paymentPeriod": {"type": "integer", "example": 21},
                    "paymentPeriodEndOfMonth": {"type": "boolean", "example": False},
                    "ibanNo": {"type": "string", "example": "NL63INGB0004511811"},
                    "bicCode": {"type": "string", "example": "INGBNL2A"},
                    "bankNo": {"type": "string", "example": ""},
                    "ukSortCode": {"type": "string", "example": ""},
                    "vatNo": {"type": "string", "example": "NL864120576B01"},
                    "vatLiable": {"type": "boolean", "example": True},
                    "vatLiableCode": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Reason code indicating why a customer is not VAT liable.",
                        "example": 1,
                    },
                    "chamberOfCommerceNo": {"type": "string", "example": "86861239"},
                    "eoriNo": {"type": "string", "example": ""},
                    "language": {"type": "string", "example": "en"},
                    "notes": {"type": "string"},
                    "crmNotes": {"type": "string"},
                    "invoiceSurcharge": {"type": "number", "example": 5.5},
                    "active": {"type": "boolean", "example": True},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true (branch account only).",
                    },
                    "contacts": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/CustomerContact"},
                    },
                    "externalId": {
                        "type": "string",
                        "nullable": True,
                        "example": "550e8400-e29b-41d4-a716-446655440000",
                    },
                },
            },
        },
    }


def build_carrier_contact_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "userId": {"type": "integer", "example": 5},
            "name": {"type": "string", "example": "Contact one"},
            "phone": {"type": "string", "example": "+3185 - 0479 475"},
            "mobile": {"type": "string", "example": ""},
            "email": {"type": "string", "format": "email", "example": "info@easytrans.nl"},
            "notes": {"type": "string", "example": "Available Mon-Thu"},
            "username": {"type": "string", "example": "import"},
        },
    }


def build_carrier_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "carrier"},
            "id": {"type": "integer", "example": 44},
            "createdAt": {"type": "string", "format": "date-time"},
            "updatedAt": {"type": "string", "format": "date-time"},
            "attributes": {
                "type": "object",
                "properties": {
                    "carrierNo": {"type": "integer", "example": 44},
                    "name": {"type": "string", "example": "External carrier"},
                    "businessAddress": {"$ref": "#/components/schemas/Address"},
                    "mailingAddress": {"$ref": "#/components/schemas/MailingAddress"},
                    "phone": {"type": "string", "example": "+3185 - 0479 475"},
                    "mobile": {"type": "string", "example": ""},
                    "email": {"type": "string", "format": "email"},
                    "emailPurchaseInvoice": {"type": "string", "format": "email"},
                    "website": {"type": "string", "example": "www.easytrans.nl"},
                    "notes": {"type": "string"},
                    "creditorNo": {"type": "string", "example": "123475"},
                    "paymentPeriod": {"type": "integer", "example": 30},
                    "paymentPeriodEndOfMonth": {"type": "boolean", "example": False},
                    "ibanNo": {"type": "string", "example": "NL63INGB0004511811"},
                    "bicCode": {"type": "string", "example": "INGBNL2A"},
                    "bankNo": {"type": "string"},
                    "ukSortCode": {"type": "string"},
                    "vatNo": {"type": "string", "example": "NL864120576B01"},
                    "vatLiable": {"type": "boolean", "example": True},
                    "vatLiableCode": {
                        "type": "integer",
                        "nullable": True,
                        "description": "Reason code indicating why a carrier is not VAT liable.",
                    },
                    "chamberOfCommerceNo": {"type": "string"},
                    "licenseNo": {"type": "string", "example": "123456789"},
                    "carrierAttributes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["charter_regular", "refrigerated"],
                    },
                    "language": {"type": "string", "example": "nl"},
                    "active": {"type": "boolean", "example": True},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true (branch account only).",
                    },
                    "contacts": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/CarrierContact"},
                    },
                    "externalId": {
                        "type": "string",
                        "nullable": True,
                        "example": "18aa59a6-7eef-4491-837a-8ac2f04c0b6e",
                    },
                },
            },
        },
    }


def build_order_attributes_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "orderNo": {"type": "integer", "example": 35558},
            "date": {"type": "string", "format": "date", "example": "2023-12-01"},
            "time": {"type": "string", "format": "time", "example": "08:00"},
            "status": {
                "type": "string",
                "description": (
                    "Order status. Customer account values: quote, saved-weborder, "
                    "pending-acceptation, in-progress, finished. "
                    "Branch account values: quote, saved-weborder, pending-acceptation, "
                    "open, planned, signed-off, checked, invoiced."
                ),
                "enum": [
                    "quote",
                    "saved-weborder",
                    "pending-acceptation",
                    "in-progress",
                    "finished",
                    "open",
                    "planned",
                    "signed-off",
                    "checked",
                    "invoiced",
                ],
                "example": "planned",
            },
            "substatusNo": {"type": "integer", "nullable": True, "example": 12},
            "substatusName": {"type": "string", "nullable": True, "example": "Out for delivery"},
            "collected": {
                "type": "boolean",
                "description": "Indicates the driver has picked-up the goods (goods on board).",
                "example": True,
            },
            "productNo": {"type": "integer", "nullable": True, "example": 1},
            "productName": {"type": "string", "nullable": True, "example": "Direct transport"},
            "customerNo": {"type": "integer", "example": 2001},
            "customerUserId": {"type": "integer", "nullable": True, "example": 271},
            "carrierNo": {
                "type": "integer",
                "nullable": True,
                "description": "Branch account only.",
                "example": 44,
            },
            "carrierUserId": {
                "type": "integer",
                "nullable": True,
                "description": "Branch account only.",
                "example": 5,
            },
            "branchNo": {"type": "integer", "example": 0},
            "vehicleTypeNo": {"type": "integer", "nullable": True, "example": 2},
            "vehicleTypeName": {"type": "string", "nullable": True, "example": "Small Van"},
            "fleetNo": {
                "type": "integer",
                "nullable": True,
                "description": "Branch account only.",
                "example": 5,
            },
            "userId": {
                "type": "integer",
                "nullable": True,
                "description": "Branch account only. The contact of the customer that belongs to the order.",
            },
            "waybillNotes": {"type": "string", "example": "3 pallets and 16 boxes"},
            "invoiceNotes": {"type": "string", "example": "P/O number: A12345"},
            "purchaseInvoiceNotes": {
                "type": "string",
                "description": "Branch account only.",
                "example": "Payment period 30 days",
            },
            "internalNotes": {
                "type": "string",
                "description": "Branch account only.",
                "example": "Upload POD before signing-off",
            },
            "carrierNotes": {
                "type": "string",
                "description": "Branch account only.",
            },
            "recipientEmail": {"type": "string", "format": "email", "example": "info@example.com"},
            "distance": {
                "type": "integer",
                "description": "Distance in kilometres (EU) or miles (UK).",
                "example": 99,
            },
            "orderPrice": {"type": "string", "example": "132.48"},
            "orderPurchasePrice": {
                "type": "string",
                "description": "Branch account only.",
                "example": "294.82",
            },
            "prepaidAmount": {"type": "string", "example": "0.00"},
            "readyForPurchaseInvoice": {
                "type": "boolean",
                "description": "Branch account only.",
                "example": True,
            },
            "usernameCreated": {
                "type": "string",
                "nullable": True,
                "description": "Branch account only.",
                "example": "Demo planner",
            },
            "usernameAssigned": {
                "type": "string",
                "nullable": True,
                "description": "Branch account only.",
                "example": "Demo planner",
            },
            "invoiceId": {"type": "integer", "example": 0},
            "trackingId": {
                "type": "string",
                "description": (
                    "Track & Trace identifier. "
                    "Use in URL: https://www.YOUR_SERVER/YOUR_ENVIRONMENT/tracktrace.php?trackingnr={trackingId}"
                ),
                "example": "GIYDAMJNGM2TKNJY",
            },
            "externalId": {
                "type": "string",
                "nullable": True,
                "description": "Reference to the corresponding record in an external system.",
                "example": "550e8400-e29b-41d4-a716-446655440000",
            },
            "isDeleted": {
                "type": "boolean",
                "description": "Only present when include_deleted=true (branch account only).",
            },
            "destinations": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Destination"},
            },
            "goods": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/GoodsLine"},
            },
            "customer": {
                "allOf": [{"$ref": "#/components/schemas/Customer"}],
                "nullable": True,
                "description": "Only present when include_customer=true.",
            },
            "carrier": {
                "allOf": [{"$ref": "#/components/schemas/Carrier"}],
                "nullable": True,
                "description": "Only present when include_carrier=true (branch account only).",
            },
            "salesRates": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Rate"},
                "description": "Only present when include_sales_rates=true.",
            },
            "purchaseRates": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Rate"},
                "description": "Only present when include_purchase_rates=true (branch account only).",
            },
            "trackHistory": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/TrackHistoryEntry"},
                "description": "Only present when include_track_history=true.",
            },
        },
    }


def build_order_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "order"},
            "id": {"type": "integer", "example": 35558},
            "createdAt": {"type": "string", "format": "date-time", "example": "2023-12-01T10:05:01+01:00"},
            "updatedAt": {"type": "string", "format": "date-time", "example": "2023-12-01T10:05:01+01:00"},
            "attributes": {"$ref": "#/components/schemas/OrderAttributes"},
        },
    }


def build_pagination_links_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "first": {"type": "string", "format": "uri", "nullable": True},
            "last": {"type": "string", "format": "uri", "nullable": True},
            "prev": {"type": "string", "format": "uri", "nullable": True},
            "next": {"type": "string", "format": "uri", "nullable": True},
        },
    }


def build_pagination_meta_link_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri", "nullable": True},
            "label": {"type": "string"},
            "active": {"type": "boolean"},
        },
    }


def build_pagination_meta_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "current_page": {"type": "integer"},
            "from": {"type": "integer", "nullable": True},
            "last_page": {"type": "integer"},
            "links": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/PaginationMetaLink"},
            },
            "path": {"type": "string", "format": "uri"},
            "per_page": {"type": "integer", "example": 100},
            "to": {"type": "integer", "nullable": True},
            "total": {"type": "integer"},
        },
    }


def build_error_response_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "message": {"type": "string", "example": "Unauthenticated."},
        },
    }


def build_validation_error_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "message": {"type": "string", "example": "The given data was invalid."},
            "errors": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "example": {"orderNo": ["The order no field is required."]},
            },
        },
    }


def build_product_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "product"},
            "id": {"type": "integer", "example": 1},
            "attributes": {
                "type": "object",
                "properties": {
                    "productNo": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Direct transport"},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true (branch account only).",
                    },
                },
            },
        },
    }


def build_substatus_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "substatus"},
            "id": {"type": "integer", "example": 12},
            "attributes": {
                "type": "object",
                "properties": {
                    "substatusNo": {"type": "integer", "example": 12},
                    "name": {"type": "string", "example": "Out for delivery"},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true (branch account only).",
                    },
                },
            },
        },
    }


def build_package_type_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "packagetype"},
            "id": {"type": "integer", "example": 1},
            "attributes": {
                "type": "object",
                "properties": {
                    "packageTypeNo": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Colli"},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true (branch account only).",
                    },
                },
            },
        },
    }


def build_vehicle_type_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "vehicletype"},
            "id": {"type": "integer", "example": 2},
            "attributes": {
                "type": "object",
                "properties": {
                    "vehicleTypeNo": {"type": "integer", "example": 2},
                    "name": {"type": "string", "example": "Small Van"},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true (branch account only).",
                    },
                },
            },
        },
    }


def build_invoice_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "invoice"},
            "id": {"type": "integer", "example": 101},
            "attributes": {
                "type": "object",
                "properties": {
                    "invoiceId": {"type": "integer", "example": 101},
                    "invoiceNo": {"type": "string", "example": "2024-0001"},
                    "invoiceDate": {"type": "string", "format": "date"},
                    "customerNo": {"type": "integer", "example": 2001},
                    "totalAmount": {"type": "string", "example": "132.48"},
                    "vatAmount": {"type": "string", "example": "27.82"},
                    "paymentMethod": {
                        "type": "string",
                        "nullable": True,
                        "description": "Branch account only.",
                    },
                    "onlinePaymentStatus": {
                        "type": "string",
                        "nullable": True,
                        "description": "Branch account only.",
                    },
                    "discountPercentage": {
                        "type": "number",
                        "nullable": True,
                        "description": "Branch account only.",
                    },
                    "sentDate": {
                        "type": "string",
                        "format": "date",
                        "nullable": True,
                        "description": "Branch account only.",
                    },
                    "paid": {
                        "type": "boolean",
                        "description": "Branch account only.",
                    },
                    "paidDate": {
                        "type": "string",
                        "format": "date",
                        "nullable": True,
                        "description": "Branch account only.",
                    },
                    "exported": {
                        "type": "boolean",
                        "description": "Branch account only.",
                    },
                    "externalId": {
                        "type": "string",
                        "nullable": True,
                        "description": "Branch account only.",
                    },
                    "invoicePdf": {
                        "type": "string",
                        "format": "byte",
                        "description": "Base64 encoded PDF. Only present when include_invoice=true.",
                    },
                },
            },
        },
    }


def build_fleet_vehicle_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "example": "fleet"},
            "id": {"type": "integer", "example": 5},
            "attributes": {
                "type": "object",
                "properties": {
                    "fleetNo": {"type": "integer", "example": 5},
                    "name": {"type": "string", "example": "Van 1"},
                    "licensePlate": {"type": "string", "example": "AB-123-C"},
                    "vehicleTypeNo": {"type": "integer", "nullable": True, "example": 2},
                    "active": {"type": "boolean", "example": True},
                    "isDeleted": {
                        "type": "boolean",
                        "description": "Only present when include_deleted=true.",
                    },
                },
            },
        },
    }


def list_response_schema(item_ref: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"$ref": item_ref},
            },
            "links": {"$ref": "#/components/schemas/PaginationLinks"},
            "meta": {"$ref": "#/components/schemas/PaginationMeta"},
        },
    }


def single_response_schema(item_ref: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "data": {"$ref": item_ref},
        },
    }


# ---------------------------------------------------------------------------
# Component schemas registry
# ---------------------------------------------------------------------------

def build_components_schemas() -> dict:
    return {
        "Address": build_address_schema(),
        "MailingAddress": build_mailing_address_schema(),
        "Location": build_location_schema(),
        "Destination": build_destination_schema(),
        "GoodsLine": build_goods_line_schema(),
        "Rate": build_rate_schema(),
        "TrackHistoryEntry": build_track_history_entry_schema(),
        "CustomerContact": build_customer_contact_schema(),
        "Customer": build_customer_schema(),
        "CarrierContact": build_carrier_contact_schema(),
        "Carrier": build_carrier_schema(),
        "OrderAttributes": build_order_attributes_schema(),
        "Order": build_order_schema(),
        "PaginationMetaLink": build_pagination_meta_link_schema(),
        "PaginationLinks": build_pagination_links_schema(),
        "PaginationMeta": build_pagination_meta_schema(),
        "OrderListResponse": list_response_schema("#/components/schemas/Order"),
        "OrderSingleResponse": single_response_schema("#/components/schemas/Order"),
        "Product": build_product_schema(),
        "ProductListResponse": list_response_schema("#/components/schemas/Product"),
        "ProductSingleResponse": single_response_schema("#/components/schemas/Product"),
        "Substatus": build_substatus_schema(),
        "SubstatusListResponse": list_response_schema("#/components/schemas/Substatus"),
        "SubstatusSingleResponse": single_response_schema("#/components/schemas/Substatus"),
        "PackageType": build_package_type_schema(),
        "PackageTypeListResponse": list_response_schema("#/components/schemas/PackageType"),
        "PackageTypeSingleResponse": single_response_schema("#/components/schemas/PackageType"),
        "VehicleType": build_vehicle_type_schema(),
        "VehicleTypeListResponse": list_response_schema("#/components/schemas/VehicleType"),
        "VehicleTypeSingleResponse": single_response_schema("#/components/schemas/VehicleType"),
        "Invoice": build_invoice_schema(),
        "InvoiceListResponse": list_response_schema("#/components/schemas/Invoice"),
        "InvoiceSingleResponse": single_response_schema("#/components/schemas/Invoice"),
        "CustomerListResponse": list_response_schema("#/components/schemas/Customer"),
        "CustomerSingleResponse": single_response_schema("#/components/schemas/Customer"),
        "CarrierListResponse": list_response_schema("#/components/schemas/Carrier"),
        "CarrierSingleResponse": single_response_schema("#/components/schemas/Carrier"),
        "FleetVehicle": build_fleet_vehicle_schema(),
        "FleetListResponse": list_response_schema("#/components/schemas/FleetVehicle"),
        "FleetSingleResponse": single_response_schema("#/components/schemas/FleetVehicle"),
        "ErrorResponse": build_error_response_schema(),
        "ValidationErrorResponse": build_validation_error_schema(),
    }


# ---------------------------------------------------------------------------
# Standard error responses
# ---------------------------------------------------------------------------

STANDARD_ERROR_RESPONSES = {
    "401": {
        "description": "Unauthenticated. Missing or invalid Authorization header.",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {"message": "Unauthenticated."},
            }
        },
    },
    "404": {
        "description": "Not found.",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {"message": "Not found."},
            }
        },
    },
    "422": {
        "description": "Validation error.",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ValidationErrorResponse"},
            }
        },
    },
    "429": {
        "description": "Too Many Requests — maximum of 60 requests per minute exceeded.",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {"message": "Too Many Attempts."},
            }
        },
    },
}


# ---------------------------------------------------------------------------
# Map endpoint paths/methods to known response schema refs
# ---------------------------------------------------------------------------

RESPONSE_SCHEMA_MAP = {
    ("GET",  "/v1/orders"):                    "OrderListResponse",
    ("GET",  "/v1/orders/{orderNo}"):           "OrderSingleResponse",
    ("PUT",  "/v1/orders/{orderNo}"):           "OrderSingleResponse",
    ("GET",  "/v1/products"):                   "ProductListResponse",
    ("GET",  "/v1/products/{productNo}"):       "ProductSingleResponse",
    ("GET",  "/v1/substatuses"):                "SubstatusListResponse",
    ("GET",  "/v1/substatuses/{substatusNo}"):  "SubstatusSingleResponse",
    ("GET",  "/v1/packagetypes"):               "PackageTypeListResponse",
    ("GET",  "/v1/packagetypes/{packageTypeNo}"): "PackageTypeSingleResponse",
    ("GET",  "/v1/vehicletypes"):               "VehicleTypeListResponse",
    ("GET",  "/v1/vehicletypes/{vehicleTypeNo}"): "VehicleTypeSingleResponse",
    ("GET",  "/v1/invoices"):                   "InvoiceListResponse",
    ("GET",  "/v1/invoices/{invoiceId}"):        "InvoiceSingleResponse",
    ("GET",  "/v1/customers"):                  "CustomerListResponse",
    ("GET",  "/v1/customers/{customerNo}"):     "CustomerSingleResponse",
    ("GET",  "/v1/carriers"):                   "CarrierListResponse",
    ("GET",  "/v1/carriers/{carrierNo}"):       "CarrierSingleResponse",
    ("GET",  "/v1/fleet"):                      "FleetListResponse",
    ("GET",  "/v1/fleet/{fleetNo}"):            "FleetSingleResponse",
    ("GET",  "/v1/carrier/orders"):             "OrderListResponse",
    ("GET",  "/v1/carrier/orders/{orderNo}"):    "OrderSingleResponse",
    ("PUT",  "/v1/carrier/orders/{orderNo}"):    "OrderSingleResponse",
}


# ---------------------------------------------------------------------------
# Tag name cleanup
# ---------------------------------------------------------------------------

def clean_tag(tag: str) -> str:
    # Strip the parenthetical account type qualifier for clean tag names.
    # e.g. "Orders (Customer or branch account)" -> "Orders"
    #      "Orders for carrier (Carrier account)" -> "Orders for carrier"
    cleaned = re.sub(r"\s*\(.*", "", tag).strip()
    return cleaned if cleaned else tag.strip()


# ---------------------------------------------------------------------------
# Operation ID generation
# ---------------------------------------------------------------------------

def make_operation_id(method: str, path: str) -> str:
    # e.g. GET /v1/orders/{orderNo} -> getOrderByOrderNo
    method_map = {"GET": "get", "PUT": "update", "POST": "create", "DELETE": "delete", "PATCH": "patch"}
    verb = method_map.get(method, method.lower())
    parts = path.replace("/v1/", "").replace("{", "").replace("}", "").split("/")
    name = "".join(p.capitalize() for p in parts if p)
    return f"{verb}{name}"


# ---------------------------------------------------------------------------
# Parameter type mapping
# ---------------------------------------------------------------------------

TYPE_MAP = {
    "integer": {"type": "integer"},
    "string": {"type": "string"},
    "boolean": {"type": "boolean"},
    "number": {"type": "number"},
    "object": {"type": "object"},
    "array": {"type": "array", "items": {}},
}


def param_schema(type_str: str, example=None) -> dict:
    s = dict(TYPE_MAP.get(type_str, {"type": "string"}))
    if example is not None and example != "":
        if s.get("type") == "integer":
            try:
                s["example"] = int(example)
            except (ValueError, TypeError):
                s["example"] = example
        elif s.get("type") == "boolean":
            s["example"] = example in ("true", "1", True)
        else:
            s["example"] = example
    return s


# ---------------------------------------------------------------------------
# Build a single endpoint operation
# ---------------------------------------------------------------------------

def build_operation(ep: dict) -> dict:
    method = ep["method"]
    path = ep["path"]
    tag = clean_tag(ep["tag"])

    op = {
        "operationId": make_operation_id(method, path),
        "summary": ep["summary"],
        "description": ep.get("description", ""),
        "tags": [tag],
        "security": [{"basicAuth": []}] if ep.get("auth_required") else [],
        "parameters": [],
        "responses": {},
    }

    # URL path parameters
    for p in ep.get("url_parameters", []):
        if not p["name"]:
            continue
        param = {
            "name": p["name"],
            "in": "path",
            "required": True,
            "description": p.get("description", ""),
            "schema": param_schema(p.get("type", "string"), p.get("example")),
        }
        op["parameters"].append(param)

    # Query parameters
    for p in ep.get("query_parameters", []):
        if not p["name"]:
            continue
        # Skip the generic aggregate "filter" parameter — it's documented via filter.xxx children
        if p["name"] == "filter":
            continue
        # Convert filter.xxx notation → filter[xxx] query param style
        name = p["name"].replace(".", "[") + ("" if "." not in p["name"] else "]")
        param = {
            "name": name,
            "in": "query",
            "required": p.get("required", False),
            "description": p.get("description", ""),
            "schema": param_schema(p.get("type", "string"), p.get("example")),
        }
        op["parameters"].append(param)

    # Body parameters (for PUT requests)
    if ep.get("body_parameters"):
        body_props = {}
        for p in ep["body_parameters"]:
            if not p["name"]:
                continue
            prop = param_schema(p.get("type", "string"), p.get("example"))
            if p.get("description"):
                prop["description"] = p["description"]
            body_props[p["name"]] = prop

        op["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": body_props,
                    }
                }
            },
        }

    # Responses
    schema_ref = RESPONSE_SCHEMA_MAP.get((method, path))
    success_response = {
        "description": "Successful response.",
        "content": {
            "application/json": {
                "schema": (
                    {"$ref": f"#/components/schemas/{schema_ref}"}
                    if schema_ref
                    else {"type": "object"}
                ),
            }
        },
    }

    # Attach the response example from intermediate if present
    if ep.get("response_examples"):
        ex = ep["response_examples"][0]
        success_response["content"]["application/json"]["example"] = ex["body"]

    op["responses"]["200"] = success_response

    # Add standard error responses
    op["responses"].update(STANDARD_ERROR_RESPONSES)

    # PUT endpoints additionally get 422
    if method != "PUT":
        op["responses"].pop("422", None)

    return op


# ---------------------------------------------------------------------------
# Build the full OpenAPI spec document
# ---------------------------------------------------------------------------

def build_openapi(data: dict) -> dict:
    info = data["info"]

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": info["title"],
            "description": (
                "REST API to communicate with the EasyTrans Transport Management System.\n\n"
                "## Account types\n\n"
                "This API supports three account types:\n"
                "- **Branch accounts**: EasyTrans users (carriers/logistics operators)\n"
                "- **Customer accounts**: Customers of EasyTrans users (web shops, ERP systems)\n"
                "- **Carrier accounts**: Third-party carriers that execute transport orders\n\n"
                "Some endpoints and fields are restricted to specific account types, "
                "as noted in the individual endpoint descriptions.\n\n"
                "## Rate limiting\n\n"
                "A maximum of 60 requests per minute is allowed. "
                "A `429 Too Many Requests` response will be returned if this limit is exceeded.\n\n"
                "## Pagination\n\n"
                "List endpoints return at most 100 records per page. "
                "Use the `links.next` URL to retrieve subsequent pages.\n\n"
                "## Filtering and sorting\n\n"
                "Use `filter[field]=value` query parameters on list endpoints. "
                "Operators like `[gte]`, `[gt]`, `[lte]`, `[lt]`, `[neq]` can be appended to field names. "
                "Multiple values can be separated by commas.\n\n"
                "## Base URL\n\n"
                "Every EasyTrans account has its own server URL. "
                "The API base URL follows the pattern: `https://www.YOUR_SERVER/YOUR_ENVIRONMENT/api/v1/`"
            ),
            "version": "1.0.0",
            "contact": {
                "name": "EasyTrans Software",
                "url": "https://www.easytrans.nl",
                "email": "info@easytrans.nl",
            },
        },
        "servers": [
            {
                "url": info["base_url"] + "/v1",
                "description": "Demo / documentation server",
            },
            {
                "url": "https://www.YOUR_SERVER/YOUR_ENVIRONMENT/api/v1",
                "description": "Your EasyTrans instance",
            },
        ],
        "security": [{"basicAuth": []}],
        "components": {
            "securitySchemes": {
                "basicAuth": {
                    "type": "http",
                    "scheme": "basic",
                    "description": (
                        "HTTP Basic authentication. "
                        "Encode `username:password` in Base64 and pass as "
                        "`Authorization: Basic {encoded}` header. "
                        "Contact your carrier to receive login credentials."
                    ),
                }
            },
            "schemas": build_components_schemas(),
        },
        "paths": {},
        "tags": [],
    }

    # Collect unique (ordered) tags
    seen_tags = []
    for ep in data["endpoints"]:
        t = clean_tag(ep["tag"])
        if t not in seen_tags:
            seen_tags.append(t)

    spec["tags"] = [{"name": t} for t in seen_tags]

    # Build paths
    for ep in data["endpoints"]:
        path = ep["path"]
        method = ep["method"].lower()
        if path not in spec["paths"]:
            spec["paths"][path] = {}
        spec["paths"][path][method] = build_operation(ep)

    return spec


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not INTERMEDIATE_FILE.exists():
        print(f"ERROR: {INTERMEDIATE_FILE} not found. Run html_to_intermediate.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {INTERMEDIATE_FILE} …")
    with open(INTERMEDIATE_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    print("Building OpenAPI spec …")
    spec = build_openapi(data)

    paths_count = len(spec["paths"])
    ops_count = sum(len(v) for v in spec["paths"].values())
    schemas_count = len(spec["components"]["schemas"])
    print(f"  {paths_count} paths, {ops_count} operations, {schemas_count} component schemas")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(dump_yaml(spec))

    print(f"OpenAPI spec written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
