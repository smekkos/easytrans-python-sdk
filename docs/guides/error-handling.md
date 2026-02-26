# Error Handling

The SDK raises typed exceptions for every error scenario so you can handle them precisely.

## Exception Hierarchy

```
EasyTransError                     ← base for all SDK errors
├── EasyTransAPIError              ← HTTP-level errors (4xx / 5xx)
│   └── EasyTransAuthError         ← 401 / 403 authentication failures
├── EasyTransValidationError       ← invalid data before the request is sent
├── EasyTransOrderError            ← order-specific API error codes
├── EasyTransDestinationError      ← destination-specific API error codes
├── EasyTransPackageError          ← package-specific API error codes
└── EasyTransCustomerError         ← customer-specific API error codes
```

See [Exceptions](../api-reference/exceptions.md) for the full attribute reference.

## Basic Error Handling

```python
from easytrans import EasyTransClient
from easytrans.exceptions import (
    EasyTransAuthError,
    EasyTransOrderError,
    EasyTransAPIError,
    EasyTransError,
)

client = EasyTransClient(...)

try:
    result = client.import_orders([order], mode="effect")
except EasyTransAuthError:
    print("Authentication failed — check credentials")
except EasyTransOrderError as exc:
    print(f"Order error [{exc.error_code}]: {exc.message}")
except EasyTransAPIError as exc:
    print(f"API error (HTTP {exc.status_code}): {exc.message}")
except EasyTransError as exc:
    print(f"SDK error: {exc}")
```

## REST API Errors

```python
from easytrans.exceptions import EasyTransAPIError

try:
    order = client.get_order("ET-NONEXISTENT")
except EasyTransAPIError as exc:
    if exc.status_code == 404:
        print("Order not found")
    else:
        raise
```

## Validation Errors

Validation errors are raised **before** the HTTP request is made:

```python
from easytrans.exceptions import EasyTransValidationError

try:
    order = Order(productno=-1, date="not-a-date", order_destinations=[])
    client.import_orders([order])
except EasyTransValidationError as exc:
    print(f"Validation failed: {exc}")
```

## Error Attributes

| Exception | Extra Attributes |
|-----------|-----------------|
| `EasyTransAPIError` | `status_code`, `response_body` |
| `EasyTransOrderError` | `error_code`, `orderno` |
| `EasyTransDestinationError` | `error_code`, `destination_index` |
| `EasyTransPackageError` | `error_code` |
| `EasyTransCustomerError` | `error_code`, `customercode` |
