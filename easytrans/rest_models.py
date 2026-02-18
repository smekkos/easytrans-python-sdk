"""
Response models for the EasyTrans REST API (``/api/v1/``).

All models are read-only dataclasses that mirror the OpenAPI schema returned
by the REST endpoints. They are populated via their ``from_dict()`` class
methods and are never serialised back to JSON (use the client's keyword
arguments for write operations instead).

Naming convention:
  - ``Rest`` prefix avoids name collisions with the existing JSON-import
    models in ``models.py`` (``Order``, ``Customer``, etc.)
  - Nested attribute bags are collapsed into explicit fields to give clean
    IDE auto-complete without dictionary look-ups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

T = TypeVar("T")


@dataclass
class PaginationLinks:
    """Pagination cursor links returned with every list response."""

    first: Optional[str] = None
    last: Optional[str] = None
    prev: Optional[str] = None
    next: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaginationLinks":
        return cls(
            first=data.get("first"),
            last=data.get("last"),
            prev=data.get("prev"),
            next=data.get("next"),
        )


@dataclass
class PaginationMeta:
    """Pagination metadata returned with every list response."""

    current_page: int = 1
    last_page: int = 1
    per_page: int = 100
    total: int = 0
    from_record: Optional[int] = None   # ``from`` is a Python keyword
    to_record: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaginationMeta":
        return cls(
            current_page=data.get("current_page", 1),
            last_page=data.get("last_page", 1),
            per_page=data.get("per_page", 100),
            total=data.get("total", 0),
            from_record=data.get("from"),
            to_record=data.get("to"),
        )


@dataclass
class PagedResponse(Generic[T]):
    """
    Generic paginated list response wrapper.

    ``has_next`` is a convenience flag for ``bool(links.next)``.
    Iterate pages by passing the ``links.next`` URL back to the
    same client method with the ``page`` parameter, or let the
    ``_iter_pages`` helper handle it automatically.
    """

    data: List[T]
    links: PaginationLinks
    meta: PaginationMeta
    has_next: bool = False

    @classmethod
    def from_dict(
        cls,
        raw: Dict[str, Any],
        item_cls: Any,
    ) -> "PagedResponse[Any]":
        links = PaginationLinks.from_dict(raw.get("links") or {})
        meta = PaginationMeta.from_dict(raw.get("meta") or {})
        data = [item_cls.from_dict(item) for item in raw.get("data", [])]
        return cls(
            data=data,
            links=links,
            meta=meta,
            has_next=bool(links.next),
        )


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

@dataclass
class RestAddress:
    """Business or mailing address block."""

    address: str = ""
    houseno: str = ""
    address2: str = ""
    postcode: str = ""
    city: str = ""
    country: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["RestAddress"]:
        if data is None:
            return None
        return cls(
            address=data.get("address", ""),
            houseno=data.get("houseno", ""),
            address2=data.get("address2", ""),
            postcode=data.get("postcode", ""),
            city=data.get("city", ""),
            country=data.get("country", ""),
        )


@dataclass
class RestMailingAddress(RestAddress):
    """Mailing address block — extends RestAddress with an ``attn`` field."""

    attn: str = ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["RestMailingAddress"]:
        if data is None:
            return None
        return cls(
            address=data.get("address", ""),
            houseno=data.get("houseno", ""),
            address2=data.get("address2", ""),
            postcode=data.get("postcode", ""),
            city=data.get("city", ""),
            country=data.get("country", ""),
            attn=data.get("attn", ""),
        )


@dataclass
class RestLocation:
    """GPS coordinates attached to a destination."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["RestLocation"]:
        if not data:
            return None
        return cls(
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )


@dataclass
class RestDestination:
    """
    A pickup or delivery stop on a transport order.

    Read-only — destination updates are sent as plain dicts via
    ``update_order(destinations=[...])``.
    """

    address_id: Optional[int] = None
    stop_no: Optional[int] = None
    task_type: Optional[str] = None          # "pickup" | "delivery"
    company: str = ""
    contact: str = ""
    address: str = ""
    houseno: str = ""
    address2: str = ""
    postcode: str = ""
    city: str = ""
    country: str = ""
    location: Optional[RestLocation] = None
    phone: str = ""
    notes: str = ""
    customer_reference: str = ""
    waybill_no: str = ""
    date: Optional[str] = None
    from_time: Optional[str] = None
    to_time: Optional[str] = None
    eta: Optional[str] = None
    delivery_date: Optional[str] = None
    delivery_time: Optional[str] = None
    departure_time: Optional[str] = None
    delivery_name: str = ""
    signature_url: Union[str, bool, None] = None
    photos: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    carrier_notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestDestination":
        return cls(
            address_id=data.get("addressId"),
            stop_no=data.get("stopNo"),
            task_type=data.get("taskType"),
            company=data.get("company", ""),
            contact=data.get("contact", ""),
            address=data.get("address", ""),
            houseno=data.get("houseno", ""),
            address2=data.get("address2", ""),
            postcode=data.get("postcode", ""),
            city=data.get("city", ""),
            country=data.get("country", ""),
            location=RestLocation.from_dict(data.get("location")),
            phone=data.get("phone", ""),
            notes=data.get("notes", ""),
            customer_reference=data.get("customerReference", ""),
            waybill_no=data.get("waybillNo", ""),
            date=data.get("date"),
            from_time=data.get("fromTime"),
            to_time=data.get("toTime"),
            eta=data.get("eta"),
            delivery_date=data.get("deliveryDate"),
            delivery_time=data.get("deliveryTime"),
            departure_time=data.get("departureTime"),
            delivery_name=data.get("deliveryName", ""),
            signature_url=data.get("signatureUrl"),
            photos=data.get("photos") or [],
            documents=data.get("documents") or [],
            carrier_notes=data.get("carrierNotes", ""),
        )


@dataclass
class RestGoodsLine:
    """A line of goods (package) on a transport order."""

    package_id: Optional[int] = None
    package_no: Optional[int] = None
    pickup_destination: Optional[int] = None
    delivery_destination: Optional[int] = None
    amount: int = 0
    package_type_no: Optional[int] = None
    package_type_name: str = ""
    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestGoodsLine":
        return cls(
            package_id=data.get("packageId"),
            package_no=data.get("packageNo"),
            pickup_destination=data.get("pickupDestination"),
            delivery_destination=data.get("deliveryDestination"),
            amount=data.get("amount", 0),
            package_type_no=data.get("packageTypeNo"),
            package_type_name=data.get("packageTypeName", ""),
            weight=data.get("weight"),
            length=data.get("length"),
            width=data.get("width"),
            height=data.get("height"),
            description=data.get("description", ""),
        )


@dataclass
class RestRate:
    """A sales or purchase rate line attached to an order."""

    rate_no: int = 0
    description: str = ""
    rate_per_unit: str = "0.00000"
    sub_total: str = "0.00"
    is_minimum_amount: bool = False
    is_percentage: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestRate":
        return cls(
            rate_no=data.get("rateNo", 0),
            description=data.get("description", ""),
            rate_per_unit=data.get("ratePerUnit", "0.00000"),
            sub_total=data.get("subTotal", "0.00"),
            is_minimum_amount=data.get("isMinimumAmount", False),
            is_percentage=data.get("isPercentage", False),
        )


@dataclass
class RestTrackHistoryEntry:
    """A single entry in the Track & Trace history of an order."""

    track_id: Optional[int] = None
    name: str = ""
    location: str = ""
    date: Optional[str] = None
    time: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestTrackHistoryEntry":
        return cls(
            track_id=data.get("trackId"),
            name=data.get("name", ""),
            location=data.get("location", ""),
            date=data.get("date"),
            time=data.get("time"),
        )


# ---------------------------------------------------------------------------
# Customer models
# ---------------------------------------------------------------------------

@dataclass
class RestCustomerContact:
    """A contact person belonging to a customer record."""

    user_id: Optional[int] = None
    contact_no: Optional[int] = None
    salutation: int = 0
    name: str = ""
    phone: str = ""
    mobile: str = ""
    email: str = ""
    use_email_for_invoice: bool = False
    use_email_for_reminder: bool = False
    notes: str = ""
    username: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestCustomerContact":
        return cls(
            user_id=data.get("userId"),
            contact_no=data.get("contactNo"),
            salutation=data.get("salutation", 0),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            mobile=data.get("mobile", ""),
            email=data.get("email", ""),
            use_email_for_invoice=data.get("useEmailForInvoice", False),
            use_email_for_reminder=data.get("useEmailForReminder", False),
            notes=data.get("notes", ""),
            username=data.get("username", ""),
        )


@dataclass
class RestCustomer:
    """
    Customer record returned by the REST API.

    Available for branch accounts via ``GET /v1/customers`` or embedded
    inside order and invoice responses when ``include_customer=True``.
    """

    id: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Core attributes
    customer_no: int = 0
    company_name: str = ""
    business_address: Optional[RestAddress] = None
    mailing_address: Optional[RestMailingAddress] = None
    website: str = ""
    debtor_no: str = ""
    payment_reference: str = ""
    payment_period: int = 0
    payment_period_end_of_month: bool = False
    iban_no: str = ""
    bic_code: str = ""
    bank_no: str = ""
    uk_sort_code: str = ""
    vat_no: str = ""
    vat_liable: bool = True
    vat_liable_code: Optional[int] = None
    chamber_of_commerce_no: str = ""
    eori_no: str = ""
    language: str = ""
    notes: str = ""
    crm_notes: str = ""
    invoice_surcharge: Optional[float] = None
    active: bool = True
    is_deleted: Optional[bool] = None
    contacts: List[RestCustomerContact] = field(default_factory=list)
    external_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestCustomer":
        attrs = data.get("attributes") or data
        contacts = [
            RestCustomerContact.from_dict(c)
            for c in (attrs.get("contacts") or [])
        ]
        return cls(
            id=data.get("id", 0),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            customer_no=attrs.get("customerNo", 0),
            company_name=attrs.get("companyName", ""),
            business_address=RestAddress.from_dict(attrs.get("businessAddress")),
            mailing_address=RestMailingAddress.from_dict(attrs.get("mailingAddress")),
            website=attrs.get("website", ""),
            debtor_no=attrs.get("debtorNo", ""),
            payment_reference=attrs.get("paymentReference", ""),
            payment_period=attrs.get("paymentPeriod", 0),
            payment_period_end_of_month=attrs.get("paymentPeriodEndOfMonth", False),
            iban_no=attrs.get("ibanNo", ""),
            bic_code=attrs.get("bicCode", ""),
            bank_no=attrs.get("bankNo", ""),
            uk_sort_code=attrs.get("ukSortCode", ""),
            vat_no=attrs.get("vatNo", ""),
            vat_liable=attrs.get("vatLiable", True),
            vat_liable_code=attrs.get("vatLiableCode"),
            chamber_of_commerce_no=attrs.get("chamberOfCommerceNo", ""),
            eori_no=attrs.get("eoriNo", ""),
            language=attrs.get("language", ""),
            notes=attrs.get("notes", ""),
            crm_notes=attrs.get("crmNotes", ""),
            invoice_surcharge=attrs.get("invoiceSurcharge"),
            active=attrs.get("active", True),
            is_deleted=attrs.get("isDeleted"),
            contacts=contacts,
            external_id=attrs.get("externalId"),
        )


# ---------------------------------------------------------------------------
# Carrier models
# ---------------------------------------------------------------------------

@dataclass
class RestCarrierContact:
    """A contact person belonging to a carrier record."""

    user_id: Optional[int] = None
    name: str = ""
    phone: str = ""
    mobile: str = ""
    email: str = ""
    notes: str = ""
    username: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestCarrierContact":
        return cls(
            user_id=data.get("userId"),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            mobile=data.get("mobile", ""),
            email=data.get("email", ""),
            notes=data.get("notes", ""),
            username=data.get("username", ""),
        )


@dataclass
class RestCarrier:
    """
    Carrier record returned by the REST API.

    Available for branch accounts via ``GET /v1/carriers`` or embedded
    inside order responses when ``include_carrier=True``.
    """

    id: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    carrier_no: int = 0
    name: str = ""
    business_address: Optional[RestAddress] = None
    mailing_address: Optional[RestMailingAddress] = None
    phone: str = ""
    mobile: str = ""
    email: str = ""
    email_purchase_invoice: str = ""
    website: str = ""
    notes: str = ""
    creditor_no: str = ""
    payment_period: int = 0
    payment_period_end_of_month: bool = False
    iban_no: str = ""
    bic_code: str = ""
    bank_no: str = ""
    uk_sort_code: str = ""
    vat_no: str = ""
    vat_liable: bool = True
    vat_liable_code: Optional[int] = None
    chamber_of_commerce_no: str = ""
    license_no: str = ""
    carrier_attributes: List[str] = field(default_factory=list)
    language: str = ""
    active: bool = True
    is_deleted: Optional[bool] = None
    contacts: List[RestCarrierContact] = field(default_factory=list)
    external_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestCarrier":
        attrs = data.get("attributes") or data
        contacts = [
            RestCarrierContact.from_dict(c)
            for c in (attrs.get("contacts") or [])
        ]
        return cls(
            id=data.get("id", 0),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            carrier_no=attrs.get("carrierNo", 0),
            name=attrs.get("name", ""),
            business_address=RestAddress.from_dict(attrs.get("businessAddress")),
            mailing_address=RestMailingAddress.from_dict(attrs.get("mailingAddress")),
            phone=attrs.get("phone", ""),
            mobile=attrs.get("mobile", ""),
            email=attrs.get("email", ""),
            email_purchase_invoice=attrs.get("emailPurchaseInvoice", ""),
            website=attrs.get("website", ""),
            notes=attrs.get("notes", ""),
            creditor_no=attrs.get("creditorNo", ""),
            payment_period=attrs.get("paymentPeriod", 0),
            payment_period_end_of_month=attrs.get("paymentPeriodEndOfMonth", False),
            iban_no=attrs.get("ibanNo", ""),
            bic_code=attrs.get("bicCode", ""),
            bank_no=attrs.get("bankNo", ""),
            uk_sort_code=attrs.get("ukSortCode", ""),
            vat_no=attrs.get("vatNo", ""),
            vat_liable=attrs.get("vatLiable", True),
            vat_liable_code=attrs.get("vatLiableCode"),
            chamber_of_commerce_no=attrs.get("chamberOfCommerceNo", ""),
            license_no=attrs.get("licenseNo", ""),
            carrier_attributes=attrs.get("carrierAttributes") or [],
            language=attrs.get("language", ""),
            active=attrs.get("active", True),
            is_deleted=attrs.get("isDeleted"),
            contacts=contacts,
            external_id=attrs.get("externalId"),
        )


# ---------------------------------------------------------------------------
# Order models
# ---------------------------------------------------------------------------

@dataclass
class RestOrderAttributes:
    """
    All order attributes from the REST API.

    Branch-only fields (``carrier_no``, ``purchase_*``, etc.) will be
    ``None`` when queried with a customer account.
    """

    order_no: int = 0
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    substatus_no: Optional[int] = None
    substatus_name: Optional[str] = None
    collected: bool = False
    product_no: Optional[int] = None
    product_name: Optional[str] = None
    customer_no: int = 0
    customer_user_id: Optional[int] = None
    carrier_no: Optional[int] = None          # branch only
    carrier_user_id: Optional[int] = None     # branch only
    branch_no: int = 0
    vehicle_type_no: Optional[int] = None
    vehicle_type_name: Optional[str] = None
    fleet_no: Optional[int] = None            # branch only
    user_id: Optional[int] = None             # branch only
    waybill_notes: str = ""
    invoice_notes: str = ""
    purchase_invoice_notes: Optional[str] = None  # branch only
    internal_notes: Optional[str] = None          # branch only
    carrier_notes: Optional[str] = None           # branch only
    recipient_email: Optional[str] = None
    distance: Optional[int] = None
    order_price: Optional[str] = None
    order_purchase_price: Optional[str] = None    # branch only
    prepaid_amount: Optional[str] = None
    ready_for_purchase_invoice: Optional[bool] = None  # branch only
    username_created: Optional[str] = None        # branch only
    username_assigned: Optional[str] = None       # branch only
    invoice_id: int = 0
    tracking_id: Optional[str] = None
    external_id: Optional[str] = None
    is_deleted: Optional[bool] = None
    destinations: List[RestDestination] = field(default_factory=list)
    goods: List[RestGoodsLine] = field(default_factory=list)
    customer: Optional[RestCustomer] = None       # when include_customer=True
    carrier: Optional[RestCarrier] = None         # when include_carrier=True
    sales_rates: List[RestRate] = field(default_factory=list)
    purchase_rates: List[RestRate] = field(default_factory=list)
    track_history: List[RestTrackHistoryEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestOrderAttributes":
        return cls(
            order_no=data.get("orderNo", 0),
            date=data.get("date"),
            time=data.get("time"),
            status=data.get("status"),
            substatus_no=data.get("substatusNo"),
            substatus_name=data.get("substatusName"),
            collected=data.get("collected", False),
            product_no=data.get("productNo"),
            product_name=data.get("productName"),
            customer_no=data.get("customerNo", 0),
            customer_user_id=data.get("customerUserId"),
            carrier_no=data.get("carrierNo"),
            carrier_user_id=data.get("carrierUserId"),
            branch_no=data.get("branchNo", 0),
            vehicle_type_no=data.get("vehicleTypeNo"),
            vehicle_type_name=data.get("vehicleTypeName"),
            fleet_no=data.get("fleetNo"),
            user_id=data.get("userId"),
            waybill_notes=data.get("waybillNotes", ""),
            invoice_notes=data.get("invoiceNotes", ""),
            purchase_invoice_notes=data.get("purchaseInvoiceNotes"),
            internal_notes=data.get("internalNotes"),
            carrier_notes=data.get("carrierNotes"),
            recipient_email=data.get("recipientEmail"),
            distance=data.get("distance"),
            order_price=data.get("orderPrice"),
            order_purchase_price=data.get("orderPurchasePrice"),
            prepaid_amount=data.get("prepaidAmount"),
            ready_for_purchase_invoice=data.get("readyForPurchaseInvoice"),
            username_created=data.get("usernameCreated"),
            username_assigned=data.get("usernameAssigned"),
            invoice_id=data.get("invoiceId", 0),
            tracking_id=data.get("trackingId"),
            external_id=data.get("externalId"),
            is_deleted=data.get("isDeleted"),
            destinations=[
                RestDestination.from_dict(d) for d in (data.get("destinations") or [])
            ],
            goods=[
                RestGoodsLine.from_dict(g) for g in (data.get("goods") or [])
            ],
            customer=(
                RestCustomer.from_dict(data["customer"])
                if data.get("customer")
                else None
            ),
            carrier=(
                RestCarrier.from_dict(data["carrier"])
                if data.get("carrier")
                else None
            ),
            sales_rates=[
                RestRate.from_dict(r) for r in (data.get("salesRates") or [])
            ],
            purchase_rates=[
                RestRate.from_dict(r) for r in (data.get("purchaseRates") or [])
            ],
            track_history=[
                RestTrackHistoryEntry.from_dict(t)
                for t in (data.get("trackHistory") or [])
            ],
        )


@dataclass
class RestOrder:
    """
    Transport order returned by the REST API.

    Use ``attributes`` to access all order data fields.
    Use the client's ``update_order()`` method to modify an order.
    """

    id: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    attributes: RestOrderAttributes = field(
        default_factory=RestOrderAttributes
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestOrder":
        return cls(
            id=data.get("id", 0),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            attributes=RestOrderAttributes.from_dict(data.get("attributes") or {}),
        )


# ---------------------------------------------------------------------------
# Reference data models
# ---------------------------------------------------------------------------

@dataclass
class RestProduct:
    """A transport product (service) available in EasyTrans."""

    id: int = 0
    product_no: int = 0
    name: str = ""
    is_deleted: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestProduct":
        attrs = data.get("attributes") or {}
        return cls(
            id=data.get("id", 0),
            product_no=attrs.get("productNo", 0),
            name=attrs.get("name", attrs.get("productName", "")),
            is_deleted=attrs.get("isDeleted"),
        )


@dataclass
class RestSubstatus:
    """An order substatus (fine-grained status label)."""

    id: int = 0
    substatus_no: int = 0
    name: str = ""
    is_deleted: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestSubstatus":
        attrs = data.get("attributes") or {}
        return cls(
            id=data.get("id", 0),
            substatus_no=attrs.get("substatusNo", 0),
            name=attrs.get("name", attrs.get("substatusName", "")),
            is_deleted=attrs.get("isDeleted"),
        )


@dataclass
class RestPackageType:
    """
    A package / rate type.

    Package types describe the kind of goods being transported and are
    also used as rate types to calculate shipping prices.
    """

    id: int = 0
    package_type_no: int = 0
    name: str = ""
    is_deleted: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestPackageType":
        attrs = data.get("attributes") or {}
        return cls(
            id=data.get("id", 0),
            package_type_no=attrs.get("packageTypeNo", 0),
            name=attrs.get("name", attrs.get("packageTypeName", "")),
            is_deleted=attrs.get("isDeleted"),
        )


@dataclass
class RestVehicleType:
    """A vehicle type (van, truck, etc.) available in EasyTrans."""

    id: int = 0
    vehicle_type_no: int = 0
    name: str = ""
    is_deleted: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestVehicleType":
        attrs = data.get("attributes") or {}
        return cls(
            id=data.get("id", 0),
            vehicle_type_no=attrs.get("vehicleTypeNo", 0),
            name=attrs.get("name", attrs.get("vehicleTypeName", "")),
            is_deleted=attrs.get("isDeleted"),
        )


@dataclass
class RestFleetVehicle:
    """
    A vehicle from the branch's own fleet.

    Branch accounts only — not accessible with customer accounts.
    """

    id: int = 0
    fleet_no: int = 0
    name: str = ""
    license_plate: str = ""
    vehicle_type_no: Optional[int] = None
    active: bool = True
    is_deleted: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestFleetVehicle":
        attrs = data.get("attributes") or {}
        return cls(
            id=data.get("id", 0),
            fleet_no=attrs.get("fleetNo", 0),
            name=attrs.get("name", ""),
            license_plate=attrs.get("licensePlate", attrs.get("registration", "")),
            vehicle_type_no=attrs.get("vehicleTypeNo"),
            active=attrs.get("active", True),
            is_deleted=attrs.get("isDeleted"),
        )


# ---------------------------------------------------------------------------
# Invoice model
# ---------------------------------------------------------------------------

@dataclass
class RestInvoice:
    """
    A sales invoice returned by the REST API.

    ``invoice_pdf`` is a base64-encoded PDF string present only when the
    request was made with ``include_invoice_pdf=True``.
    """

    id: int = 0
    invoice_id: int = 0
    invoice_no: str = ""
    invoice_date: Optional[str] = None
    customer_no: int = 0
    total_amount: Optional[str] = None
    vat_amount: Optional[str] = None
    payment_method: Optional[str] = None       # branch only
    online_payment_status: Optional[str] = None  # branch only
    discount_percentage: Optional[float] = None  # branch only
    sent_date: Optional[str] = None            # branch only
    paid: Optional[bool] = None                # branch only
    paid_date: Optional[str] = None            # branch only
    exported: Optional[bool] = None            # branch only
    external_id: Optional[str] = None          # branch only
    invoice_pdf: Optional[str] = None          # base64 when include_invoice=True
    customer: Optional[RestCustomer] = None    # when include_customer=True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestInvoice":
        attrs = data.get("attributes") or data
        return cls(
            id=data.get("id", 0),
            invoice_id=attrs.get("invoiceId", 0),
            invoice_no=str(attrs.get("invoiceNo", "")),
            invoice_date=attrs.get("invoiceDate"),
            customer_no=attrs.get("customerNo", 0),
            total_amount=attrs.get("totalAmount", attrs.get("amountInclVat")),
            vat_amount=attrs.get("vatAmount", attrs.get("amountExclVat")),
            payment_method=attrs.get("paymentMethod"),
            online_payment_status=attrs.get("onlinePaymentStatus"),
            discount_percentage=attrs.get("discountPercentage"),
            sent_date=attrs.get("sentDate"),
            paid=attrs.get("paid"),
            paid_date=attrs.get("paidDate"),
            exported=attrs.get("exported"),
            external_id=attrs.get("externalId"),
            invoice_pdf=attrs.get("invoicePdf"),
            customer=(
                RestCustomer.from_dict(attrs["customer"])
                if attrs.get("customer")
                else None
            ),
        )


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

__all__ = [
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
]
