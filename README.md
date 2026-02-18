# EasyTrans Python SDK

A pure Python SDK for integrating with **EasyTrans Software** (Dutch TMS - Transport Management System).

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

✅ **Pure Python** - Framework-agnostic, works with Django, Flask, FastAPI, or standalone  
✅ **Strongly Typed** - Dataclass models with full type hints  
✅ **Error Handling** - Specific exceptions for all API error codes  
✅ **Webhook Support** - Parse and validate status update webhooks  

## Installation

```bash
pip install easytrans-sdk
```

For development:

```bash
pip install easytrans-sdk[dev]
```

## Quick Start

```python
from easytrans import EasyTransClient, Order, Destination

# Initialize client
client = EasyTransClient(
    server_url="mytrans.nl",
    environment_name="production",
    username="your_username",
    password="your_password"
)

# Create an order
order = Order(
    productno=2,
    date="2026-02-18",
    order_destinations=[
        Destination(company_name="Sender", postal_code="1234AB", city="Amsterdam"),
        Destination(company_name="Receiver", postal_code="5678CD", city="Utrecht"),
    ]
)

# Submit to EasyTrans
result = client.import_orders([order], mode="effect")
print(f"Order created: {result.new_ordernos[0]}")
```

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Order Management](#order-management)
- [Customer Management](#customer-management)
- [Webhook Handling](#webhook-handling)
- [Django Integration](#django-integration)
- [Error Handling](#error-handling)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Contributing](#contributing)

## Authentication

EasyTrans uses a unique authentication method where credentials are embedded in the JSON POST body, **not** in HTTP headers.

```python
from easytrans import EasyTransClient

client = EasyTransClient(
    server_url="mytrans.nl",          # Your server URL
    environment_name="production",     # Your environment name
    username="your_username",          # API username
    password="your_password",          # API password
    default_mode="test",               # "test" or "effect"
    timeout=30,                        # Request timeout in seconds
)
```

### Getting Credentials

Before you begin, obtain the following from your carrier:

1. **Server URL** - e.g., `mytrans.nl`, `mytrans.be`, `mytransport.co.uk`
2. **Environment name** - Your specific environment (e.g., `demo`, `production`)
3. **Username & Password** - Same as your Customer Portal login
4. **Product number(s)** - Available products for booking orders

## Order Management

### Creating a Simple Order

```python
from easytrans import Order, Destination, Package
from easytrans.constants import CollectDeliver

# Define pickup location
pickup = Destination(
    collect_deliver=CollectDeliver.PICKUP.value,
    company_name="Sender Company",
    address="Keizersgracht",
    houseno="1",
    postal_code="1015CC",
    city="Amsterdam",
    country="NL",
    telephone="020-1234567",
)

# Define delivery location
delivery = Destination(
    collect_deliver=CollectDeliver.DELIVERY.value,
    company_name="Receiver Company",
    address="Kanaalweg",
    houseno="14",
    postal_code="3526KL",
    city="Utrecht",
    country="NL",
    customer_reference="ORDER-123",
)

# Define package details
package = Package(
    amount=2.0,      # 2 packages
    weight=150.0,    # kg per package
    length=120.0,    # cm
    width=80.0,
    height=50.0,
    description="Euro pallets",
)

# Create order
order = Order(
    productno=2,
    date="2026-02-18",
    time="14:00",
    status="submit",  # "submit", "save", or "quote"
    remark="Important delivery",
    external_id="my-system-order-123",  # Your internal reference
    order_destinations=[pickup, delivery],
    order_packages=[package],
)

# Submit order
result = client.import_orders([order], mode="effect")
```

### Test Before Submitting

Always test your orders first:

```python
# Test mode - validates but doesn't create order
test_result = client.import_orders([order], mode="test")
print(f"Validation passed: {test_result.total_orders} order(s)")

# If validation passes, submit for real
result = client.import_orders([order], mode="effect")
print(f"Order created: {result.new_ordernos[0]}")
```

### Get Rate Calculation

```python
result = client.import_orders(
    [order], 
    mode="test",
    return_rates=True
)

if result.order_rates:
    for order_no, rates in result.order_rates.items():
        print(f"Total excl. VAT: €{rates.order_total_excluding_vat}")
        print(f"Total incl. VAT: €{rates.order_total_including_vat}")
```

### Request Shipping Labels

```python
result = client.import_orders(
    [order],
    mode="effect",
    return_documents="label10x15"  # Returns base64 PDF label
)

if result.order_documents:
    for order_no, doc in result.order_documents.items():
        if "base64_document" in doc:
            # Save or display label
            import base64
            pdf_data = base64.b64decode(doc["base64_document"])
            with open(f"label_{order_no}.pdf", "wb") as f:
                f.write(pdf_data)
```

### Upload Documents with Order

```python
from easytrans import Document
import base64

# Read document file
with open("invoice.pdf", "rb") as f:
    pdf_content = base64.b64encode(f.read()).decode()

# Attach to destination
delivery.documents = [
    Document(
        name="Commercial Invoice",
        type="pdf",
        base64_content=pdf_content,
    )
]
```

## Customer Management

### Creating a Customer

```python
from easytrans import Customer, CustomerContact
from easytrans.constants import Salutation

# Define contact person
contact = CustomerContact(
    salutation=Salutation.MR.value,
    contact_name="John Doe",
    telephone="020-1234567",
    mobile="06-12345678",
    email="john@example.com",
    use_email_for_invoice=True,
)

# Create customer
customer = Customer(
    company_name="Example Company",
    address="Main Street",
    houseno="123",
    postal_code="1234AB",
    city="Amsterdam",
    country="NL",
    email="info@example.com",
    external_id="customer-123",
    customer_contacts=[contact],
)

# Import customer
result = client.import_customers([customer], mode="effect")
print(f"Customer created: {result.new_customernos[0]}")
```

### Updating a Customer

```python
# Use existing customer number
customer = Customer(
    customerno=12345,  # Existing customer number
    update_on_existing_customerno=True,  # Enable update mode
    company_name="Updated Company Name",
    # ... other fields
)

result = client.import_customers([customer], mode="effect")
```

## Webhook Handling

EasyTrans sends webhooks when order status changes (collected, delivered, etc.).

### Flask Example

```python
from flask import Flask, request, jsonify
from easytrans import EasyTransClient
from easytrans.exceptions import EasyTransError

app = Flask(__name__)

@app.route('/easytrans/webhook', methods=['POST'])
def webhook_handler():
    try:
        # Parse and validate webhook
        webhook = EasyTransClient.parse_webhook(
            payload=request.get_data(),
            expected_api_key="b6e6a42d-1243-453d-81ba-0dac775227fc",
            headers=dict(request.headers)
        )
        
        # Process webhook
        order_id = webhook.order.externalId
        status = webhook.order.status
        
        if status == "collected":
            print(f"Order {order_id} was collected")
            
        elif status == "finished":
            print(f"Order {order_id} was delivered")
            # Get signature if available
            for dest in webhook.order.destinations:
                if dest.taskType == "delivery":
                    print(f"Signed by: {dest.taskResult.signedBy}")
        
        return jsonify({"status": "ok"}), 200
        
    except EasyTransError as e:
        return jsonify({"error": str(e)}), 400
```

### Django Example

See [`examples/django_integration.py`](examples/django_integration.py) for a complete Django integration example.

## Django Integration

### Settings Configuration

```python
# settings.py
import os

EASYTRANS = {
    "SERVER_URL": "mytrans.nl",
    "ENVIRONMENT": os.environ.get("EASYTRANS_ENV", "demo"),
    "USERNAME": os.environ["EASYTRANS_USERNAME"],
    "PASSWORD": os.environ["EASYTRANS_PASSWORD"],
    "DEFAULT_MODE": "effect",
    "WEBHOOK_API_KEY": os.environ["EASYTRANS_WEBHOOK_KEY"],
}
```

### Service Layer

```python
# services/easytrans_service.py
from django.conf import settings
from easytrans import EasyTransClient

def get_easytrans_client():
    return EasyTransClient(
        server_url=settings.EASYTRANS["SERVER_URL"],
        environment_name=settings.EASYTRANS["ENVIRONMENT"],
        username=settings.EASYTRANS["USERNAME"],
        password=settings.EASYTRANS["PASSWORD"],
        default_mode=settings.EASYTRANS["DEFAULT_MODE"],
    )

def create_shipment_from_order(django_order):
    client = get_easytrans_client()
    
    # Build EasyTrans order from Django model
    easytrans_order = Order(
        productno=2,
        external_id=str(django_order.id),
        order_destinations=[...],  # Build from Django model
    )
    
    result = client.import_orders([easytrans_order], mode="effect")
    
    # Save tracking info back to Django
    django_order.tracking_number = result.order_tracktrace[...].local_trackingnr
    django_order.save()
    
    return result
```

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from easytrans.exceptions import (
    EasyTransAuthError,
    EasyTransOrderError,
    EasyTransDestinationError,
    EasyTransCustomerError,
)

try:
    result = client.import_orders([order], mode="effect")
    
except EasyTransAuthError as e:
    # Authentication failed (wrong username/password)
    print(f"Authentication error: {e}")
    
except EasyTransOrderError as e:
    # Order validation error (invalid product number, etc.)
    print(f"Order error: {e}")
    
except EasyTransDestinationError as e:
    # Destination validation error (invalid address, etc.)
    print(f"Destination error: {e}")
    
except EasyTransAPIError as e:
    # HTTP/network error
    print(f"API error: {e}")
```

### Exception Hierarchy

```
EasyTransError (base)
├── EasyTransAPIError (HTTP/network errors)
├── EasyTransAuthError (authentication failures)
├── EasyTransValidationError (general validation)
├── EasyTransOrderError (order validation)
├── EasyTransDestinationError (destination validation)
├── EasyTransPackageError (package validation)
└── EasyTransCustomerError (customer validation)
```

## API Reference

### EasyTransClient

#### `__init__(server_url, environment_name, username, password, ...)`

Initialize the client.

**Parameters:**
- `server_url` (str): Base server URL (e.g., "mytrans.nl")
- `environment_name` (str): Environment name (e.g., "production")
- `username` (str): API username
- `password` (str): API password
- `default_mode` (str): Default mode "test" or "effect" (default: "test")
- `timeout` (int): Request timeout in seconds (default: 30)

#### `import_orders(orders, mode=None, return_rates=False, return_documents="")`

Import one or more orders.

**Parameters:**
- `orders` (List[Order]): List of Order objects
- `mode` (str): Override default mode
- `return_rates` (bool): Request rate calculation
- `return_documents` (str): Document type to return

**Returns:** `OrderResult` with created order numbers and tracking info

**Raises:** Various `EasyTransError` subclasses

#### `import_customers(customers, mode=None)`

Import one or more customers.

**Parameters:**
- `customers` (List[Customer]): List of Customer objects
- `mode` (str): Override default mode

**Returns:** `CustomerResult` with created customer numbers

#### `parse_webhook(payload, expected_api_key=None, headers=None)` (static)

Parse and validate webhook payload.

**Parameters:**
- `payload` (str|bytes|dict): Webhook payload
- `expected_api_key` (str): Optional API key for validation
- `headers` (dict): Optional HTTP headers

**Returns:** `WebhookPayload` object

### Models

All models are dataclasses with `to_dict()` and `from_dict()` methods.

- **Order** - Transport order
- **Destination** - Pickup/delivery address
- **Package** - Goods/package information
- **Document** - File to upload with order
- **Customer** - Customer entity
- **CustomerContact** - Contact person
- **OrderResult** - Order import response
- **CustomerResult** - Customer import response
- **WebhookPayload** - Webhook callback data

See [`easytrans/models.py`](easytrans/models.py) for complete model definitions.

## Testing

The SDK ships with two complementary test suites:

| Suite | Location | Needs real API? | What it proves |
|---|---|---|---|
| **Unit tests** | `tests/` | ❌ No | Internal logic: serialisation, error mapping, webhook parsing |
| **Integration tests** | `tests/integration/` | ✅ Yes | Real API accepts the exact JSON your SDK sends |

### Unit Tests (default)

Run without any credentials — all HTTP calls are intercepted by the
[`responses`](https://github.com/getsentry/responses) library.

```bash
# Install dev dependencies
pip install -e .[dev]

# Run unit tests (default — integration tests excluded automatically)
pytest

# Run with HTML coverage report
pytest --cov=easytrans --cov-report=html

# Run a single file
pytest tests/test_client.py -v
```

### Integration Tests

Integration tests make real HTTP requests to the EasyTrans demo environment
using **`mode="test"`** — which validates every payload on the server but
**never creates real orders or customers**.

#### 1. Set credentials

Copy the provided template and fill in your values:

```bash
cp .env.example .env
# edit .env with your server, credentials, and product/customer numbers
```

`.env` is git-ignored. The variables it expects:

```bash
# ── Connection ──────────────────────────────────────────────────────────────
EASYTRANS_SERVER=mytrans.nl        # hostname only, no https://
EASYTRANS_ENV=demo                  # environment path segment
EASYTRANS_USERNAME=your_username
EASYTRANS_PASSWORD=your_password

# ── Order tests ─────────────────────────────────────────────────────────────
# Product number valid in your environment (Customer Portal → Products/Services)
EASYTRANS_TEST_PRODUCTNO=2

# Customer number — required only for branch accounts (errorno 23 if absent)
# Leave blank for direct-customer accounts
EASYTRANS_TEST_CUSTOMERNO=3
```

#### 2. Run integration tests

```bash
# Run the full integration suite
pytest tests/integration/ -m integration -v

# Run a single file
pytest tests/integration/test_order_simple.py -m integration -v

# Run everything (unit + integration) — skip integration if no credentials
pytest -m integration --no-cov -v

# Quick one-liner with inline env vars
EASYTRANS_SERVER=mytrans.nl EASYTRANS_ENV=demo \
EASYTRANS_USERNAME=user EASYTRANS_PASSWORD=pass \
EASYTRANS_TEST_PRODUCTNO=2 EASYTRANS_TEST_CUSTOMERNO=3 \
pytest tests/integration/ -m integration -v --no-cov
```

### Test Structure

```
tests/
├── conftest.py                          # Unit-test fixtures (mocked responses)
├── test_client.py                       # EasyTransClient unit tests
├── test_models.py                       # Model serialisation unit tests
└── integration/
    ├── conftest.py                      # Real client fixture + auto-skip logic
    ├── test_order_minimal.py            # Bare-minimum 2-destination order
    ├── test_order_simple.py             # All common fields + one package
    ├── test_order_extended.py           # 3 destinations, routed packages, rates/documents
    ├── test_order_with_document.py      # base64 PDF attached to a destination
    ├── test_order_batch.py              # Multiple orders in one request
    ├── test_customer_simple.py          # Single customer, one contact
    ├── test_customer_extended.py        # Two contacts with portal credentials
    ├── test_customer_update.py          # Update existing customer record
    └── test_error_paths.py             # Auth errors, unknown productno, missing fields
```

### Writing Custom Unit Tests

```python
import responses
from easytrans import EasyTransClient, Order

@responses.activate
def test_my_integration():
    # Mock API response
    responses.add(
        responses.POST,
        "https://mytrans.nl/demo/import_json.php",
        json={"result": {"mode": "test", "total_orders": 1,
                          "total_order_destinations": 2, "total_order_packages": 0,
                          "result_description": "OK", "new_ordernos": [],
                          "order_tracktrace": {}}},
        status=200,
    )

    client = EasyTransClient(
        server_url="mytrans.nl", environment_name="demo",
        username="user", password="pass",
    )
    result = client.import_orders([order])

    assert result.total_orders == 1
```

## Requirements

- Python 3.8+
- requests >= 2.28.0

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/easytrans-sdk.git
cd easytrans-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black easytrans tests

# Lint code
ruff check easytrans tests

# Type checking
mypy easytrans
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Repository](https://github.com/yourusername/easytrans-sdk)
- **Issues**: [GitHub Issues](https://github.com/yourusername/easytrans-sdk/issues)
- **EasyTrans Support**: support@easytrans.nl

## Changelog

### Version 1.0.0 (2026-02-18)

- Initial release
- Order import functionality
- Customer import functionality
- Webhook support
- Comprehensive test suite
- Django integration examples

## Credits

Created for integrating Django projects with EasyTrans TMS.

---

**Note**: This SDK is not officially affiliated with EasyTrans Software B.V. For official API documentation, contact your EasyTrans carrier.
