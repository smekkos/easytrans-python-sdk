"""
Integration test: order import with a base64-encoded document attached.

Mirrors the 'simple with document' example from the official documentation:
  EasyTrans - JSON order import example - simple with document.json

The documentation shows a PDF attached to the pickup destination's 'documents'
list. The Document model serializes to {"name": ..., "type": ..., "base64_content": ...}.

Key risks this test catches:
- Document.to_dict() produces the exact key names the API expects
- The base64_content field name is correct (not "content" or "data")
- A non-empty base64 PDF string is accepted without rejection
- The documents list is correctly nested inside the destination dict,
  not at the order level

Requires:
    EASYTRANS_TEST_PRODUCTNO   — a valid product number in your environment
    EASYTRANS_TEST_CUSTOMERNO  — required only for branch accounts (errorno 23)
"""

import pytest
from easytrans import Order, Destination
from easytrans.models import Document
from easytrans.constants import CollectDeliver, DocumentType

pytestmark = pytest.mark.integration

# Minimal valid PDF encoded as base64 (3×3 pt blank page, ~500 bytes).
_MINIMAL_PDF_BASE64 = (
    "JVBERi0xLjAKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2Jq"
    "CjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2Jq"
    "CjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAzIDNd"
    "ID4+CmVuZG9iagp4cmVmCjAgNAowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMDkgMDAwMDAgbiAK"
    "MDAwMDAwMDA1OCAwMDAwMCBuIAowMDAwMDAwMTE1IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNC"
    "AvUm9vdCAxIDAgUiA+PgpzdGFydHhyZWYKMTkwCiUlRU9G"
)


class TestOrderWithDocument:
    """Order import with a base64 PDF attached to a destination."""

    def test_order_with_pdf_document_accepted(self, real_client, productno, customerno):
        """
        An order whose pickup destination carries a PDF Document is accepted.

        Verifies that Document serialisation produces the field names
        {"name", "type", "base64_content"} that the API requires.
        """
        pickup = Destination(
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
            documents=[
                Document(
                    name="Commercial invoice",
                    type=DocumentType.PDF.value,
                    base64_content=_MINIMAL_PDF_BASE64,
                )
            ],
        )
        delivery = Destination(
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
        )

        order = Order(
            productno=productno,
            customerno=customerno,
            date="2026-06-01",
            time="14:45",
            status="submit",
            remark="1 Euro pallet with brochures",
            remark_invoice="P/O Number: ABCD1234",
            external_id="integration-test-document-001",
            order_destinations=[pickup, delivery],
        )

        result = real_client.import_orders([order], mode="test")

        assert result.mode == "test"
        assert result.total_orders == 1
        assert result.total_order_destinations == 2

    def test_document_name_field_accepted(self, real_client, productno, customerno):
        """
        The optional Document.name field is transmitted correctly and does not
        cause an API validation error when present.
        """
        pickup = Destination(
            collect_deliver=CollectDeliver.PICKUP.value,
            company_name="Sender",
            postal_code="1015CC",
            city="Amsterdam",
            documents=[
                Document(
                    name="Packing List",
                    type=DocumentType.PDF.value,
                    base64_content=_MINIMAL_PDF_BASE64,
                )
            ],
        )
        delivery = Destination(
            collect_deliver=CollectDeliver.DELIVERY.value,
            company_name="Receiver",
            postal_code="3526KL",
            city="Utrecht",
        )

        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=[pickup, delivery],
        )

        result = real_client.import_orders([order], mode="test")

        assert result.total_orders == 1

    def test_document_on_delivery_destination_accepted(
        self, real_client, productno, customerno
    ):
        """
        A document attached to the *delivery* destination (not pickup)
        is also accepted by the API.
        """
        pickup = Destination(
            collect_deliver=CollectDeliver.PICKUP.value,
            company_name="Sender",
            postal_code="1015CC",
            city="Amsterdam",
        )
        delivery = Destination(
            collect_deliver=CollectDeliver.DELIVERY.value,
            company_name="Receiver",
            postal_code="3526KL",
            city="Utrecht",
            documents=[
                Document(
                    name="Delivery Confirmation",
                    type=DocumentType.PDF.value,
                    base64_content=_MINIMAL_PDF_BASE64,
                )
            ],
        )

        order = Order(
            productno=productno,
            customerno=customerno,
            order_destinations=[pickup, delivery],
        )

        result = real_client.import_orders([order], mode="test")

        assert result.total_orders == 1
