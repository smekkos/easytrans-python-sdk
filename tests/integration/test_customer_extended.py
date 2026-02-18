"""
Integration test: extended customer import with portal credentials.

Mirrors the 'extended' example from the official documentation:
  EasyTrans - JSON customer import example - extended.json

Exercises every field not covered by the simple test:
- Two contacts in one customer, each with portal username + password
- debtorno, payment_ref, crm_notes, eorino
- payment_method enum value ("bank_transfer")
- language setting
- Full mailing-address block (separate from the main address)

Key risks this test catches:
- Portal credential fields (username/password on CustomerContact) do not
  conflict with the SDK's own auth credentials in the request body
- payment_method string values match what the API expects
- crm_notes and eorino are accepted as unknown-to-the-SDK-tests fields
- Two contacts in one customer are counted correctly in
  result.total_customer_contacts
"""

import pytest
from easytrans import Customer
from easytrans.constants import PaymentMethod, Language, VatLiable
from easytrans.models import CustomerResult

pytestmark = pytest.mark.integration


class TestExtendedCustomerImport:
    """Customer with two portal-enabled contacts and all extended fields."""

    def test_extended_customer_accepted(self, real_client, portal_contacts):
        """Full extended customer payload is accepted by the API."""
        customer = Customer(
            company_name="Example Company A",
            attn="Administration",
            address="Keizersgracht",
            houseno="1",
            addition="a",
            address2="2nd floor",
            postal_code="1015CC",
            city="Amsterdam",
            country="NL",
            mail_address="Postbus",
            mail_houseno="73",
            mail_postal_code="1010AA",
            mail_city="Amsterdam",
            mail_country="NL",
            debtorno="ABC1234",
            payment_ref="Example project",
            website="www.example.com",
            remark="Customer remark",
            crm_notes="Customer Relationship Management remarks",
            ibanno="NL63INGB0004511811",
            bicno="INGBNL2A",
            cocno="50725769",
            vatno="NL822891682B01",
            eorino="NL822891682",
            payment_method=PaymentMethod.BANK_TRANSFER.value,
            vat_liable=VatLiable.LIABLE.value,
            language=Language.DUTCH.value,
            external_id="integration-test-customer-ext-001",
            customer_contacts=portal_contacts,
        )

        result = real_client.import_customers([customer], mode="test")

        assert isinstance(result, CustomerResult)
        assert result.mode == "test"
        assert result.total_customers == 1

    def test_two_contacts_counted_correctly(self, real_client, portal_contacts):
        """total_customer_contacts must equal the number of contacts sent (2)."""
        customer = Customer(
            company_name="Example Company A",
            postal_code="1015CC",
            city="Amsterdam",
            customer_contacts=portal_contacts,   # 2 contacts
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customer_contacts == 2

    def test_portal_credentials_do_not_conflict_with_auth(self, real_client, portal_contacts):
        """
        CustomerContact.username and CustomerContact.password are nested inside
        the customers array — they must not interfere with the top-level
        authentication block in the JSON body.
        """
        customer = Customer(
            company_name="Portal Test Company",
            customer_contacts=portal_contacts,
        )

        # If auth were confused with contact credentials this would raise
        # EasyTransAuthError
        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1

    def test_payment_method_bank_transfer_accepted(self, real_client, simple_customer_contact):
        """payment_method='bank_transfer' is a valid enum value."""
        customer = Customer(
            company_name="Payment Method Test",
            payment_method=PaymentMethod.BANK_TRANSFER.value,
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1

    def test_payment_method_bank_transfer_online_accepted(
        self, real_client, simple_customer_contact
    ):
        """payment_method='bank_transfer_online_payment' is accepted (extended doc uses it)."""
        customer = Customer(
            company_name="Online Payment Test",
            payment_method=PaymentMethod.BANK_TRANSFER_ONLINE_PAYMENT.value,
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1

    def test_language_field_accepted(self, real_client, simple_customer_contact):
        """language='nl' and language='en' are both accepted without errors."""
        for lang in (Language.DUTCH.value, Language.ENGLISH.value):
            customer = Customer(
                company_name="Language Test Company",
                language=lang,
                customer_contacts=[simple_customer_contact],
            )

            result = real_client.import_customers([customer], mode="test")

            assert result.total_customers == 1

    def test_crm_notes_and_eorino_accepted(self, real_client, simple_customer_contact):
        """crm_notes and eorino are accepted without causing a validation error."""
        customer = Customer(
            company_name="CRM Test Company",
            crm_notes="Some CRM notes for testing",
            eorino="NL822891682",
            customer_contacts=[simple_customer_contact],
        )

        result = real_client.import_customers([customer], mode="test")

        assert result.total_customers == 1
