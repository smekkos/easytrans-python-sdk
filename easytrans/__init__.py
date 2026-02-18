"""
EasyTrans Python SDK
====================

A pure Python SDK for integrating with EasyTrans Software (Dutch TMS system).

Basic Usage:
    >>> from easytrans import EasyTransClient, Order, Destination
    >>> 
    >>> client = EasyTransClient(
    ...     server_url="mytrans.nl",
    ...     environment_name="production",
    ...     username="your_username",
    ...     password="your_password"
    ... )
    >>> 
    >>> order = Order(
    ...     productno=2,
    ...     date="2026-02-18",
    ...     order_destinations=[
    ...         Destination(company_name="Sender", postal_code="1234AB", city="Amsterdam"),
    ...         Destination(company_name="Receiver", postal_code="5678CD", city="Utrecht"),
    ...     ]
    ... )
    >>> 
    >>> result = client.import_orders([order], mode="effect")
    >>> print(f"Order created: {result.new_ordernos[0]}")

For more examples, see the documentation at:
https://github.com/yourusername/easytrans-sdk
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
from easytrans.constants import (
    AuthType,
    Mode,
    OrderStatus,
    CollectDeliver,
    Salutation,
    DocumentType,
    PaymentMethod,
    VatLiable,
)

__version__ = "1.0.0"
__all__ = [
    # Client
    "EasyTransClient",
    # Exceptions
    "EasyTransError",
    "EasyTransAPIError",
    "EasyTransAuthError",
    "EasyTransValidationError",
    "EasyTransOrderError",
    "EasyTransDestinationError",
    "EasyTransPackageError",
    "EasyTransCustomerError",
    # Models
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
    # Constants
    "AuthType",
    "Mode",
    "OrderStatus",
    "CollectDeliver",
    "Salutation",
    "DocumentType",
    "PaymentMethod",
    "VatLiable",
]
