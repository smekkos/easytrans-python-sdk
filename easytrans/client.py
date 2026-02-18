"""
Main client for EasyTrans API communication.

The EasyTransClient handles all authentication, request building,
and error handling for both EasyTrans API surfaces:

JSON Import API (``import_json.php``)
    Used by ``import_orders()`` and ``import_customers()``.
    Authentication is embedded in the POST body.
    Response errors are signalled via HTTP 200 + an ``"error"`` key.

REST API (``/api/v1/``)
    Used by all ``get_*`` and ``update_*`` methods.
    Authentication uses HTTP Basic Auth (``Authorization: Basic``).
    Response errors are signalled via standard HTTP 4xx status codes.

Both surfaces share the same four constructor arguments — users never
need to know which backing API is called.
"""

import base64
import json
from typing import Any, Dict, Iterator, List, Optional, Union

import requests

from easytrans.models import (
    Customer,
    CustomerResult,
    Order,
    OrderResult,
    WebhookPayload,
)
from easytrans.rest_models import (
    PagedResponse,
    RestCarrier,
    RestCustomer,
    RestFleetVehicle,
    RestInvoice,
    RestOrder,
    RestPackageType,
    RestProduct,
    RestSubstatus,
    RestVehicleType,
)
from easytrans.exceptions import (
    EasyTransAPIError,
    EasyTransAuthError,
    EasyTransCustomerError,
    EasyTransDestinationError,
    EasyTransNotFoundError,
    EasyTransOrderError,
    EasyTransPackageError,
    EasyTransRateLimitError,
    EasyTransValidationError,
)
from easytrans.constants import AuthType, Mode


class EasyTransClient:
    """
    Unified client for the EasyTrans TMS API.

    Covers both the JSON import API and the REST API behind a single,
    consistent interface. Construct once and use all methods freely.

    Example::

        client = EasyTransClient(
            server_url="mytrans.nl",
            environment_name="production",
            username="user",
            password="secret",
        )

        # --- JSON import (create) ---
        result = client.import_orders([order], mode="effect")
        order_no = result.new_ordernos[0]

        # --- REST (read) ---
        order = client.get_order(order_no, include_track_history=True)
        print(order.attributes.status)          # "planned"
        print(order.attributes.tracking_id)     # "GIYDAMJNGM2TKNJY"
    """

    def __init__(
        self,
        server_url: str,
        environment_name: str,
        username: str,
        password: str,
        default_mode: str = "test",
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        Initialise the EasyTrans client.

        Args:
            server_url: Base server hostname without protocol
                        (e.g. ``"mytrans.nl"``, ``"mytransport.co.uk"``).
            environment_name: Path segment identifying the EasyTrans
                              environment (e.g. ``"demo"``, ``"production"``).
            username: API username (same credential used in the portal).
            password: API password.
            default_mode: Default mode for JSON import calls.
                          ``"test"`` validates without saving;
                          ``"effect"`` saves to the database (default: ``"test"``).
            timeout: HTTP request timeout in seconds (default: 30).
            verify_ssl: Verify SSL certificates (default: True).

        Note:
            JSON import URL: ``https://{server_url}/{environment_name}/import_json.php``
            REST API URL:    ``https://{server_url}/{environment_name}/api/v1``
        """
        # ── JSON Import API ──────────────────────────────────────────────────
        self.base_url = f"https://{server_url}/{environment_name}/import_json.php"
        self.username = username
        self.password = password
        self.default_mode = default_mode
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.verify = verify_ssl

        # ── REST API ─────────────────────────────────────────────────────────
        self._rest_base_url = f"https://{server_url}/{environment_name}/api/v1"

        _creds = base64.b64encode(
            f"{username}:{password}".encode()
        ).decode()

        self._rest_session = requests.Session()
        self._rest_session.headers.update(
            {
                "Authorization": f"Basic {_creds}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        self._rest_session.verify = verify_ssl

    # =========================================================================
    # JSON Import — private helpers
    # =========================================================================

    def _build_auth_payload(
        self,
        auth_type: str,
        mode: Optional[str] = None,
        return_rates: bool = False,
        return_documents: str = "",
        version: int = 2,
    ) -> Dict[str, Any]:
        """Build the authentication object for a JSON import request."""
        auth: Dict[str, Any] = {
            "username": self.username,
            "password": self.password,
            "type": auth_type,
            "mode": mode if mode is not None else self.default_mode,
            "version": version,
        }
        if return_rates:
            auth["return_rates"] = True
        if return_documents:
            auth["return_documents"] = return_documents
        return auth

    def _make_request(
        self,
        auth_type: str,
        data: Dict[str, Any],
        mode: Optional[str] = None,
        return_rates: bool = False,
        return_documents: str = "",
        version: int = 2,
    ) -> Dict[str, Any]:
        """
        Make an authenticated POST request to the JSON import API.

        EasyTrans returns HTTP 200 even for errors; errors are signalled
        by an ``"error"`` key in the response body.
        """
        auth = self._build_auth_payload(
            auth_type=auth_type,
            mode=mode,
            return_rates=return_rates,
            return_documents=return_documents,
            version=version,
        )
        payload = {"authentication": auth, **data}

        try:
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise EasyTransAPIError(
                f"Request timeout after {self.timeout}s: {exc}"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise EasyTransAPIError(f"Connection error: {exc}") from exc
        except requests.exceptions.HTTPError as exc:
            raise EasyTransAPIError(
                f"HTTP error {response.status_code}: {exc}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise EasyTransAPIError(f"Request failed: {exc}") from exc

        try:
            result = response.json()
        except ValueError as exc:
            raise EasyTransAPIError(
                f"Invalid JSON response from API: {exc}\n"
                f"Response: {response.text[:200]}"
            ) from exc

        if "error" in result:
            self._handle_error(result["error"])

        return result.get("result", result)

    def _handle_error(self, error_data: Dict[str, Any]) -> None:
        """Map JSON import API error codes to appropriate exception types."""
        errorno = error_data.get("errorno", 0)
        description = error_data.get("error_description", "Unknown error")
        message = f"[Error {errorno}] {description}"

        if errorno == 5:
            raise EasyTransValidationError(message)
        elif errorno in range(10, 20):
            raise EasyTransAuthError(message)
        elif errorno in range(20, 30) or errorno in (210, 211, 213, 214, 215):
            raise EasyTransOrderError(message)
        elif errorno in range(30, 40) or errorno == 310:
            raise EasyTransDestinationError(message)
        elif errorno in range(40, 46):
            raise EasyTransPackageError(message)
        elif errorno in range(50, 66):
            raise EasyTransCustomerError(message)
        else:
            raise EasyTransValidationError(message)

    # =========================================================================
    # JSON Import — public methods
    # =========================================================================

    def import_orders(
        self,
        orders: List[Order],
        mode: Optional[str] = None,
        return_rates: bool = False,
        return_documents: str = "",
    ) -> OrderResult:
        """
        Import one or more orders to EasyTrans.

        Args:
            orders: List of ``Order`` objects to import.
            mode: Override default mode (``"test"`` or ``"effect"``).
                  ``"test"`` validates only; ``"effect"`` creates the orders.
            return_rates: Request rate calculation in the response.
            return_documents: Document type to return
                              (e.g. ``"label10x15"``, ``"delivery_note"``).

        Returns:
            ``OrderResult`` with created order numbers and tracking info.

        Raises:
            ``EasyTransAuthError``: Authentication failed.
            ``EasyTransOrderError``: Order validation failed.
            ``EasyTransDestinationError``: Destination validation failed.
            ``EasyTransPackageError``: Package validation failed.
            ``EasyTransAPIError``: HTTP/network error.

        Example::

            result = client.import_orders([order], mode="effect")
            print(f"Created order {result.new_ordernos[0]}")
        """
        orders_data = [order.to_dict() for order in orders]
        response = self._make_request(
            auth_type=AuthType.ORDER_IMPORT.value,
            data={"orders": orders_data},
            mode=mode,
            return_rates=return_rates,
            return_documents=return_documents,
        )
        return OrderResult.from_dict(response)

    def import_customers(
        self,
        customers: List[Customer],
        mode: Optional[str] = None,
    ) -> CustomerResult:
        """
        Import one or more customers to EasyTrans.

        Args:
            customers: List of ``Customer`` objects to import.
            mode: Override default mode (``"test"`` or ``"effect"``).

        Returns:
            ``CustomerResult`` with created customer numbers and user IDs.

        Raises:
            ``EasyTransAuthError``: Authentication failed.
            ``EasyTransCustomerError``: Customer validation failed.
            ``EasyTransAPIError``: HTTP/network error.
        """
        customers_data = [customer.to_dict() for customer in customers]
        response = self._make_request(
            auth_type=AuthType.CUSTOMER_IMPORT.value,
            data={"customers": customers_data},
            mode=mode,
        )
        return CustomerResult.from_dict(response)

    @staticmethod
    def parse_webhook(
        payload: Union[str, bytes, Dict[str, Any]],
        expected_api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> WebhookPayload:
        """
        Parse and validate a webhook payload from EasyTrans.

        Webhooks are sent when order status changes (collected, finished, …).
        They include status updates, delivery times, signatures, and GPS coordinates.

        Args:
            payload: JSON string, bytes, or dict from the webhook request body.
            expected_api_key: Optional API key for validation (UUID).
            headers: Optional HTTP headers dict for API key verification.

        Returns:
            ``WebhookPayload`` object with order status information.

        Raises:
            ``EasyTransAuthError``: API key validation failed.
            ``EasyTransValidationError``: Invalid JSON or missing required fields.

        Security:
            Always validate the ``X-API-Key`` header to ensure the webhook
            comes from EasyTrans. The API key is a fixed UUID per environment.
        """
        if expected_api_key and headers:
            api_key = headers.get("X-API-Key") or headers.get("x-api-key")
            if api_key != expected_api_key:
                raise EasyTransAuthError(
                    f"Invalid webhook API key. Expected key starting with "
                    f"{expected_api_key[:8]}..., "
                    f"got {api_key[:8] if api_key else 'None'}..."
                )

        if isinstance(payload, (str, bytes)):
            try:
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                payload = json.loads(payload)
            except (ValueError, UnicodeDecodeError) as exc:
                raise EasyTransValidationError(
                    f"Invalid JSON in webhook payload: {exc}"
                ) from exc

        if not isinstance(payload, dict):
            raise EasyTransValidationError(
                "Webhook payload must be a JSON object"
            )

        required_fields = ["companyId", "eventTime", "order"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise EasyTransValidationError(
                f"Webhook payload missing required fields: {', '.join(missing)}"
            )

        try:
            return WebhookPayload.from_dict(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise EasyTransValidationError(
                f"Invalid webhook payload structure: {exc}"
            ) from exc

    # =========================================================================
    # REST API — private helpers
    # =========================================================================

    def _build_rest_params(
        self,
        filter: Optional[Dict[str, Any]] = None,  # noqa: A002
        sort: Optional[str] = None,
        page: Optional[int] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """
        Build a flat query-parameter dict for a REST list request.

        The ``filter`` dict supports two forms:

        * Simple: ``{"status": "planned"}``
          → ``filter[status]=planned``
        * Operator: ``{"date": {"gte": "2024-01-01"}}``
          → ``filter[date][gte]=2024-01-01``

        Args:
            filter: Optional nested filter dict.
            sort: Optional sort string (e.g. ``"-orderNo,date"``).
            page: Optional page number.
            **extra: Additional top-level query parameters
                     (e.g. ``include_customer=True``).

        Returns:
            Flat dict ready to pass as ``params`` to :mod:`requests`.
        """
        params: Dict[str, Any] = {}

        if filter:
            for field, value in filter.items():
                if isinstance(value, dict):
                    for op, op_val in value.items():
                        params[f"filter[{field}][{op}]"] = op_val
                else:
                    params[f"filter[{field}]"] = value

        if sort is not None:
            params["sort"] = sort

        if page is not None:
            params["page"] = page

        for key, value in extra.items():
            if value is not None and value is not False:
                params[key] = value

        return params

    # Synthesised empty-list body returned when the server 404s on a list call.
    _EMPTY_LIST_RESPONSE: Dict[str, Any] = {
        "data": [],
        "links": {"first": None, "last": None, "prev": None, "next": None},
        "meta": {"current_page": 1, "last_page": 1, "per_page": 100, "total": 0},
    }

    def _make_rest_list_request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        GET a REST list endpoint; treat HTTP 404 as an empty result set.

        Some EasyTrans environments return 404 (rather than ``{"data": []}``
        ) when a list endpoint has zero records. This helper normalises that
        behaviour so all ``get_*s()`` methods always return a valid
        ``PagedResponse`` with an empty ``data`` list rather than raising
        ``EasyTransNotFoundError``.
        """
        try:
            return self._make_rest_request("GET", path, params=params)
        except EasyTransNotFoundError:
            return self._EMPTY_LIST_RESPONSE

    def _make_rest_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make an authenticated request to the REST API.

        Args:
            method: HTTP method, ``"GET"`` or ``"PUT"``.
            path: URL path relative to the REST base URL
                  (e.g. ``"/orders"`` or ``"/orders/35558"``).
            params: Optional query parameters.
            json_body: Optional JSON body (for PUT requests).

        Returns:
            Parsed JSON response (``dict`` or ``list``).

        Raises:
            ``EasyTransAuthError``: HTTP 401 — invalid credentials.
            ``EasyTransNotFoundError``: HTTP 404 — resource not found.
            ``EasyTransValidationError``: HTTP 422 — validation error.
            ``EasyTransRateLimitError``: HTTP 429 — rate limit exceeded.
            ``EasyTransAPIError``: Other HTTP or network errors.
        """
        url = f"{self._rest_base_url}{path}"
        request_kwargs: Dict[str, Any] = {"timeout": self.timeout}
        if params:
            request_kwargs["params"] = params
        if json_body is not None:
            request_kwargs["json"] = json_body

        try:
            if method == "GET":
                response = self._rest_session.get(url, **request_kwargs)
            elif method == "PUT":
                response = self._rest_session.put(url, **request_kwargs)
            else:
                raise EasyTransAPIError(f"Unsupported HTTP method: {method}")
        except requests.exceptions.Timeout as exc:
            raise EasyTransAPIError(
                f"REST request timeout after {self.timeout}s: {exc}"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise EasyTransAPIError(f"REST connection error: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise EasyTransAPIError(f"REST request failed: {exc}") from exc

        self._handle_rest_error(response)

        try:
            return response.json()
        except ValueError as exc:
            raise EasyTransAPIError(
                f"Invalid JSON in REST response: {exc}\n"
                f"Response: {response.text[:200]}"
            ) from exc

    def _handle_rest_error(self, response: requests.Response) -> None:
        """
        Raise the appropriate exception for a REST API 4xx/5xx response.

        Does nothing when the status code indicates success (2xx).
        """
        if response.ok:
            return

        status = response.status_code
        try:
            body = response.json()
            message = body.get("message", response.text[:200])
        except ValueError:
            message = response.text[:200]

        if status == 401:
            raise EasyTransAuthError(
                f"REST authentication failed (401): {message}"
            )
        if status == 404:
            raise EasyTransNotFoundError(
                f"REST resource not found (404): {message}"
            )
        if status == 422:
            errors = ""
            if isinstance(body, dict) and body.get("errors"):
                errors = "; ".join(
                    f"{k}: {', '.join(v)}"
                    for k, v in body["errors"].items()
                )
            raise EasyTransValidationError(
                f"REST validation error (422): {message}"
                + (f" — {errors}" if errors else "")
            )
        if status == 429:
            raise EasyTransRateLimitError(
                "REST rate limit exceeded (429): max 60 requests per minute. "
                "Back off and retry after a short delay."
            )
        raise EasyTransAPIError(
            f"REST API error (HTTP {status}): {message}"
        )

    def _iter_pages(
        self,
        path: str,
        params: Dict[str, Any],
        item_cls: Any,
    ) -> Iterator[Any]:
        """
        Yield every item across all pages by following ``links.next``.

        Args:
            path: Path relative to the REST base URL.
            params: Base query parameters (filters, includes, sort, …).
            item_cls: Dataclass with a ``from_dict`` class-method.

        Yields:
            Individual resource objects of type ``item_cls``.
        """
        while True:
            raw = self._make_rest_request("GET", path, params=params)
            for item in raw.get("data", []):
                yield item_cls.from_dict(item)

            next_url = (raw.get("links") or {}).get("next")
            if not next_url:
                break

            # Extract next page number from URL query string
            import urllib.parse as _up

            parsed = _up.urlparse(next_url)
            qs = _up.parse_qs(parsed.query)
            page_vals = qs.get("page", [None])
            if page_vals and page_vals[0]:
                params = {**params, "page": page_vals[0]}
            else:
                break

    # =========================================================================
    # REST API — Orders (branch and customer accounts)
    # =========================================================================

    def get_orders(
        self,
        *,
        filter: Optional[Dict[str, Any]] = None,  # noqa: A002
        sort: Optional[str] = None,
        include_customer: bool = False,
        include_carrier: bool = False,
        include_track_history: bool = False,
        include_sales_rates: bool = False,
        include_purchase_rates: bool = False,
        include_deleted: bool = False,
        page: Optional[int] = None,
    ) -> "PagedResponse[RestOrder]":
        """
        Return a paginated list of transport orders.

        Supports rich filtering and sorting. Results are paginated to
        100 orders per page; use ``page`` or ``has_next`` / ``links.next``
        to iterate over subsequent pages.

        Args:
            filter: Filter dict, e.g.::

                {"status": "planned"}
                {"date": {"gte": "2024-01-01"}}
                {"orderNo": {"gte": 1000, "lt": 2000}}

            sort: Sort expression, e.g. ``"status,-date"`` (the leading
                  dash reverses order).
            include_customer: Embed full customer record in each order.
            include_carrier: Embed full carrier record (branch only).
            include_track_history: Include Track & Trace history array.
            include_sales_rates: Include sales rate breakdown.
            include_purchase_rates: Include purchase rates (branch only).
            include_deleted: Include soft-deleted orders (branch only).
            page: Page number (1-based). Defaults to page 1.

        Returns:
            ``PagedResponse[RestOrder]`` with ``data``, ``links``, ``meta``,
            and a ``has_next`` convenience flag.

        Example::

            # All orders planned since 2024
            response = client.get_orders(
                filter={"date": {"gte": "2024-01-01"}, "status": "planned"},
                sort="-date",
                include_track_history=True,
            )
            for order in response.data:
                print(order.attributes.order_no, order.attributes.status)

            # Auto-paginate
            while True:
                for order in response.data:
                    process(order)
                if not response.has_next:
                    break
                response = client.get_orders(page=response.meta.current_page + 1)
        """
        params = self._build_rest_params(
            filter=filter,
            sort=sort,
            page=page,
            include_customer="true" if include_customer else None,
            include_carrier="true" if include_carrier else None,
            include_track_history="true" if include_track_history else None,
            include_sales_rates="true" if include_sales_rates else None,
            include_purchase_rates="true" if include_purchase_rates else None,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request("/orders", params=params or None)
        return PagedResponse.from_dict(raw, RestOrder)

    def get_order(
        self,
        order_no: int,
        *,
        include_customer: bool = False,
        include_carrier: bool = False,
        include_track_history: bool = False,
        include_sales_rates: bool = False,
        include_purchase_rates: bool = False,
        include_deleted: bool = False,
    ) -> RestOrder:
        """
        Return a single transport order by order number.

        Args:
            order_no: The EasyTrans order number.
            include_customer: Embed full customer record.
            include_carrier: Embed full carrier record (branch only).
            include_track_history: Include Track & Trace history.
            include_sales_rates: Include sales rate breakdown.
            include_purchase_rates: Include purchase rates (branch only).
            include_deleted: Return the order even if soft-deleted (branch only).

        Returns:
            ``RestOrder`` dataclass.

        Raises:
            ``EasyTransNotFoundError``: Order number does not exist.

        Example::

            order = client.get_order(35558, include_track_history=True)
            print(order.attributes.tracking_id)
        """
        params = self._build_rest_params(
            include_customer="true" if include_customer else None,
            include_carrier="true" if include_carrier else None,
            include_track_history="true" if include_track_history else None,
            include_sales_rates="true" if include_sales_rates else None,
            include_purchase_rates="true" if include_purchase_rates else None,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/orders/{order_no}", params=params or None
        )
        return RestOrder.from_dict(raw["data"])

    def update_order(
        self,
        order_no: int,
        *,
        carrier_no: Optional[int] = None,
        fleet_no: Optional[int] = None,
        waybill_notes: Optional[str] = None,
        invoice_notes: Optional[str] = None,
        purchase_invoice_notes: Optional[str] = None,
        internal_notes: Optional[str] = None,
        ready_for_purchase_invoice: Optional[bool] = None,
        external_id: Optional[str] = None,
        destinations: Optional[List[Dict[str, Any]]] = None,
        goods: Optional[List[Dict[str, Any]]] = None,
        sales_rates: Optional[List[Dict[str, Any]]] = None,
        purchase_rates: Optional[List[Dict[str, Any]]] = None,
    ) -> RestOrder:
        """
        Update an existing order (branch accounts only).

        Only the supplied keyword arguments are included in the request
        body; unspecified fields are left unchanged.

        To update a specific destination, include ``addressId`` or
        ``stopNo`` in the destination dict alongside the fields to change::

            destinations=[{"stopNo": 2, "date": "2024-12-31", "fromTime": "09:00"}]

        To update a goods line, include ``packageId`` or ``packageNo``::

            goods=[{"packageNo": 1, "amount": 20}]

        Supplying ``carrier_no=0`` removes the assigned carrier.

        Args:
            order_no: The EasyTrans order number to update.
            carrier_no: Assign (or remove) a carrier.
            fleet_no: Assign a fleet vehicle.
            waybill_notes: Replace the waybill notes.
            invoice_notes: Replace the invoice notes.
            purchase_invoice_notes: Replace the purchase invoice notes.
            internal_notes: Replace the internal notes.
            ready_for_purchase_invoice: Toggle purchase-invoice readiness.
            external_id: Update the external reference (max 50 chars).
            destinations: List of destination update dicts.
            goods: List of goods line update dicts.
            sales_rates: List of sales rate update dicts.
            purchase_rates: List of purchase rate update dicts.

        Returns:
            Updated ``RestOrder``.

        Raises:
            ``EasyTransNotFoundError``: Order does not exist.
            ``EasyTransValidationError``: Body failed server-side validation.
        """
        body: Dict[str, Any] = {}
        if carrier_no is not None:
            body["carrierNo"] = carrier_no
        if fleet_no is not None:
            body["fleetNo"] = fleet_no
        if waybill_notes is not None:
            body["waybillNotes"] = waybill_notes
        if invoice_notes is not None:
            body["invoiceNotes"] = invoice_notes
        if purchase_invoice_notes is not None:
            body["purchaseInvoiceNotes"] = purchase_invoice_notes
        if internal_notes is not None:
            body["internalNotes"] = internal_notes
        if ready_for_purchase_invoice is not None:
            body["readyForPurchaseInvoice"] = ready_for_purchase_invoice
        if external_id is not None:
            body["externalId"] = external_id
        if destinations is not None:
            body["destinations"] = destinations
        if goods is not None:
            body["goods"] = goods
        if sales_rates is not None:
            body["salesRates"] = sales_rates
        if purchase_rates is not None:
            body["purchaseRates"] = purchase_rates

        raw = self._make_rest_request(
            "PUT", f"/orders/{order_no}", json_body=body
        )
        return RestOrder.from_dict(raw["data"])

    # =========================================================================
    # REST API — Products
    # =========================================================================

    def get_products(
        self,
        *,
        filter_name: Optional[str] = None,
        include_deleted: bool = False,
    ) -> "PagedResponse[RestProduct]":
        """
        Return a list of transport products available in EasyTrans.

        Args:
            filter_name: Filter by (part of) the product name.
            include_deleted: Include soft-deleted products (branch only).

        Returns:
            ``PagedResponse[RestProduct]``.
        """
        params = self._build_rest_params(
            filter={"productName": filter_name} if filter_name else None,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request("/products", params=params or None)
        return PagedResponse.from_dict(raw, RestProduct)

    def get_product(
        self,
        product_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestProduct:
        """
        Return a single product by product number.

        Args:
            product_no: The product number.
            include_deleted: Return the product even if soft-deleted.

        Returns:
            ``RestProduct``.

        Raises:
            ``EasyTransNotFoundError``: Product does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/products/{product_no}", params=params or None
        )
        return RestProduct.from_dict(raw["data"])

    # =========================================================================
    # REST API — Substatuses
    # =========================================================================

    def get_substatuses(
        self,
        *,
        filter_name: Optional[str] = None,
        include_deleted: bool = False,
    ) -> "PagedResponse[RestSubstatus]":
        """
        Return a list of order substatuses.

        Args:
            filter_name: Filter by (part of) the substatus name.
            include_deleted: Include soft-deleted substatuses (branch only).

        Returns:
            ``PagedResponse[RestSubstatus]``.
        """
        params = self._build_rest_params(
            filter={"substatusName": filter_name} if filter_name else None,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request(
            "/substatuses", params=params or None
        )
        return PagedResponse.from_dict(raw, RestSubstatus)

    def get_substatus(
        self,
        substatus_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestSubstatus:
        """
        Return a single substatus by substatus number.

        Args:
            substatus_no: The substatus number.
            include_deleted: Return the substatus even if soft-deleted.

        Returns:
            ``RestSubstatus``.

        Raises:
            ``EasyTransNotFoundError``: Substatus does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/substatuses/{substatus_no}", params=params or None
        )
        return RestSubstatus.from_dict(raw["data"])

    # =========================================================================
    # REST API — Package types
    # =========================================================================

    def get_package_types(
        self,
        *,
        filter_name: Optional[str] = None,
        include_deleted: bool = False,
    ) -> "PagedResponse[RestPackageType]":
        """
        Return a list of package / rate types.

        Package types describe the kind of goods and are also used as
        rate types to calculate shipping prices.

        Args:
            filter_name: Filter by (part of) the package type name.
            include_deleted: Include soft-deleted package types (branch only).

        Returns:
            ``PagedResponse[RestPackageType]``.
        """
        params = self._build_rest_params(
            filter={"packageTypeName": filter_name} if filter_name else None,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request(
            "/packagetypes", params=params or None
        )
        return PagedResponse.from_dict(raw, RestPackageType)

    def get_package_type(
        self,
        package_type_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestPackageType:
        """
        Return a single package type by package type number.

        Args:
            package_type_no: The package type number.
            include_deleted: Return the package type even if soft-deleted.

        Returns:
            ``RestPackageType``.

        Raises:
            ``EasyTransNotFoundError``: Package type does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/packagetypes/{package_type_no}", params=params or None
        )
        return RestPackageType.from_dict(raw["data"])

    # =========================================================================
    # REST API — Vehicle types
    # =========================================================================

    def get_vehicle_types(
        self,
        *,
        filter_name: Optional[str] = None,
        include_deleted: bool = False,
    ) -> "PagedResponse[RestVehicleType]":
        """
        Return a list of vehicle types.

        Args:
            filter_name: Filter by (part of) the vehicle type name.
            include_deleted: Include soft-deleted vehicle types (branch only).

        Returns:
            ``PagedResponse[RestVehicleType]``.
        """
        params = self._build_rest_params(
            filter={"vehicleTypeName": filter_name} if filter_name else None,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request(
            "/vehicletypes", params=params or None
        )
        return PagedResponse.from_dict(raw, RestVehicleType)

    def get_vehicle_type(
        self,
        vehicle_type_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestVehicleType:
        """
        Return a single vehicle type by vehicle type number.

        Args:
            vehicle_type_no: The vehicle type number.
            include_deleted: Return the vehicle type even if soft-deleted.

        Returns:
            ``RestVehicleType``.

        Raises:
            ``EasyTransNotFoundError``: Vehicle type does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/vehicletypes/{vehicle_type_no}", params=params or None
        )
        return RestVehicleType.from_dict(raw["data"])

    # =========================================================================
    # REST API — Customers (branch accounts only)
    # =========================================================================

    def get_customers(
        self,
        *,
        filter: Optional[Dict[str, Any]] = None,  # noqa: A002
        sort: Optional[str] = None,
        include_deleted: bool = False,
        page: Optional[int] = None,
    ) -> "PagedResponse[RestCustomer]":
        """
        Return a paginated list of customers (branch accounts only).

        Args:
            filter: Filter dict. Supported fields include ``customerNo``,
                    ``companyName``, ``createdAt``, ``updatedAt``,
                    ``debtorNo``, ``vatNo``, ``externalId``, and nested
                    address / contact fields.
            sort: Sort expression, e.g. ``"companyName,-createdAt"``.
            include_deleted: Include soft-deleted customers.
            page: Page number (1-based).

        Returns:
            ``PagedResponse[RestCustomer]``.
        """
        params = self._build_rest_params(
            filter=filter,
            sort=sort,
            page=page,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request(
            "/customers", params=params or None
        )
        return PagedResponse.from_dict(raw, RestCustomer)

    def get_customer(
        self,
        customer_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestCustomer:
        """
        Return a single customer by customer number (branch accounts only).

        Args:
            customer_no: The EasyTrans customer number.
            include_deleted: Return the customer even if soft-deleted.

        Returns:
            ``RestCustomer``.

        Raises:
            ``EasyTransNotFoundError``: Customer does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/customers/{customer_no}", params=params or None
        )
        return RestCustomer.from_dict(raw["data"])

    # =========================================================================
    # REST API — Carriers (branch accounts only)
    # =========================================================================

    def get_carriers(
        self,
        *,
        filter: Optional[Dict[str, Any]] = None,  # noqa: A002
        sort: Optional[str] = None,
        include_deleted: bool = False,
        page: Optional[int] = None,
    ) -> "PagedResponse[RestCarrier]":
        """
        Return a paginated list of carriers (branch accounts only).

        Args:
            filter: Filter dict. Supported fields include ``carrierNo``,
                    ``name``, ``createdAt``, ``updatedAt``,
                    ``creditorNo``, ``externalId``, and nested address /
                    contact fields.
            sort: Sort expression, e.g. ``"name,-createdAt"``.
            include_deleted: Include soft-deleted carriers.
            page: Page number (1-based).

        Returns:
            ``PagedResponse[RestCarrier]``.
        """
        params = self._build_rest_params(
            filter=filter,
            sort=sort,
            page=page,
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request(
            "/carriers", params=params or None
        )
        return PagedResponse.from_dict(raw, RestCarrier)

    def get_carrier(
        self,
        carrier_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestCarrier:
        """
        Return a single carrier by carrier number (branch accounts only).

        Args:
            carrier_no: The EasyTrans carrier number.
            include_deleted: Return the carrier even if soft-deleted.

        Returns:
            ``RestCarrier``.

        Raises:
            ``EasyTransNotFoundError``: Carrier does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/carriers/{carrier_no}", params=params or None
        )
        return RestCarrier.from_dict(raw["data"])

    # =========================================================================
    # REST API — Fleet (branch accounts only)
    # =========================================================================

    def get_fleet(
        self,
        *,
        filter_registration: Optional[str] = None,
        include_deleted: bool = False,
    ) -> "PagedResponse[RestFleetVehicle]":
        """
        Return a list of vehicles from the branch fleet.

        Args:
            filter_registration: Filter by (part of) the license plate.
            include_deleted: Include soft-deleted vehicles.

        Returns:
            ``PagedResponse[RestFleetVehicle]``.
        """
        params = self._build_rest_params(
            filter=(
                {"registration": filter_registration}
                if filter_registration
                else None
            ),
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_list_request("/fleet", params=params or None)
        return PagedResponse.from_dict(raw, RestFleetVehicle)

    def get_fleet_vehicle(
        self,
        fleet_no: int,
        *,
        include_deleted: bool = False,
    ) -> RestFleetVehicle:
        """
        Return a single fleet vehicle by fleet number.

        Args:
            fleet_no: The EasyTrans fleet number.
            include_deleted: Return the vehicle even if soft-deleted.

        Returns:
            ``RestFleetVehicle``.

        Raises:
            ``EasyTransNotFoundError``: Fleet vehicle does not exist.
        """
        params = self._build_rest_params(
            include_deleted="true" if include_deleted else None,
        )
        raw = self._make_rest_request(
            "GET", f"/fleet/{fleet_no}", params=params or None
        )
        return RestFleetVehicle.from_dict(raw["data"])

    # =========================================================================
    # REST API — Invoices
    # =========================================================================

    def get_invoices(
        self,
        *,
        filter: Optional[Dict[str, Any]] = None,  # noqa: A002
        include_customer: bool = False,
        include_invoice_pdf: bool = False,
        page: Optional[int] = None,
    ) -> "PagedResponse[RestInvoice]":
        """
        Return a paginated list of invoices.

        Args:
            filter: Filter dict. Supported fields include ``invoiceId``,
                    ``invoiceNo``, ``invoiceNoPrefix``, ``customerNo``,
                    ``invoiceDate`` (supports operator dicts such as
                    ``{"gte": "2024-01-01"}``).
            include_customer: Embed full customer record in each invoice.
            include_invoice_pdf: Embed base64-encoded PDF in each invoice.
                                 Note: substantially increases response size.
            page: Page number (1-based).

        Returns:
            ``PagedResponse[RestInvoice]``.

        Example::

            invoices = client.get_invoices(
                filter={"invoiceDate": {"gte": "2024-01-01"}},
                include_invoice_pdf=True,
            )
            for inv in invoices.data:
                save_pdf(inv.invoice_no, inv.invoice_pdf)
        """
        params = self._build_rest_params(
            filter=filter,
            page=page,
            include_customer="true" if include_customer else None,
            include_invoice="true" if include_invoice_pdf else None,
        )
        raw = self._make_rest_list_request("/invoices", params=params or None)
        return PagedResponse.from_dict(raw, RestInvoice)

    def get_invoice(
        self,
        invoice_id: int,
        *,
        include_customer: bool = False,
        include_invoice_pdf: bool = False,
    ) -> RestInvoice:
        """
        Return a single invoice by its internal invoice ID.

        Args:
            invoice_id: The internal EasyTrans invoice ID (not the
                        human-readable invoice number).
            include_customer: Embed full customer record.
            include_invoice_pdf: Embed base64-encoded PDF.

        Returns:
            ``RestInvoice``.

        Raises:
            ``EasyTransNotFoundError``: Invoice does not exist.
        """
        params = self._build_rest_params(
            include_customer="true" if include_customer else None,
            include_invoice="true" if include_invoice_pdf else None,
        )
        raw = self._make_rest_request(
            "GET", f"/invoices/{invoice_id}", params=params or None
        )
        return RestInvoice.from_dict(raw["data"])

    # =========================================================================
    # Session lifecycle
    # =========================================================================

    def close(self) -> None:
        """Close both HTTP sessions and release all connections."""
        self.session.close()
        self._rest_session.close()

    def __enter__(self) -> "EasyTransClient":
        """Context manager entry — returns ``self``."""
        return self

    def __exit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> bool:
        """Context manager exit — closes both sessions."""
        self.close()
        return False
