"""
Main client for EasyTrans API communication.

The EasyTransClient handles all authentication, request building,
and error handling for the EasyTrans TMS API.
"""

import json
from typing import Dict, List, Optional, Any, Union
import requests

from easytrans.models import (
    Order,
    Customer,
    OrderResult,
    CustomerResult,
    WebhookPayload,
)
from easytrans.exceptions import (
    EasyTransAPIError,
    EasyTransAuthError,
    EasyTransValidationError,
    EasyTransOrderError,
    EasyTransDestinationError,
    EasyTransPackageError,
    EasyTransCustomerError,
)
from easytrans.constants import AuthType, Mode


class EasyTransClient:
    """
    Main client for EasyTrans API.
    
    This client handles order and customer imports with automatic
    authentication, error handling, and response parsing.
    
    Important: EasyTrans does NOT use HTTP Basic Auth. Instead,
    authentication credentials are embedded in the JSON POST body.
    
    Example:
        >>> client = EasyTransClient(
        ...     server_url="mytrans.nl",
        ...     environment_name="production",
        ...     username="user1234",
        ...     password="secret"
        ... )
        >>> 
        >>> order = Order(
        ...     productno=2,
        ...     order_destinations=[...]
        ... )
        >>> 
        >>> result = client.import_orders([order], mode="effect")
        >>> print(f"Created order {result.new_ordernos[0]}")
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
        Initialize EasyTrans client.
        
        Args:
            server_url: Base server URL without protocol
                        (e.g., "mytrans.nl", "mytrans.be", "mytransport.co.uk")
            environment_name: Environment name (e.g., "demo", "production")
            username: API username (can be same as portal login)
            password: API password
            default_mode: Default mode "test" or "effect" (default: "test")
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Verify SSL certificates (default: True)
        
        Note:
            The API endpoint will be: https://{server_url}/{environment_name}/import_json.php
        """
        # Build endpoint URL
        self.base_url = f"https://{server_url}/{environment_name}/import_json.php"
        
        # Store credentials
        self.username = username
        self.password = password
        self.default_mode = default_mode
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.verify = verify_ssl

    def _build_auth_payload(
        self,
        auth_type: str,
        mode: Optional[str] = None,
        return_rates: bool = False,
        return_documents: str = "",
        version: int = 2,
    ) -> Dict[str, Any]:
        """
        Build authentication object for API request.
        
        Args:
            auth_type: Type of import (order_import, customer_import, etc.)
            mode: Override default mode
            return_rates: Request rate calculation in response
            return_documents: Document type to return
            version: API version (always use 2 for new implementations)
        
        Returns:
            Authentication dictionary
        """
        auth = {
            "username": self.username,
            "password": self.password,
            "type": auth_type,
            "mode": mode if mode is not None else self.default_mode,
            "version": version,
        }
        
        # Add optional fields only if specified
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
        Make authenticated request to EasyTrans API.
        
        This method:
        1. Builds authentication object
        2. Merges it with data payload
        3. Posts to API endpoint
        4. Parses response
        5. Handles errors
        
        Args:
            auth_type: Type of import
            data: Payload data (orders, customers, etc.)
            mode: Override default mode
            return_rates: Request rates
            return_documents: Request documents
            version: API version
        
        Returns:
            Parsed result dictionary
        
        Raises:
            EasyTransAPIError: HTTP/network errors
            EasyTransAuthError: Authentication failures
            EasyTransOrderError: Order validation errors
            EasyTransDestinationError: Destination validation errors
            EasyTransPackageError: Package validation errors
            EasyTransCustomerError: Customer validation errors
            EasyTransValidationError: Other validation errors
        """
        # Build authentication
        auth = self._build_auth_payload(
            auth_type=auth_type,
            mode=mode,
            return_rates=return_rates,
            return_documents=return_documents,
            version=version,
        )
        
        # Merge authentication with data
        # NOTE: Authentication is a SIBLING to orders/customers in the JSON body
        payload = {
            "authentication": auth,
            **data,
        }
        
        # Make HTTP request
        try:
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
        except requests.exceptions.Timeout as e:
            raise EasyTransAPIError(f"Request timeout after {self.timeout}s: {e}") from e
        
        except requests.exceptions.ConnectionError as e:
            raise EasyTransAPIError(f"Connection error: {e}") from e
        
        except requests.exceptions.HTTPError as e:
            raise EasyTransAPIError(f"HTTP error {response.status_code}: {e}") from e
        
        except requests.exceptions.RequestException as e:
            raise EasyTransAPIError(f"Request failed: {e}") from e
        
        # Parse JSON response
        try:
            result = response.json()
        except ValueError as e:
            raise EasyTransAPIError(
                f"Invalid JSON response from API: {e}\nResponse: {response.text[:200]}"
            ) from e
        
        # Check for API errors
        # NOTE: EasyTrans returns HTTP 200 even on errors!
        # Errors are indicated by an "error" key in the JSON response
        if "error" in result:
            self._handle_error(result["error"])
        
        # Return result object
        return result.get("result", result)

    def _handle_error(self, error_data: Dict[str, Any]) -> None:
        """
        Map API error codes to appropriate exception types.
        
        Args:
            error_data: Error object from API response
        
        Raises:
            Appropriate EasyTransError subclass based on error code
        """
        errorno = error_data.get("errorno", 0)
        description = error_data.get("error_description", "Unknown error")
        
        # Build error message with error number
        message = f"[Error {errorno}] {description}"
        
        # Map error codes to exception types
        # See documentation section 7.2 for complete error list
        
        # JSON parsing errors (5)
        if errorno == 5:
            raise EasyTransValidationError(message)
        
        # Authentication errors (10-19)
        elif errorno in (10, 11, 12, 13, 14, 15, 16, 17, 18, 19):
            raise EasyTransAuthError(message)
        
        # Order errors (20-29, plus 210-215)
        elif errorno in range(20, 30) or errorno in (210, 211, 213, 214, 215):
            raise EasyTransOrderError(message)
        
        # Destination errors (30-39, plus 310)
        elif errorno in range(30, 40) or errorno == 310:
            raise EasyTransDestinationError(message)
        
        # Package errors (40-45)
        elif errorno in range(40, 46):
            raise EasyTransPackageError(message)
        
        # Customer errors (50-65)
        elif errorno in range(50, 66):
            raise EasyTransCustomerError(message)
        
        # Generic validation error for unknown codes
        else:
            raise EasyTransValidationError(message)

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
            orders: List of Order objects to import
            mode: Override default mode ("test" or "effect")
                  - "test": Validate only, don't create orders
                  - "effect": Create orders in production
            return_rates: Request rate calculation in response
            return_documents: Document type to return in response
                             (e.g., "label10x15", "delivery_note")
        
        Returns:
            OrderResult with created order numbers and tracking info
        
        Raises:
            EasyTransAuthError: Authentication failed
            EasyTransOrderError: Order validation failed
            EasyTransDestinationError: Destination validation failed
            EasyTransPackageError: Package validation failed
            EasyTransAPIError: HTTP/network error
        
        Example:
            >>> from easytrans import EasyTransClient, Order, Destination
            >>> 
            >>> client = EasyTransClient(...)
            >>> order = Order(
            ...     productno=2,
            ...     date="2026-02-18",
            ...     order_destinations=[
            ...         Destination(company_name="Sender", ...),
            ...         Destination(company_name="Receiver", ...),
            ...     ]
            ... )
            >>> 
            >>> # Test first
            >>> result = client.import_orders([order], mode="test")
            >>> print(f"Validation passed: {result.total_orders} orders")
            >>> 
            >>> # Then submit
            >>> result = client.import_orders([order], mode="effect")
            >>> print(f"Created order: {result.new_ordernos[0]}")
        """
        # Convert Order objects to dictionaries
        orders_data = [order.to_dict() for order in orders]
        
        # Make API request
        response = self._make_request(
            auth_type=AuthType.ORDER_IMPORT.value,
            data={"orders": orders_data},
            mode=mode,
            return_rates=return_rates,
            return_documents=return_documents,
        )
        
        # Parse and return result
        return OrderResult.from_dict(response)

    def import_customers(
        self,
        customers: List[Customer],
        mode: Optional[str] = None,
    ) -> CustomerResult:
        """
        Import one or more customers to EasyTrans.
        
        Args:
            customers: List of Customer objects to import
            mode: Override default mode ("test" or "effect")
                  - "test": Validate only, don't create customers
                  - "effect": Create customers in production
        
        Returns:
            CustomerResult with created customer numbers and user IDs
        
        Raises:
            EasyTransAuthError: Authentication failed
            EasyTransCustomerError: Customer validation failed
            EasyTransAPIError: HTTP/network error
        
        Example:
            >>> from easytrans import EasyTransClient, Customer, CustomerContact
            >>> 
            >>> client = EasyTransClient(...)
            >>> customer = Customer(
            ...     company_name="Example Company",
            ...     address="Main Street",
            ...     houseno="123",
            ...     postal_code="1234AB",
            ...     city="Amsterdam",
            ...     country="NL",
            ...     customer_contacts=[
            ...         CustomerContact(
            ...             contact_name="John Doe",
            ...             email="john@example.com"
            ...         )
            ...     ]
            ... )
            >>> 
            >>> result = client.import_customers([customer], mode="effect")
            >>> print(f"Created customer: {result.new_customernos[0]}")
        """
        # Convert Customer objects to dictionaries
        customers_data = [customer.to_dict() for customer in customers]
        
        # Make API request
        response = self._make_request(
            auth_type=AuthType.CUSTOMER_IMPORT.value,
            data={"customers": customers_data},
            mode=mode,
        )
        
        # Parse and return result
        return CustomerResult.from_dict(response)

    @staticmethod
    def parse_webhook(
        payload: Union[str, bytes, Dict[str, Any]],
        expected_api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> WebhookPayload:
        """
        Parse and validate webhook payload from EasyTrans.
        
        Webhooks are sent when order status changes (collected, finished, etc.).
        They include status updates, delivery times, signatures, and GPS coordinates.
        
        Args:
            payload: JSON string, bytes, or dict from webhook request body
            expected_api_key: Optional API key for validation (UUID)
            headers: Optional HTTP headers dict for API key verification
        
        Returns:
            WebhookPayload object with order status information
        
        Raises:
            EasyTransAuthError: API key validation failed
            EasyTransValidationError: Invalid JSON or missing required fields
        
        Security:
            Always validate the X-API-Key header to ensure the webhook
            comes from EasyTrans. The API key is a fixed UUID per environment.
        
        Example:
            >>> # In Flask/Django view
            >>> @app.route('/easytrans/webhook', methods=['POST'])
            >>> def webhook_handler():
            ...     try:
            ...         webhook = EasyTransClient.parse_webhook(
            ...             payload=request.get_data(),
            ...             expected_api_key=settings.EASYTRANS_WEBHOOK_KEY,
            ...             headers=dict(request.headers)
            ...         )
            ...         
            ...         # Process webhook
            ...         order_id = webhook.order.externalId
            ...         status = webhook.order.status
            ...         
            ...         # Update database
            ...         update_order_status(order_id, status)
            ...         
            ...         return {"status": "ok"}, 200
            ...     
            ...     except EasyTransError as e:
            ...         return {"error": str(e)}, 400
        """
        # Validate API key if provided
        if expected_api_key and headers:
            api_key = headers.get("X-API-Key") or headers.get("x-api-key")
            if api_key != expected_api_key:
                raise EasyTransAuthError(
                    f"Invalid webhook API key. Expected key starting with "
                    f"{expected_api_key[:8]}..., got {api_key[:8] if api_key else 'None'}..."
                )
        
        # Parse JSON if string or bytes
        if isinstance(payload, (str, bytes)):
            try:
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                payload = json.loads(payload)
            except (ValueError, UnicodeDecodeError) as e:
                raise EasyTransValidationError(f"Invalid JSON in webhook payload: {e}") from e
        
        # Validate required fields
        if not isinstance(payload, dict):
            raise EasyTransValidationError("Webhook payload must be a JSON object")
        
        required_fields = ["companyId", "eventTime", "order"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise EasyTransValidationError(
                f"Webhook payload missing required fields: {', '.join(missing)}"
            )
        
        # Parse and return
        try:
            return WebhookPayload.from_dict(payload)
        except (KeyError, TypeError, ValueError) as e:
            raise EasyTransValidationError(f"Invalid webhook payload structure: {e}") from e

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
