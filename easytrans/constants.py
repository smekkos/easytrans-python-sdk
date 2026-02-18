"""
Constants and enumerations for EasyTrans SDK.
"""

from enum import Enum


class AuthType(str, Enum):
    """API authentication/import types."""

    ORDER_IMPORT = "order_import"
    CUSTOMER_IMPORT = "customer_import"
    PACKS_ORDER_IMPORT = "packs_order_import"
    GLS_ORDER_IMPORT = "gls_order_import"


class Mode(str, Enum):
    """API operation modes."""

    TEST = "test"  # Validate but don't process
    EFFECT = "effect"  # Process and save data


class OrderStatus(str, Enum):
    """Order submission statuses."""

    SAVE = "save"  # Save as draft
    SUBMIT = "submit"  # Submit for processing
    QUOTE = "quote"  # Request quote only


class CollectDeliver(int, Enum):
    """Destination types (pickup/delivery)."""

    PICKUP = 0
    DELIVERY = 1
    BOTH = 2  # Pickup and delivery (multi-stop)


class Salutation(int, Enum):
    """Contact person salutations."""

    UNKNOWN = 0  # Dear...
    MR = 1  # Dear Mr....
    MRS_MS = 2  # Dear Ms....
    ATTN = 3  # Attn.


class DocumentType(str, Enum):
    """Supported document file types for upload."""

    PDF = "pdf"
    XLS = "xls"
    XLSX = "xlsx"
    DOC = "doc"
    DOCX = "docx"


class ReturnDocumentType(str, Enum):
    """Document types that can be returned in API response."""

    NONE = ""
    DELIVERY_NOTE = "delivery_note"
    ORDERLIST = "orderlist"
    ORDERLIST_LANDSCAPE = "orderlist_landscape"
    LABEL_10X15 = "label10x15"
    LABEL_4XA6_1 = "label4xa6_1"  # Position 1 (top left)
    LABEL_4XA6_2 = "label4xa6_2"  # Position 2 (top right)
    LABEL_4XA6_3 = "label4xa6_3"  # Position 3 (bottom left)
    LABEL_4XA6_4 = "label4xa6_4"  # Position 4 (bottom right)
    CMR = "cmr"


class PaymentMethod(str, Enum):
    """Customer payment methods."""

    EMPTY = ""  # Defaults to bank transfer
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    DIRECT_DEBIT = "direct_debit"
    ONLINE_PAYMENT = "online_payment"
    BANK_TRANSFER_ONLINE_PAYMENT = "bank_transfer_online_payment"
    CREDITCARD = "creditcard"
    FACTORING = "factoring"


class VatLiable(int, Enum):
    """VAT liability status."""

    NOT_LIABLE_SHIFTED = 0  # Not liable, VAT shifted (EU)
    LIABLE = 1  # Liable to pay tax
    NOT_LIABLE_EXPORT = 2  # Not liable, export (outside EU)


class Language(str, Enum):
    """Supported languages for documents and emails."""

    DUTCH = "nl"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    DEFAULT = ""  # Use carrier's default


class WebhookStatus(str, Enum):
    """Order statuses in webhook callbacks."""

    IN_PROGRESS = "in-progress"
    COLLECTED = "collected"
    FINISHED = "finished"
    EXCEPTION = "exception"


class TaskType(str, Enum):
    """Destination task types in webhooks."""

    PICKUP = "pickup"
    DELIVERY = "delivery"
    PICKUP_DELIVERY = "pickup/delivery"
