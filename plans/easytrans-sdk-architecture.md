# EasyTrans Python SDK - Architecture Plan

## Executive Summary

This document outlines the architecture for a pure Python SDK to integrate Django projects with EasyTrans Software (Dutch TMS system). The SDK will be framework-agnostic, pip-installable, and provide strongly-typed models for JSON API communication.

## Project Structure

```
easytrans-python-sdk/
├── pyproject.toml              # Modern Python project configuration
├── README.md                   # Usage documentation and examples
├── LICENSE                     # MIT or similar
├── .gitignore                  # Python-specific ignores
│
├── easytrans/                  # Main package directory
│   ├── __init__.py            # Package exports
│   ├── client.py              # Main EasyTransClient class
│   ├── models.py              # Dataclass models for API entities
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── constants.py           # Enums and constants
│   └── utils.py               # Utility functions (optional)
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures and configuration
│   ├── test_client.py         # Client tests
│   ├── test_models.py         # Model serialization tests
│   ├── test_exceptions.py     # Exception mapping tests
│   └── fixtures/              # JSON fixture files
│       ├── responses/         # Mock API responses
│       │   ├── success_order.json
│       │   ├── success_customer.json
│       │   ├── error_auth.json
│       │   └── error_validation.json
│       └── requests/          # Sample request payloads
│
└── examples/                   # Usage examples
    ├── django_integration.py  # How to use in Django
    ├── basic_order.py         # Simple order creation
    └── webhook_handler.py     # Webhook consumption example
```

## Core Components

### 1. Exception Hierarchy (`exceptions.py`)

```python
# Base exception
EasyTransError(Exception)
    ├── EasyTransAPIError          # HTTP/network errors
    ├── EasyTransAuthError         # Authentication failures (errorno: 10-19)
    ├── EasyTransValidationError   # Data validation errors (errorno: 20-45, 50-65)
    ├── EasyTransOrderError        # Order-specific errors (errorno: 20-29)
    ├── EasyTransDestinationError  # Destination errors (errorno: 30-39)
    ├── EasyTransPackageError      # Package/goods errors (errorno: 40-45)
    └── EasyTransCustomerError     # Customer-specific errors (errorno: 50-65)
```

**Error Number Mapping** (from documentation):
- **5**: JSON parsing error
- **10-19**: Authentication errors
- **20-29**: Order errors
- **30-39**: Destination errors
- **40-45**: Package errors
- **50-65**: Customer errors

### 2. Data Models (`models.py`)

All models use Python dataclasses with:
- Type hints for all fields
- Optional fields with default values
- `to_dict()` method for JSON serialization
- Field validation in `__post_init__()` where needed

#### Core Models:

**Authentication Models:**
```python
@dataclass
class Authentication:
    username: str
    password: str
    type: str  # "order_import" | "customer_import"
    mode: str = "test"  # "test" | "effect"
    version: int = 2
    return_rates: bool = False
    return_documents: str = ""
```

**Order Models:**
```python
@dataclass
class Order:
    productno: int
    order_destinations: List[Destination]
    date: Optional[str] = None
    time: Optional[str] = None
    status: str = "submit"  # "save" | "submit" | "quote"
    customerno: Optional[int] = None
    carrierno: int = 0
    vehicleno: int = 0
    fleetno: Optional[int] = None
    substatusno: Optional[int] = None
    remark: str = ""
    remark_invoice: str = ""
    remark_internal: str = ""
    remark_purchase: str = ""
    no_confirmation_email: bool = False
    email_receiver: str = ""
    price: float = 0.0
    price_description: str = "Other costs"
    purchase_price: float = 0.0
    purchase_price_description: str = "Other costs"
    carrier_service: str = ""
    carrier_options: str = ""
    external_id: str = ""
    order_packages: List[Package] = field(default_factory=list)
```

**Destination Models:**
```python
@dataclass
class Document:
    type: str  # "pdf" | "xls" | "xlsx" | "doc" | "docx"
    base64_content: str
    name: str = ""

@dataclass
class Destination:
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
```

**Package Models:**
```python
@dataclass
class Package:
    amount: float = 0.0
    weight: float = 0.0
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    description: str = ""
    collect_destinationno: Optional[int] = None
    deliver_destinationno: Optional[int] = None
    ratetypeno: int = 0
```

**Customer Models:**
```python
@dataclass
class CustomerContact:
    contact_name: str = ""
    salutation: int = 0  # 0=Unknown, 1=Mr., 2=Mrs./Ms., 3=Attn.
    telephone: str = ""
    mobile: str = ""
    email: str = ""
    use_email_for_invoice: bool = True
    use_email_for_reminder: bool = True
    contact_remark: str = ""
    username: str = ""
    password: str = ""
    userid: Optional[int] = None

@dataclass
class Customer:
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
    # ... (all other fields from docs)
    customer_contacts: List[CustomerContact] = field(default_factory=list)
```

**Response Models:**
```python
@dataclass
class OrderTrackTrace:
    local_trackingnr: str
    local_tracktrace_url: str
    global_trackingnr: str
    global_tracktrace_url: str
    status: str

@dataclass
class OrderResult:
    mode: str
    total_orders: int
    total_order_destinations: int
    total_order_packages: int
    result_description: str
    new_ordernos: List[int]
    order_tracktrace: Dict[str, OrderTrackTrace]
    order_rates: Optional[Dict] = None
    order_documents: Optional[Dict] = None

@dataclass
class CustomerResult:
    mode: str
    total_customers: int
    total_customer_contacts: int
    result_description: str
    new_customernos: List[int]
    new_userids: Dict[int, List[int]]

@dataclass
class WebhookPayload:
    companyId: int
    eventTime: str
    order: Dict  # Partial order data with status updates
```

### 3. Main Client (`client.py`)

```python
class EasyTransClient:
    """Main client for EasyTrans API communication."""
    
    def __init__(
        self,
        server_url: str,
        environment_name: str,
        username: str,
        password: str,
        default_mode: str = "test",
        timeout: int = 30
    ):
        """
        Initialize EasyTrans client.
        
        Args:
            server_url: Base server URL (e.g., "mytrans.nl")
            environment_name: Environment name (e.g., "demo")
            username: API username
            password: API password
            default_mode: Default mode "test" or "effect"
            timeout: Request timeout in seconds
        """
        self.base_url = f"https://{server_url}/{environment_name}/import_json.php"
        self.username = username
        self.password = password
        self.default_mode = default_mode
        self.timeout = timeout
        self.session = requests.Session()
    
    def _make_request(
        self,
        auth_type: str,
        data: Dict,
        mode: Optional[str] = None,
        return_rates: bool = False,
        return_documents: str = "",
        version: int = 2
    ) -> Dict:
        """
        Make authenticated request to EasyTrans API.
        
        Handles authentication embedding and error parsing.
        """
        # Build authentication object
        auth = {
            "username": self.username,
            "password": self.password,
            "type": auth_type,
            "mode": mode or self.default_mode,
            "version": version,
            "return_rates": return_rates,
            "return_documents": return_documents
        }
        
        # Merge auth with payload
        payload = {"authentication": auth, **data}
        
        try:
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
        except requests.RequestException as e:
            raise EasyTransAPIError(f"HTTP request failed: {e}") from e
        
        # Parse JSON response
        try:
            result = response.json()
        except ValueError as e:
            raise EasyTransAPIError(f"Invalid JSON response: {e}") from e
        
        # Check for API errors
        if "error" in result:
            self._handle_error(result["error"])
        
        return result.get("result", result)
    
    def _handle_error(self, error_data: Dict) -> None:
        """
        Map error codes to appropriate exception types.
        
        Raises appropriate exception based on errorno.
        """
        errorno = error_data.get("errorno")
        description = error_data.get("error_description", "Unknown error")
        
        # Map error codes to exception types
        if errorno in (10, 11, 12, 13, 14, 15, 16, 17, 18, 19):
            raise EasyTransAuthError(f"[{errorno}] {description}")
        elif errorno in range(20, 30):
            raise EasyTransOrderError(f"[{errorno}] {description}")
        elif errorno in range(30, 40):
            raise EasyTransDestinationError(f"[{errorno}] {description}")
        elif errorno in range(40, 46):
            raise EasyTransPackageError(f"[{errorno}] {description}")
        elif errorno in range(50, 66):
            raise EasyTransCustomerError(f"[{errorno}] {description}")
        else:
            raise EasyTransValidationError(f"[{errorno}] {description}")
    
    def import_orders(
        self,
        orders: List[Order],
        mode: Optional[str] = None,
        return_rates: bool = False,
        return_documents: str = ""
    ) -> OrderResult:
        """
        Import one or more orders.
        
        Args:
            orders: List of Order objects to import
            mode: Override default mode ("test" or "effect")
            return_rates: Request rate calculation in response
            return_documents: Document type to return (e.g., "label10x15")
        
        Returns:
            OrderResult with created order numbers and tracking info
        
        Raises:
            EasyTransAuthError: Authentication failed
            EasyTransOrderError: Order validation failed
            EasyTransDestinationError: Destination validation failed
            EasyTransPackageError: Package validation failed
        """
        # Convert Order objects to dict
        orders_data = [order.to_dict() for order in orders]
        
        response = self._make_request(
            auth_type="order_import",
            data={"orders": orders_data},
            mode=mode,
            return_rates=return_rates,
            return_documents=return_documents
        )
        
        return OrderResult.from_dict(response)
    
    def import_customers(
        self,
        customers: List[Customer],
        mode: Optional[str] = None
    ) -> CustomerResult:
        """
        Import one or more customers.
        
        Args:
            customers: List of Customer objects to import
            mode: Override default mode ("test" or "effect")
        
        Returns:
            CustomerResult with created customer numbers
        
        Raises:
            EasyTransAuthError: Authentication failed
            EasyTransCustomerError: Customer validation failed
        """
        customers_data = [customer.to_dict() for customer in customers]
        
        response = self._make_request(
            auth_type="customer_import",
            data={"customers": customers_data},
            mode=mode
        )
        
        return CustomerResult.from_dict(response)
    
    @staticmethod
    def parse_webhook(
        payload: Union[str, Dict],
        expected_api_key: Optional[str] = None,
        headers: Optional[Dict] = None
    ) -> WebhookPayload:
        """
        Parse and validate webhook payload from EasyTrans.
        
        Args:
            payload: JSON string or dict from webhook
            expected_api_key: Optional API key for validation
            headers: Optional HTTP headers for API key verification
        
        Returns:
            WebhookPayload object
        
        Raises:
            EasyTransValidationError: Invalid webhook payload
            EasyTransAuthError: API key validation failed
        """
        # Validate API key if provided
        if expected_api_key and headers:
            api_key = headers.get("X-API-Key")
            if api_key != expected_api_key:
                raise EasyTransAuthError("Invalid webhook API key")
        
        # Parse JSON if string
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError as e:
                raise EasyTransValidationError(f"Invalid JSON: {e}")
        
        return WebhookPayload.from_dict(payload)
```

### 4. Constants (`constants.py`)

```python
from enum import Enum

class AuthType(str, Enum):
    ORDER_IMPORT = "order_import"
    CUSTOMER_IMPORT = "customer_import"
    PACKS_ORDER_IMPORT = "packs_order_import"
    GLS_ORDER_IMPORT = "gls_order_import"

class Mode(str, Enum):
    TEST = "test"
    EFFECT = "effect"

class OrderStatus(str, Enum):
    SAVE = "save"
    SUBMIT = "submit"
    QUOTE = "quote"

class CollectDeliver(int, Enum):
    PICKUP = 0
    DELIVERY = 1
    BOTH = 2

class Salutation(int, Enum):
    UNKNOWN = 0
    MR = 1
    MRS_MS = 2
    ATTN = 3

# ... more enums as needed
```

## Testing Strategy

### Test Organization

1. **Unit Tests** (`test_client.py`):
   - Authentication payload construction
   - Error parsing and exception mapping
   - Request/response serialization
   - All mocked with `responses` library

2. **Model Tests** (`test_models.py`):
   - Dataclass serialization (`to_dict()`)
   - Deserialization (`from_dict()`)
   - Field validation

3. **Integration Tests** (optional):
   - Real API calls in test mode
   - Requires credentials

### Key Test Scenarios

#### 1. Payload Construction Test
```python
def test_authentication_merged_with_payload(mock_responses):
    """Verify authentication is correctly merged into request body."""
    # Setup mock
    mock_responses.add(
        responses.POST,
        "https://mytrans.nl/demo/import_json.php",
        json={"result": {...}},
        status=200
    )
    
    client = EasyTransClient(...)
    client.import_orders([order])
    
    # Assert request body contains both auth and orders
    assert "authentication" in mock_responses.calls[0].request.body
    assert "orders" in mock_responses.calls[0].request.body
```

#### 2. Success Response Test
```python
def test_successful_order_import(mock_responses):
    """Test happy path order import."""
    mock_responses.add(
        responses.POST,
        "https://mytrans.nl/demo/import_json.php",
        json={
            "result": {
                "mode": "effect",
                "total_orders": 1,
                "new_ordernos": [29145],
                "order_tracktrace": {...}
            }
        }
    )
    
    result = client.import_orders([order])
    assert result.total_orders == 1
    assert 29145 in result.new_ordernos
```

#### 3. Error Mapping Test
```python
def test_auth_error_raises_correct_exception(mock_responses):
    """Verify errorno 12 raises EasyTransAuthError."""
    mock_responses.add(
        responses.POST,
        "https://mytrans.nl/demo/import_json.php",
        json={
            "error": {
                "errorno": 12,
                "error_description": "Login attempt failed"
            }
        }
    )
    
    with pytest.raises(EasyTransAuthError) as exc_info:
        client.import_orders([order])
    
    assert "12" in str(exc_info.value)
    assert "Login attempt failed" in str(exc_info.value)
```

### Fixtures (`conftest.py`)

```python
@pytest.fixture
def client():
    """Create test client instance."""
    return EasyTransClient(
        server_url="mytrans.nl",
        environment_name="demo",
        username="test_user",
        password="test_pass"
    )

@pytest.fixture
def sample_order():
    """Create sample order for testing."""
    return Order(
        productno=2,
        date="2026-01-01",
        order_destinations=[
            Destination(
                company_name="Test Company",
                address="Test Street",
                houseno="1",
                postal_code="1234AB",
                city="Amsterdam",
                collect_deliver=CollectDeliver.PICKUP
            ),
            Destination(
                company_name="Delivery Company",
                address="Other Street",
                houseno="2",
                postal_code="5678CD",
                city="Utrecht",
                collect_deliver=CollectDeliver.DELIVERY
            )
        ]
    )

@pytest.fixture
def success_response():
    """Load success response fixture."""
    with open("tests/fixtures/responses/success_order.json") as f:
        return json.load(f)
```

## Django Integration Pattern

```python
# settings.py
EASYTRANS = {
    "SERVER_URL": "mytrans.nl",
    "ENVIRONMENT": "production",
    "USERNAME": os.environ.get("EASYTRANS_USERNAME"),
    "PASSWORD": os.environ.get("EASYTRANS_PASSWORD"),
    "DEFAULT_MODE": "effect",
    "WEBHOOK_API_KEY": os.environ.get("EASYTRANS_WEBHOOK_KEY"),
}

# services.py
from easytrans import EasyTransClient, Order, Destination
from django.conf import settings

def get_easytrans_client():
    """Factory function to create configured client."""
    return EasyTransClient(
        server_url=settings.EASYTRANS["SERVER_URL"],
        environment_name=settings.EASYTRANS["ENVIRONMENT"],
        username=settings.EASYTRANS["USERNAME"],
        password=settings.EASYTRANS["PASSWORD"],
        default_mode=settings.EASYTRANS["DEFAULT_MODE"],
    )

def create_shipment(order_data):
    """Business logic for creating shipment."""
    client = get_easytrans_client()
    
    order = Order(
        productno=2,
        date=order_data["ship_date"],
        order_destinations=[...],
        external_id=str(order_data["id"])  # Reference Django model
    )
    
    result = client.import_orders([order], mode="effect")
    return result

# views.py (webhook handler)
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from easytrans import EasyTransClient

@csrf_exempt
def webhook_handler(request):
    """Handle EasyTrans status updates."""
    try:
        webhook = EasyTransClient.parse_webhook(
            payload=request.body,
            expected_api_key=settings.EASYTRANS["WEBHOOK_API_KEY"],
            headers=request.headers
        )
        
        # Process webhook
        # Update order status in database using webhook.order.externalId
        
        return JsonResponse({"status": "ok"}, status=200)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
```

## Dependencies (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "easytrans-sdk"
version = "1.0.0"
description = "Python SDK for EasyTrans TMS API"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
keywords = ["easytrans", "tms", "transport", "logistics", "api", "sdk"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "responses>=0.23.0",
    "black>=23.0",
    "mypy>=1.0",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/easytrans-python-sdk"
Documentation = "https://github.com/yourusername/easytrans-python-sdk#readme"
Repository = "https://github.com/yourusername/easytrans-python-sdk"
Issues = "https://github.com/yourusername/easytrans-python-sdk/issues"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --cov=easytrans --cov-report=html --cov-report=term"

[tool.black]
line-length = 100
target-version = ["py38", "py39", "py310", "py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Implementation Sequence

1. **Phase 1: Foundation**
   - Set up project structure and `pyproject.toml`
   - Implement exception hierarchy
   - Create constants/enums

2. **Phase 2: Models**
   - Implement all dataclasses with `to_dict()` and `from_dict()`
   - Add field validation
   - Write model tests

3. **Phase 3: Client**
   - Implement `EasyTransClient` core
   - Add `_make_request()` with auth merging
   - Implement error handling
   - Add `import_orders()` and `import_customers()`

4. **Phase 4: Testing**
   - Create pytest fixtures
   - Write comprehensive unit tests
   - Achieve >90% code coverage

5. **Phase 5: Documentation**
   - Write README with examples
   - Add docstrings to all public APIs
   - Create Django integration example

## Key Design Decisions

### 1. **Dataclasses over Pydantic**
- Lighter dependency footprint
- Standard library (Python 3.7+)
- Sufficient for this use case

### 2. **Explicit to_dict() Methods**
- Full control over JSON serialization
- Handle None vs missing fields
- Custom date formatting

### 3. **Session Reuse**
- Use `requests.Session` for connection pooling
- Better performance for multiple requests

### 4. **Type Hints Throughout**
- mypy compatibility
- Better IDE support
- Self-documenting code

### 5. **Framework-Agnostic**
- No Django/Flask dependencies
- Settings injection pattern
- Static methods for utilities

## Security Considerations

1. **Credentials**: Never hardcode, use environment variables
2. **Webhook Validation**: Always verify X-API-Key header
3. **HTTPS Only**: Enforce HTTPS in production
4. **Input Validation**: Validate all user inputs before API calls

## Performance Considerations

1. **Connection Pooling**: Use persistent session
2. **Timeouts**: Configurable request timeout (default 30s)
3. **Batch Operations**: API supports multiple orders/customers per request
4. **Response Caching**: Not implemented (API is not idempotent)

## Error Handling Philosophy

- **Fail Fast**: Validate inputs before API call
- **Clear Messages**: Include error codes in exception messages
- **Type Safety**: Specific exception types for different errors
- **Logging**: Client can add logging as needed

## Future Enhancements

1. **Async Support**: Add `AsyncEasyTransClient` with `aiohttp`
2. **Retry Logic**: Automatic retries with exponential backoff
3. **Rate Limiting**: Client-side rate limiting
4. **Webhook Server**: Built-in webhook receiver for testing
5. **CLI Tool**: Command-line interface for testing

---

## Appendix: Error Code Reference

| Code Range | Category | Exception Type |
|------------|----------|----------------|
| 5 | JSON parsing | `EasyTransValidationError` |
| 10-19 | Authentication | `EasyTransAuthError` |
| 20-29 | Orders | `EasyTransOrderError` |
| 30-39 | Destinations | `EasyTransDestinationError` |
| 40-45 | Packages | `EasyTransPackageError` |
| 50-65 | Customers | `EasyTransCustomerError` |

## Appendix: API Authentication Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. Create Order object
       ▼
┌─────────────────────────┐
│  EasyTransClient        │
│  .import_orders()       │
└──────┬──────────────────┘
       │
       │ 2. Serialize to dict
       │    order.to_dict()
       ▼
┌─────────────────────────┐
│  _make_request()        │
│                         │
│  Merge:                 │
│  {                      │
│    "authentication": {  │
│      "username": "...", │
│      "password": "...", │
│      "type": "order_...",│
│      "mode": "effect"   │
│    },                   │
│    "orders": [...]      │
│  }                      │
└──────┬──────────────────┘
       │
       │ 3. POST to API
       ▼
┌─────────────────────────┐
│  EasyTrans API          │
│  import_json.php        │
└──────┬──────────────────┘
       │
       │ 4. HTTP 200 (always)
       │    + JSON body
       ▼
┌─────────────────────────┐
│  Response Handler       │
│                         │
│  IF "error" in response:│
│    → _handle_error()    │
│    → raise Exception    │
│  ELSE:                  │
│    → parse result       │
│    → return OrderResult │
└─────────────────────────┘
```

## Questions for Review

Before implementation, please confirm:

1. **Package Name**: Is `easytrans-sdk` acceptable, or prefer `easytrans-python` or `python-easytrans`?
2. **License**: MIT license OK?
3. **Minimum Python Version**: Python 3.8+ acceptable?
4. **Webhook Handler**: Should we include a Flask/FastAPI webhook receiver example?
5. **Async Support**: Priority for initial release or future enhancement?
6. **Private PyPI**: Will this be published to PyPI or private repository?

---

**Next Steps**: Upon approval, switch to Code mode to begin implementation.
