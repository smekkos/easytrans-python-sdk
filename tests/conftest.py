"""
Pytest configuration and fixtures for EasyTrans SDK tests.

Provides reusable fixtures for client instances, sample data,
and mock API responses.
"""

import json
import pytest
from typing import Dict, Any

from easytrans import EasyTransClient, Order, Destination, Package, Customer, CustomerContact
from easytrans.constants import CollectDeliver, Salutation


@pytest.fixture
def client():
    """
    Create a test EasyTransClient instance.
    
    Uses test credentials pointing to a demo environment.
    """
    return EasyTransClient(
        server_url="mytrans.nl",
        environment_name="demo",
        username="test_user",
        password="test_pass",
        default_mode="test",
    )


@pytest.fixture
def sample_destinations():
    """Create sample pickup and delivery destinations."""
    return [
        Destination(
            destinationno=1,
            collect_deliver=CollectDeliver.PICKUP.value,
            company_name="Sender Company A",
            contact="Mr. Johnson",
            address="Keizersgracht",
            houseno="1",
            addition="a",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            telephone="020-1234567",
            destination_remark="Call before arrival",
        ),
        Destination(
            destinationno=2,
            collect_deliver=CollectDeliver.DELIVERY.value,
            company_name="Receiver Company B",
            contact="Mr. Pietersen",
            address="Kanaalweg",
            houseno="14",
            postal_code="3526KL",
            city="Utrecht",
            country="NL",
            telephone="030-7654321",
            destination_remark="Delivery at neighbours if not at home",
            customer_reference="ABCD1234",
        ),
    ]


@pytest.fixture
def sample_packages():
    """Create sample package/goods data."""
    return [
        Package(
            amount=2.0,
            weight=150.0,
            length=120.0,
            width=80.0,
            height=50.0,
            description="Euro pallet",
        )
    ]


@pytest.fixture
def sample_order(sample_destinations, sample_packages):
    """
    Create a complete sample order for testing.
    
    Includes destinations and packages.
    """
    return Order(
        productno=2,
        date="2026-02-18",
        time="14:45",
        status="submit",
        customerno=3,
        remark="Test order - 1 Euro pallet",
        remark_invoice="P/O Number: TEST1234",
        email_receiver="test@example.com",
        external_id="test-order-12345",
        order_destinations=sample_destinations,
        order_packages=sample_packages,
    )


@pytest.fixture
def sample_customer_contacts():
    """Create sample customer contacts."""
    return [
        CustomerContact(
            salutation=Salutation.MR.value,
            contact_name="Bram Pietersen",
            telephone="020-7654321",
            mobile="06-12345678",
            email="bram@example.com",
            use_email_for_invoice=True,
            use_email_for_reminder=True,
            contact_remark="Warehouse manager",
            username="bram_user",
            password="SecureP@ss123",
        )
    ]


@pytest.fixture
def sample_customer(sample_customer_contacts):
    """Create a complete sample customer for testing."""
    return Customer(
        company_name="Example Company A",
        attn="Administration",
        address="Keizersgracht",
        houseno="1a",
        address2="2nd floor",
        postal_code="1015CC",
        city="Amsterdam",
        country="NL",
        website="www.example.com",
        remark="Test customer",
        ibanno="NL63INGB0004511811",
        bicno="INGBNL2A",
        cocno="50725769",
        vatno="NL822891682B01",
        vat_liable=1,
        language="en",
        external_id="test-customer-12345",
        customer_contacts=sample_customer_contacts,
    )


@pytest.fixture
def success_order_response() -> Dict[str, Any]:
    """Mock successful order import response."""
    return {
        "result": {
            "mode": "effect",
            "total_orders": 1,
            "total_order_destinations": 2,
            "total_order_packages": 1,
            "result_description": "Import completed successfully. 1 orders have been added",
            "new_ordernos": [29145],
            "order_tracktrace": {
                "29145": {
                    "local_trackingnr": "AEZS2MRZGE2DK",
                    "local_tracktrace_url": "https://www.mytrans.nl/demo/tracktrace.php?trackingnr=AEZS2MRZGE2DK",
                    "global_trackingnr": "AE4TSOJPGEZS2MRZGE2DK",
                    "global_tracktrace_url": "https://www.mytrans.nl/tracktrace?trackingnr=AE4TSOJPGEZS2MRZGE2DK",
                    "status": "accepted",
                }
            },
        }
    }


@pytest.fixture
def success_order_response_with_rates() -> Dict[str, Any]:
    """Mock successful order response with rate calculation."""
    return {
        "result": {
            "mode": "effect",
            "total_orders": 1,
            "total_order_destinations": 2,
            "total_order_packages": 1,
            "result_description": "Import completed successfully. 1 orders have been added",
            "new_ordernos": [29145],
            "order_tracktrace": {
                "29145": {
                    "local_trackingnr": "AEZS2MRZGE2DK",
                    "local_tracktrace_url": "https://www.mytrans.nl/demo/tracktrace.php?trackingnr=AEZS2MRZGE2DK",
                    "global_trackingnr": "AE4TSOJPGEZS2MRZGE2DK",
                    "global_tracktrace_url": "https://www.mytrans.nl/tracktrace?trackingnr=AE4TSOJPGEZS2MRZGE2DK",
                    "status": "accepted",
                }
            },
            "order_rates": {
                "29145": {
                    "rates": [
                        {"description": "Small Van", "price": 153.0},
                        {"description": "Fuel surcharge", "price": 5.74},
                    ],
                    "order_total_excluding_vat": 158.74,
                    "order_total_including_vat": 192.08,
                }
            },
        }
    }


@pytest.fixture
def success_customer_response() -> Dict[str, Any]:
    """Mock successful customer import response."""
    return {
        "result": {
            "mode": "effect",
            "total_customers": 1,
            "total_customer_contacts": 1,
            "result_description": "Import completed successfully. 1 customers have been added",
            "new_customernos": [12345],
            "new_userids": {"12345": [201]},
        }
    }


@pytest.fixture
def error_auth_response() -> Dict[str, Any]:
    """Mock authentication error response (errorno 12)."""
    return {"error": {"errorno": 12, "error_description": "Login attempt failed. Invalid username or password"}}


@pytest.fixture
def error_order_response() -> Dict[str, Any]:
    """Mock order validation error response (errorno 21)."""
    return {"error": {"errorno": 21, "error_description": "No productno given (required field)."}}


@pytest.fixture
def error_destination_response() -> Dict[str, Any]:
    """Mock destination validation error response (errorno 30)."""
    return {"error": {"errorno": 30, "error_description": "A minimum of two destinations is required."}}


@pytest.fixture
def error_customer_response() -> Dict[str, Any]:
    """Mock customer validation error response (errorno 50)."""
    return {"error": {"errorno": 50, "error_description": "No company_name given (required field)."}}


@pytest.fixture
def webhook_payload_finished() -> Dict[str, Any]:
    """Mock webhook payload for finished order."""
    return {
        "companyId": 2000,
        "eventTime": "2026-02-18T14:56:09+01:00",
        "order": {
            "orderNo": 1234,
            "customerNo": 8,
            "status": "finished",
            "subStatusId": 12,
            "subStatusName": "Delivered at the neighbours",
            "destinations": [
                {
                    "addressId": 28626,
                    "stopNo": 1,
                    "customerReference": "",
                    "waybillNo": "",
                    "notes": "Notes with the pickup destination",
                    "taskType": "pickup",
                    "taskResult": {
                        "date": "2026-02-17",
                        "arrivalTime": "10:00",
                        "departureTime": "10:15",
                        "signedBy": "Mr. Johnson",
                        "base64EncodedSignature": "",
                        "latitude": None,
                        "longitude": None,
                    },
                },
                {
                    "addressId": 28627,
                    "stopNo": 2,
                    "customerReference": "ABCD1234",
                    "waybillNo": "NL1234567",
                    "notes": "Notes with the delivery destination",
                    "taskType": "delivery",
                    "taskResult": {
                        "date": "2026-02-18",
                        "arrivalTime": "16:00",
                        "departureTime": "16:15",
                        "signedBy": "Mike",
                        "base64EncodedSignature": "",
                        "latitude": "52.1234567",
                        "longitude": "5.1234567",
                    },
                },
            ],
            "externalId": "test-order-12345",
        },
    }


@pytest.fixture
def webhook_payload_collected() -> Dict[str, Any]:
    """Mock webhook payload for collected order."""
    return {
        "companyId": 2000,
        "eventTime": "2026-02-17T10:30:00+01:00",
        "order": {
            "orderNo": 1234,
            "customerNo": 8,
            "status": "collected",
            "subStatusId": None,
            "subStatusName": None,
            "destinations": [
                {
                    "addressId": 28626,
                    "stopNo": 1,
                    "customerReference": "",
                    "waybillNo": "",
                    "notes": "",
                    "taskType": "pickup",
                    "taskResult": {
                        "date": "2026-02-17",
                        "arrivalTime": "10:00",
                        "departureTime": "10:15",
                        "signedBy": "Mr. Johnson",
                        "base64EncodedSignature": "",
                        "latitude": "52.3702157",
                        "longitude": "4.8951679",
                    },
                }
            ],
            "externalId": "test-order-12345",
        },
    }
