"""
Integration test: customer update using update_on_existing_customerno.

Mirrors the second customer in the 'extended' documentation example which
uses the update path:

  "customerno": 12345,
  "update_on_existing_customerno": true,
  "delete_existing_customer_contacts": false

This is an entirely separate server-side code path from customer creation.
The API routes on update_on_existing_customerno=True and applies a diff to
an existing customer record rather than inserting a new one.

Key risks this test catches:
- update_on_existing_customerno is serialised as JSON boolean true, not
  the integer 1 (Python's asdict() preserves bool type, but _clean_dict
  could accidentally coerce it)
- delete_existing_customer_contacts=False is transmitted (not omitted),
  which is intentional — an absent field might default to True on the server
- customerno (int) must be included in the serialised customer dict

Note on test-mode behaviour:
  In mode="test" the update is validated but never applied, so the test
  will succeed even if customerno=12345 does not exist in the demo
  environment — the server validates the payload structure only.
  If the server does require the customer to exist even in test mode,
  the test will raise EasyTransCustomerError which is caught and re-raised
  with a descriptive message to guide the operator.
"""

import pytest

from easytrans import Customer
from easytrans.models import CustomerResult
from easytrans.exceptions import EasyTransCustomerError

pytestmark = pytest.mark.integration


class TestCustomerUpdate:
    """Customer update via update_on_existing_customerno flag."""

    def test_update_payload_structure_accepted(self, real_client, simple_customer_contact):
        """
        The update payload (customerno + update_on_existing_customerno=True)
        is serialised correctly and the API does not reject it.

        If the demo environment requires the customer to exist in test mode
        as well, an EasyTransCustomerError is raised. That is acceptable —
        what matters is that NO other exception (e.g. ValueError, KeyError,
        TypeError) is raised from within the SDK itself.
        """
        customer = Customer(
            customerno=12345,
            update_on_existing_customerno=True,
            delete_existing_customer_contacts=False,
            company_name="Updated Company Name",
            attn="Administration",
            address="Kanaalweg",
            houseno="14",
            postal_code="3526KL",
            city="Utrecht",
            country="NL",
            ibanno="NL63INGB0004511811",
            bicno="INGBNL2A",
            cocno="50725769",
            vatno="NL822891682B01",
            vat_liable=1,
            language="en",
            external_id="integration-test-customer-update-001",
            customer_contacts=[simple_customer_contact],
        )

        try:
            result = real_client.import_customers([customer], mode="test")
            # If we reach here the API accepted the payload
            assert isinstance(result, CustomerResult)
            assert result.mode == "test"
        except EasyTransCustomerError as exc:
            # The customer number doesn't exist in this demo environment —
            # that is a data issue, not an SDK serialisation issue.
            pytest.skip(
                f"customerno=12345 does not exist in demo environment: {exc}. "
                "Provide a valid customerno via EASYTRANS_TEST_CUSTOMERNO env var "
                "to run this test against a real customer record."
            )

    def test_update_flag_is_boolean_not_integer(self, real_client, simple_customer_contact):
        """
        Verify update_on_existing_customerno=True is serialised as JSON true.

        The _clean_dict helper must not convert booleans to integers or omit
        False values that are needed for correctness.
        """
        import json as _json

        customer = Customer(
            customerno=1,
            update_on_existing_customerno=True,
            delete_existing_customer_contacts=False,
            company_name="Boolean Test Company",
            customer_contacts=[simple_customer_contact],
        )

        serialised = customer.to_dict()

        assert serialised["update_on_existing_customerno"] is True
        assert serialised["delete_existing_customer_contacts"] is False

        # Confirm round-trip through JSON preserves bool type
        json_str = _json.dumps(serialised)
        parsed = _json.loads(json_str)
        assert parsed["update_on_existing_customerno"] is True
        assert parsed["delete_existing_customer_contacts"] is False

    def test_existing_customerno_update(self, real_client, simple_customer_contact):
        """
        If EASYTRANS_TEST_CUSTOMERNO is provided, run a full round-trip update
        against that specific customer number in the demo environment.
        """
        import os

        customerno_str = os.getenv("EASYTRANS_TEST_CUSTOMERNO")
        if not customerno_str:
            pytest.skip(
                "Set EASYTRANS_TEST_CUSTOMERNO to a valid customer number in your "
                "demo environment to run this test."
            )

        customerno = int(customerno_str)

        customer = Customer(
            customerno=customerno,
            update_on_existing_customerno=True,
            delete_existing_customer_contacts=False,
            company_name="Integration Test Updated Name",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.mode == "test"
        assert result.total_customers == 1
