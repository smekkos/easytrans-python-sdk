"""
Pytest configuration and fixtures for EasyTrans integration tests.

Uses real environment variables to construct a live EasyTransClient.
The entire integration suite is skipped automatically when
EASYTRANS_USERNAME is not set in the environment, so CI pipelines that
don't have credentials configured are unaffected.

All integration tests operate with default_mode="test" so the EasyTrans
API validates every payload without creating real orders or customers.

REST API tests additionally require known entity IDs (order numbers, customer
numbers, etc.) because the REST API only reads existing data — it never
creates test records.  Set the EASYTRANS_REST_KNOWN_* variables to enable
those tests; individual tests are skipped with an informative message when
their required ID is absent.
"""

import os
import pytest

from easytrans import EasyTransClient, Order, Destination, Package, Customer, CustomerContact
from easytrans.constants import CollectDeliver, Salutation

# ---------------------------------------------------------------------------
# Skip the entire integration suite unless credentials are present
# ---------------------------------------------------------------------------

_CREDENTIALS_PRESENT = bool(os.getenv("EASYTRANS_USERNAME"))

_SKIP_REASON = (
    "Integration credentials not configured. "
    "Set EASYTRANS_SERVER, EASYTRANS_ENV, EASYTRANS_USERNAME and "
    "EASYTRANS_PASSWORD to run integration tests."
)


def pytest_collection_modifyitems(items):
    """Skip all integration tests when credentials are absent."""
    if not _CREDENTIALS_PRESENT:
        skip_marker = pytest.mark.skip(reason=_SKIP_REASON)
        for item in items:
            if "integration" in str(item.fspath):
                item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Client and environment fixtures (session-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def productno():
    """
    Product number that is valid in the connected EasyTrans environment.

    EasyTrans product numbers are carrier-specific and differ per environment,
    so there is no universal default. Set EASYTRANS_TEST_PRODUCTNO before
    running order import integration tests.

    Example:
        export EASYTRANS_TEST_PRODUCTNO=21
    """
    pno = os.getenv("EASYTRANS_TEST_PRODUCTNO")
    if not pno:
        pytest.skip(
            "Set EASYTRANS_TEST_PRODUCTNO to a valid product number in your "
            "EasyTrans environment to run order import tests. "
            "You can find valid product numbers in the EasyTrans Customer Portal."
        )
    return int(pno)


@pytest.fixture(scope="session")
def customerno():
    """
    Customer number to attach to every order.

    Required when the API account is a *branch* account (errorno 23 if absent).
    Not needed for direct-customer accounts — leave unset and the field is
    omitted from the payload automatically via _clean_dict().

    Example:
        export EASYTRANS_TEST_CUSTOMERNO=3
    """
    cno = os.getenv("EASYTRANS_TEST_CUSTOMERNO")
    return int(cno) if cno else None


@pytest.fixture(scope="session")
def real_client():
    """
    Return an EasyTransClient connected to the real EasyTrans demo API.

    The client defaults to mode="test" so no real orders or customers
    are ever created during the integration test run.
    """
    client = EasyTransClient(
        server_url=os.environ.get("EASYTRANS_SERVER", "mytrans.nl"),
        environment_name=os.environ.get("EASYTRANS_ENV", "demo"),
        username=os.environ["EASYTRANS_USERNAME"],
        password=os.environ["EASYTRANS_PASSWORD"],
        default_mode="test",
        timeout=30,
    )
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Shared destination fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_destinations():
    """
    Minimal destination pair — only the fields present in the
    'minimal' example from the official documentation.

    Notably absent: country, collect_deliver, telephone, contact.
    """
    return [
        Destination(
            company_name="Example Company A",
            address="Keizersgracht",
            houseno="1a",
            postal_code="1015CC",
            city="Amsterdam",
        ),
        Destination(
            company_name="Example Company B",
            address="Kanaalweg",
            houseno="14",
            postal_code="3526KL",
            city="Utrecht",
        ),
    ]


@pytest.fixture
def simple_destinations():
    """Full destination pair with explicit collect_deliver values."""
    return [
        Destination(
            collect_deliver=CollectDeliver.PICKUP.value,
            company_name="Example Company A",
            contact="Mr. Johnson",
            address="Keizersgracht",
            houseno="1",
            addition="a",
            address2="2nd floor",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            telephone="020-1234567",
            destination_remark="Call before arrival",
        ),
        Destination(
            collect_deliver=CollectDeliver.DELIVERY.value,
            company_name="Example Company B",
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
def extended_destinations():
    """
    Three-stop destination list from the 'extended' documentation example.

    Destination 2 uses collect_deliver=2 (BOTH), which exercises the third
    enum value not covered by the unit test fixtures.
    """
    return [
        Destination(
            destinationno=1,
            collect_deliver=CollectDeliver.PICKUP.value,
            company_name="Example Company A",
            contact="Mr. Johnson",
            address="Keizersgracht",
            houseno="1",
            addition="a",
            address2="2nd floor",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            telephone="020-1234567",
            destination_remark="Call before arrival",
            delivery_date="2026-06-01",
            delivery_time="12:00",
            delivery_time_from="09:00",
        ),
        Destination(
            destinationno=2,
            collect_deliver=CollectDeliver.BOTH.value,   # 2 = pickup AND delivery
            company_name="Example Company B",
            contact="Mr. Pietersen",
            address="Kanaalweg",
            houseno="14",
            postal_code="3526KL",
            city="Utrecht",
            country="NL",
            telephone="030-7654321",
            destination_remark="Delivery at neighbours if not at home",
            customer_reference="ABC1234",
            delivery_date="2026-06-01",
            delivery_time="15:00",
            delivery_time_from="12:00",
        ),
        Destination(
            destinationno=3,
            collect_deliver=CollectDeliver.DELIVERY.value,
            company_name="Example Company C",
            contact="Mr. Klaassen",
            address="Steenstraat",
            houseno="17",
            postal_code="6828CA",
            city="Arnhem",
            country="NL",
            telephone="026-3456789",
            customer_reference="DEF5678",
            delivery_date="2026-06-02",
            delivery_time="17:00",
            delivery_time_from="15:00",
        ),
    ]


# ---------------------------------------------------------------------------
# Shared package fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def standard_packages():
    """Single package line with full dimensions (used by most tests)."""
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
def routed_packages():
    """
    Package lines with explicit collect_destinationno/deliver_destinationno
    routing (from the 'extended' documentation example).
    """
    return [
        Package(
            collect_destinationno=1,
            deliver_destinationno=2,
            ratetypeno=0,   # 0 = standard "Packages" rate type (universally valid)
            amount=2.0,
            weight=150.0,
            length=120.0,
            width=80.0,
            height=50.0,
            description="Euro pallet",
        ),
        Package(
            collect_destinationno=1,
            deliver_destinationno=3,
            amount=1.0,
            weight=10.0,
            length=40.0,
            width=30.0,
            height=20.0,
            description="Box with brochures",
        ),
    ]


# ---------------------------------------------------------------------------
# Shared customer fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_customer_contact():
    """Single contact without portal access credentials."""
    return CustomerContact(
        salutation=Salutation.MR.value,
        contact_name="Bram Pietersen",
        telephone="020-7654321",
        mobile="06-12345678",
        email="bram@example.com",
        use_email_for_invoice=True,
        use_email_for_reminder=True,
        contact_remark="Warehouse manager",
    )


@pytest.fixture
def portal_contacts():
    """Two contacts with portal access credentials (from extended example)."""
    return [
        CustomerContact(
            salutation=Salutation.MR.value,
            contact_name="Bram Pietersen",
            telephone="020-7654321",
            mobile="06-12345678",
            email="bram@example.com",
            use_email_for_invoice=False,
            contact_remark="Warehouse manager",
            username="bram_integration_test",
            password="v5xhCmRs",
        ),
        CustomerContact(
            salutation=Salutation.MRS_MS.value,
            contact_name="Kim Verbeek",
            telephone="020-7654321",
            mobile="06-12345678",
            email="kim@example.com",
            use_email_for_invoice=True,
            contact_remark="Front desk",
            username="kim_integration_test",
            password="eLn3y23D",
        ),
    ]


# ---------------------------------------------------------------------------
# REST API fixtures — shared client + known-entity ID fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def rest_client():
    """
    Return an EasyTransClient for REST API integration tests.

    Reuses the same credentials as the JSON import tests. The client is
    session-scoped so the same TCP connection pool is reused across all
    REST tests.
    """
    client = EasyTransClient(
        server_url=os.environ.get("EASYTRANS_SERVER", "mytrans.nl"),
        environment_name=os.environ.get("EASYTRANS_ENV", "demo"),
        username=os.environ["EASYTRANS_USERNAME"],
        password=os.environ["EASYTRANS_PASSWORD"],
        timeout=30,
    )
    yield client
    client.close()


def _rest_entity_fixture(env_var: str, label: str, cast=int):
    """
    Factory for REST known-entity fixtures.

    If the env-var is unset, the fixture skips the test with a clear
    message rather than failing with a confusing KeyError.
    """
    @pytest.fixture(scope="session")
    def _fixture():
        raw = os.getenv(env_var)
        if not raw:
            pytest.skip(
                f"Set {env_var} to a valid {label} in your EasyTrans "
                f"environment to run this REST integration test."
            )
        return cast(raw)

    _fixture.__name__ = env_var.lower()
    return _fixture


# Known entity IDs — each is optional; its tests are skipped when absent.
rest_known_order_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_ORDER_NO", "order number"
)
rest_known_product_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_PRODUCT_NO", "product number"
)
rest_known_substatus_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_SUBSTATUS_NO", "substatus number"
)
rest_known_package_type_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_PACKAGE_TYPE_NO", "package type number"
)
rest_known_vehicle_type_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_VEHICLE_TYPE_NO", "vehicle type number"
)
rest_known_customer_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_CUSTOMER_NO", "customer number"
)
rest_known_carrier_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_CARRIER_NO", "carrier number"
)
rest_known_fleet_no = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_FLEET_NO", "fleet number"
)
rest_known_invoice_id = _rest_entity_fixture(
    "EASYTRANS_REST_KNOWN_INVOICE_ID", "invoice ID"
)


# ---------------------------------------------------------------------------
# Rate-limit guard
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _rate_limit_guard():
    """
    Pause briefly before every integration test to avoid hitting the
    EasyTrans rate limit of 60 requests per minute.

    At 1.1 s per test the full REST suite (~65 tests) takes ~70 s — still
    well within a CI timeout — while ensuring we never exceed 54 req/min.
    """
    import time
    time.sleep(1.1)
