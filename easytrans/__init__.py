"""
EasyTrans Python SDK
====================

A pure Python SDK for integrating with EasyTrans Software (Dutch TMS system).

Both the proprietary JSON Import API and the REST API (``/api/v1/``) are
exposed through the same ``EasyTransClient`` — no extra configuration needed.

Basic Usage::

    from easytrans import EasyTransClient, Order, Destination

    client = EasyTransClient(
        server_url="mytrans.nl",
        environment_name="production",
        username="your_username",
        password="your_password",
    )

    # ── JSON Import (create orders / customers) ──────────────────────────────
    order = Order(
        productno=2,
        date="2026-02-18",
        order_destinations=[
            Destination(company_name="Sender", postal_code="1234AB", city="Amsterdam"),
            Destination(company_name="Receiver", postal_code="5678CD", city="Utrecht"),
        ],
    )
    result = client.import_orders([order], mode="effect")
    print(f"Order created: {result.new_ordernos[0]}")

    # ── REST API (read back) ─────────────────────────────────────────────────
    rest_order = client.get_order(result.new_ordernos[0], include_track_history=True)
    print(f"Status:     {rest_order.attributes.status}")
    print(f"Tracking:   {rest_order.attributes.tracking_id}")
    print(f"Created:    {rest_order.created_at}")

For more examples, see ``README.md`` and the ``examples/`` directory.
"""

from easytrans.client import EasyTransClient
from easytrans.exceptions import (
    EasyTransError,
    EasyTransAPIError,
    EasyTransAuthError,
    EasyTransValidationError,
    EasyTransOrderError,
    EasyTransDestinationError,
    EasyTransPackageError,
    EasyTransCustomerError,
    EasyTransNotFoundError,
    EasyTransRateLimitError,
)
from easytrans.models import (
    Order,
    Destination,
    Package,
    Document,
    Customer,
    CustomerContact,
    OrderResult,
    CustomerResult,
    OrderTrackTrace,
    WebhookPayload,
)
from easytrans.rest_models import (
    PaginationLinks,
    PaginationMeta,
    PagedResponse,
    RestAddress,
    RestMailingAddress,
    RestLocation,
    RestDestination,
    RestGoodsLine,
    RestRate,
    RestTrackHistoryEntry,
    RestCustomerContact,
    RestCustomer,
    RestCarrierContact,
    RestCarrier,
    RestOrderAttributes,
    RestOrder,
    RestProduct,
    RestSubstatus,
    RestPackageType,
    RestVehicleType,
    RestFleetVehicle,
    RestInvoice,
)
from easytrans.constants import (
    AuthType,
    Mode,
    OrderStatus,
    CollectDeliver,
    Salutation,
    DocumentType,
    PaymentMethod,
    VatLiable,
    RestOrderStatus,
    TaskType,
)

__version__ = "1.1.0"

__all__ = [
    # ── Client ──────────────────────────────────────────────────────────────
    "EasyTransClient",
    # ── Exceptions ──────────────────────────────────────────────────────────
    "EasyTransError",
    "EasyTransAPIError",
    "EasyTransAuthError",
    "EasyTransValidationError",
    "EasyTransOrderError",
    "EasyTransDestinationError",
    "EasyTransPackageError",
    "EasyTransCustomerError",
    "EasyTransNotFoundError",
    "EasyTransRateLimitError",
    # ── JSON Import models ───────────────────────────────────────────────────
    "Order",
    "Destination",
    "Package",
    "Document",
    "Customer",
    "CustomerContact",
    "OrderResult",
    "CustomerResult",
    "OrderTrackTrace",
    "WebhookPayload",
    # ── REST API models ──────────────────────────────────────────────────────
    "PaginationLinks",
    "PaginationMeta",
    "PagedResponse",
    "RestAddress",
    "RestMailingAddress",
    "RestLocation",
    "RestDestination",
    "RestGoodsLine",
    "RestRate",
    "RestTrackHistoryEntry",
    "RestCustomerContact",
    "RestCustomer",
    "RestCarrierContact",
    "RestCarrier",
    "RestOrderAttributes",
    "RestOrder",
    "RestProduct",
    "RestSubstatus",
    "RestPackageType",
    "RestVehicleType",
    "RestFleetVehicle",
    "RestInvoice",
    # ── Constants ────────────────────────────────────────────────────────────
    "AuthType",
    "Mode",
    "OrderStatus",
    "CollectDeliver",
    "Salutation",
    "DocumentType",
    "PaymentMethod",
    "VatLiable",
    "RestOrderStatus",
    "TaskType",
]
