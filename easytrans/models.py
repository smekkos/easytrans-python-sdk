"""
Data models for EasyTrans SDK.

All models are implemented as dataclasses with:
- Type hints for all fields
- to_dict() method for JSON serialization
- from_dict() class method for deserialization
- Optional field validation in __post_init__()
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


def _clean_dict(data: Dict[str, Any], remove_none: bool = True) -> Dict[str, Any]:
    """
    Clean dictionary for JSON serialization.
    
    Args:
        data: Dictionary to clean
        remove_none: Whether to remove None values
    
    Returns:
        Cleaned dictionary
    """
    if not remove_none:
        return data
    
    return {k: v for k, v in data.items() if v is not None and v != "" and v != [] and v != {}}


@dataclass
class Document:
    """
    Document to upload with order destination.
    
    Supports PDF, Excel, and Word documents encoded as base64.
    Maximum 2 documents per destination.
    """

    type: str  # "pdf" | "xls" | "xlsx" | "doc" | "docx"
    base64_content: str
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return _clean_dict(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create Document from dictionary."""
        return cls(**data)


@dataclass
class Destination:
    """
    Order destination (pickup or delivery address).
    
    Minimum of 2 destinations required per order
    (1 pickup + 1 delivery).
    """

    company_name: str = ""
    contact: str = ""
    address: str = ""
    houseno: str = ""
    addition: str = ""
    address2: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = ""
    telephone: str = ""
    destinationno: Optional[int] = None
    collect_deliver: int = 0  # 0=Pickup, 1=Delivery, 2=Both
    destination_remark: str = ""
    customer_reference: str = ""
    waybillno: str = ""
    delivery_date: str = ""
    delivery_time: str = ""
    delivery_time_from: str = ""
    documents: List[Document] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert documents to dict
        if self.documents:
            data["documents"] = [doc.to_dict() for doc in self.documents]
        return _clean_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Destination":
        """Create Destination from dictionary."""
        # Convert documents
        if "documents" in data and data["documents"]:
            data["documents"] = [Document.from_dict(d) for d in data["documents"]]
        return cls(**data)


@dataclass
class Package:
    """
    Package/goods line for an order.
    
    Represents goods of the same type, weight, and dimensions.
    Multiple packages of same type can be specified via 'amount'.
    """

    amount: float = 0.0
    weight: float = 0.0  # kg per package (not total)
    length: float = 0.0  # cm
    width: float = 0.0  # cm
    height: float = 0.0  # cm
    description: str = ""
    collect_destinationno: Optional[int] = None
    deliver_destinationno: Optional[int] = None
    ratetypeno: int = 0  # 0 = standard "Packages" rate type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return _clean_dict(asdict(self), remove_none=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Package":
        """Create Package from dictionary."""
        return cls(**data)


@dataclass
class Order:
    """
    Transport order with destinations and packages.
    
    Required fields:
    - productno: Product number from carrier
    - order_destinations: Minimum 2 destinations (pickup + delivery)
    """

    productno: int
    order_destinations: List[Destination]
    date: Optional[str] = None  # "yyyy-mm-dd" or None for current date
    time: Optional[str] = None  # "hh:mm" or None for current time
    status: str = "submit"  # "save" | "submit" | "quote"
    customerno: Optional[int] = None  # Required for branch accounts
    carrierno: int = 0
    vehicleno: int = 0
    fleetno: Optional[int] = None
    substatusno: Optional[int] = None
    remark: str = ""
    remark_invoice: str = ""
    remark_internal: str = ""  # Branch only
    remark_purchase: str = ""  # Branch only
    no_confirmation_email: bool = False
    email_receiver: str = ""
    price: float = 0.0  # Branch only
    price_description: str = "Other costs"  # Branch only
    purchase_price: float = 0.0  # Branch only
    purchase_price_description: str = "Other costs"  # Branch only
    carrier_service: str = ""  # For DPD/Packs/GLS
    carrier_options: str = ""  # Comma-separated options
    external_id: str = ""  # Reference to external system
    order_packages: List[Package] = field(default_factory=list)

    def __post_init__(self):
        """Validate order after initialization."""
        if not self.order_destinations or len(self.order_destinations) < 2:
            raise ValueError("Order requires minimum of 2 destinations (pickup + delivery)")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert destinations
        if self.order_destinations:
            data["order_destinations"] = [dest.to_dict() for dest in self.order_destinations]
        # Convert packages
        if self.order_packages:
            data["order_packages"] = [pkg.to_dict() for pkg in self.order_packages]
        return _clean_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        """Create Order from dictionary."""
        # Convert destinations
        if "order_destinations" in data:
            data["order_destinations"] = [
                Destination.from_dict(d) for d in data["order_destinations"]
            ]
        # Convert packages
        if "order_packages" in data:
            data["order_packages"] = [Package.from_dict(p) for p in data["order_packages"]]
        return cls(**data)


@dataclass
class CustomerContact:
    """
    Contact person for a customer.
    
    Can optionally have portal access credentials.
    """

    contact_name: str = ""
    salutation: int = 0  # 0=Unknown, 1=Mr., 2=Mrs./Ms., 3=Attn.
    telephone: str = ""
    mobile: str = ""
    email: str = ""
    use_email_for_invoice: bool = True
    use_email_for_reminder: bool = True
    contact_remark: str = ""
    username: str = ""  # For portal access
    password: str = ""  # For portal access
    userid: Optional[int] = None  # For updating existing contacts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return _clean_dict(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomerContact":
        """Create CustomerContact from dictionary."""
        return cls(**data)


@dataclass
class Customer:
    """
    Customer entity with address and contact information.
    
    Required field:
    - company_name: Company or person name
    """

    company_name: str
    customerno: Optional[int] = None
    update_on_existing_customerno: bool = False
    delete_existing_customer_contacts: bool = False
    attn: str = ""
    address: str = ""
    houseno: str = ""
    addition: str = ""
    address2: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = ""
    # Mailing address (defaults to main address if not provided)
    mail_address: str = ""
    mail_houseno: str = ""
    mail_addition: str = ""
    mail_address2: str = ""
    mail_postal_code: str = ""
    mail_city: str = ""
    mail_country: str = ""
    # Additional fields
    debtorno: str = ""  # External debtor number
    payment_ref: str = ""
    website: str = ""
    remark: str = ""
    crm_notes: str = ""
    # Banking
    ibanno: str = ""
    bicno: str = ""
    bankno: str = ""  # Non-SEPA
    uk_sort_code: str = ""
    # Registration numbers
    cocno: str = ""  # Chamber of commerce
    vatno: str = ""  # VAT number
    eorino: str = ""  # Economic Operators Registration
    # Settings
    payment_method: str = ""  # See PaymentMethod enum
    vat_liable: int = 1  # 0=Shifted, 1=Liable, 2=Export
    language: str = ""  # "nl", "en", "de", "fr", or ""
    external_id: str = ""  # Reference to external system
    customer_contacts: List[CustomerContact] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert contacts
        if self.customer_contacts:
            data["customer_contacts"] = [contact.to_dict() for contact in self.customer_contacts]
        return _clean_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Customer":
        """Create Customer from dictionary."""
        # Convert contacts
        if "customer_contacts" in data and data["customer_contacts"]:
            data["customer_contacts"] = [
                CustomerContact.from_dict(c) for c in data["customer_contacts"]
            ]
        return cls(**data)


@dataclass
class OrderTrackTrace:
    """Track and trace information for an order."""

    local_trackingnr: str
    local_tracktrace_url: str
    global_trackingnr: str
    global_tracktrace_url: str
    status: str  # "quote", "saved-weborder", "pending-acceptation", "accepted"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderTrackTrace":
        """Create OrderTrackTrace from dictionary."""
        return cls(**data)


@dataclass
class OrderRate:
    """Rate information for an order."""

    rates: List[Dict[str, Any]]  # [{"description": str, "price": float}, ...]
    order_total_excluding_vat: float
    order_total_including_vat: float
    warnings: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderRate":
        """Create OrderRate from dictionary."""
        return cls(**data)


@dataclass
class OrderResult:
    """
    Result of order import operation.
    
    Contains created order numbers, tracking info, and optional rates/documents.
    """

    mode: str  # "test" or "effect"
    total_orders: int
    total_order_destinations: int
    total_order_packages: int
    result_description: str
    new_ordernos: List[int]
    order_tracktrace: Dict[str, OrderTrackTrace] = field(default_factory=dict)
    order_rates: Optional[Dict[str, OrderRate]] = None
    order_documents: Optional[Dict[str, Dict[str, str]]] = None
    packs_response: Optional[Dict[str, Any]] = None
    gls_response: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderResult":
        """Create OrderResult from dictionary."""
        # Convert order_tracktrace
        if "order_tracktrace" in data and data["order_tracktrace"]:
            data["order_tracktrace"] = {
                orderno: OrderTrackTrace.from_dict(tt_data)
                for orderno, tt_data in data["order_tracktrace"].items()
            }
        
        # Convert order_rates if present
        if "order_rates" in data and data["order_rates"]:
            data["order_rates"] = {
                orderno: OrderRate.from_dict(rate_data)
                for orderno, rate_data in data["order_rates"].items()
            }
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class CustomerResult:
    """
    Result of customer import operation.
    
    Contains created customer numbers and user IDs for contacts.
    """

    mode: str  # "test" or "effect"
    total_customers: int
    total_customer_contacts: int
    result_description: str
    new_customernos: List[int]
    new_userids: Dict[int, List[int]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomerResult":
        """Create CustomerResult from dictionary."""
        # Convert new_userids keys to int if they're strings
        if "new_userids" in data and data["new_userids"]:
            data["new_userids"] = {
                int(k): v for k, v in data["new_userids"].items()
            }
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class TaskResult:
    """Task result information in webhook payload."""

    date: Optional[str] = None
    arrivalTime: Optional[str] = None
    departureTime: Optional[str] = None
    signedBy: Optional[str] = None
    base64EncodedSignature: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskResult":
        """Create TaskResult from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class WebhookDestination:
    """Destination information in webhook payload."""

    addressId: int
    stopNo: int
    customerReference: str
    waybillNo: str
    notes: str
    taskType: str  # "pickup" | "delivery" | "pickup/delivery"
    taskResult: TaskResult

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookDestination":
        """Create WebhookDestination from dictionary."""
        if "taskResult" in data:
            data["taskResult"] = TaskResult.from_dict(data["taskResult"])
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class WebhookOrder:
    """Order information in webhook payload."""

    orderNo: int
    customerNo: int
    status: str  # "in-progress" | "collected" | "finished" | "exception"
    subStatusId: Optional[int] = None
    subStatusName: Optional[str] = None
    destinations: List[WebhookDestination] = field(default_factory=list)
    externalId: Optional[str] = None
    exceptionCode: Optional[int] = None  # Only for Packs exceptions
    exceptionDescription: Optional[str] = None  # Only for Packs exceptions

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookOrder":
        """Create WebhookOrder from dictionary."""
        if "destinations" in data and data["destinations"]:
            data["destinations"] = [
                WebhookDestination.from_dict(d) for d in data["destinations"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class WebhookPayload:
    """
    Webhook callback payload from EasyTrans.
    
    Sent when order status changes (collected, finished, etc.).
    """

    companyId: int
    eventTime: str  # ISO 8601 datetime
    order: WebhookOrder

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookPayload":
        """Create WebhookPayload from dictionary."""
        if "order" in data:
            data["order"] = WebhookOrder.from_dict(data["order"])
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def get_event_datetime(self) -> datetime:
        """Parse eventTime to datetime object."""
        return datetime.fromisoformat(self.eventTime.replace("+", " +"))
