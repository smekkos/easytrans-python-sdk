# EasyTrans Python SDK

A pure Python SDK for integrating with **EasyTrans Software** — a Dutch Transport Management System (TMS).

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- ✅ **Pure Python** — Framework-agnostic, works with Django, Flask, FastAPI, or standalone scripts
- ✅ **Strongly Typed** — Dataclass models with full type hints
- ✅ **Unified Client** — JSON Import API and REST API in one object
- ✅ **Error Handling** — Specific exceptions for every API error code
- ✅ **Webhook Support** — Parse and validate order-status update webhooks

## Installation

```bash
pip install easytrans-sdk
```

For development (includes docs, linting and test tools):

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from easytrans import EasyTransClient, Order, Destination

# 1. Create a client
client = EasyTransClient(
    server_url="mytrans.nl",
    environment_name="production",
    username="your_username",
    password="your_password",
)

# 2. Build an order
order = Order(
    productno=2,
    date="2026-02-18",
    order_destinations=[
        Destination(company_name="Sender",   postal_code="1234AB", city="Amsterdam"),
        Destination(company_name="Receiver", postal_code="5678CD", city="Utrecht"),
    ],
)

# 3. Submit (JSON Import API)
result = client.import_orders([order], mode="effect")
print(f"Order created: {result.new_ordernos[0]}")

# 4. Read back (REST API)
rest_order = client.get_order(result.new_ordernos[0], include_track_history=True)
print(f"Status:   {rest_order.attributes.status}")
print(f"Tracking: {rest_order.attributes.tracking_id}")
```

## API Surfaces

| Surface | Endpoint | Purpose |
|---------|----------|---------|
| **JSON Import API** | `POST /import_json.php` | Create/update orders and customers |
| **REST API** | `/api/v1/` | Read, filter, sort orders; reference data; invoices |

## Next Steps

- [Authentication Guide](guides/authentication.md)
- [Creating Orders](guides/orders.md)
- [Managing Customers](guides/customers.md)
- [REST API](guides/rest-api.md)
- [Webhook Handling](guides/webhooks.md)
- [Error Handling](guides/error-handling.md)
- [API Reference](api-reference/index.md)
