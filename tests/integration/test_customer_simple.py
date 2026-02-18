"""
Integration test: simple customer import.

Mirrors the 'simple' example from the official documentation:
  EasyTrans - JSON customer import example - simple.json

Exercises the most common customer creation fields:
- Full address block
- Optional postal/mailing address (mail_address, mail_houseno, etc.)
- Banking details: ibanno, bicno
- Registration numbers: cocno, vatno
- vat_liable flag
- One contact without portal access credentials

Key risks this test catches:
- CustomerResult.new_customernos == [] in test mode (not an error)
- CustomerResult.new_userids == {} when no portal accounts created
- Banking and registration number fields are accepted as-is (no format
  validation on the SDK side — server must accept raw strings)
- The customer_import auth type is correctly sent
  (not order_import, which is a different code path)
"""

import pytest
from easytrans import Customer
from easytrans.models import CustomerResult

pytestmark = pytest.mark.integration


class TestSimpleCustomerImport:
    """Single customer with one contact, no portal access."""

    def test_simple_customer_accepted(self, real_client, simple_customer_contact):
        """A complete simple customer payload is accepted by the API."""
        customer = Customer(
            company_name="Example Company A",
            attn="Administration",
            address="Keizersgracht",
            houseno="1a",
            address2="2nd floor",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            mail_address="Postbus",
            mail_houseno="73",
            mail_postal_code="1010AA",
            mail_city="Amsterdam",
            mail_country="NL",
            website="www.example.com",
            remark="Integration test customer",
            ibanno="NL63INGB0004511811",
            bicno="INGBNL2A",
            cocno="50725769",
            vatno="NL822891682B01",
            vat_liable=1,
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert isinstance(result, CustomerResult)
        assert result.mode == "test"
        assert result.total_customers == 1
        assert result.total_customer_contacts == 1

    def test_simple_customer_test_mode_creates_nothing(
        self, real_client, simple_customer_contact
    ):
        """Test mode must return empty new_customernos and empty new_userids."""
        customer = Customer(
            company_name="Example Company A",
            postal_code="1015CC",
            city="Amsterdam",
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.new_customernos == []
        assert result.new_userids == {}

    def test_minimal_customer_only_company_name_required(self, real_client, simple_customer_contact):
        """
        The only truly required Customer field is company_name.
        All address, banking, and registration fields are optional.
        """
        customer = Customer(
            company_name="Minimal Test Company",
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1

    def test_customer_result_description_present(self, real_client, simple_customer_contact):
        """The API always returns a non-empty result_description for customers."""
        customer = Customer(
            company_name="Example Company A",
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.result_description
        assert isinstance(result.result_description, str)
        assert len(result.result_description) > 0

    def test_customer_with_external_id_accepted(self, real_client, simple_customer_contact):
        """external_id is accepted and does not cause a validation error."""
        customer = Customer(
            company_name="Example Company A",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            external_id="integration-test-customer-001",
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1

    def test_customer_with_banking_details_accepted(self, real_client, simple_customer_contact):
        """Banking details (IBAN, BIC, Chamber of Commerce, VAT) are accepted."""
        customer = Customer(
            company_name="Example Company A",
            ibanno="NL63INGB0004511811",
            bicno="INGBNL2A",
            cocno="50725769",
            vatno="NL822891682B01",
            vat_liable=1,
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1
