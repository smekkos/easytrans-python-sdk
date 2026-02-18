# EasyTrans SDK - Quick Start Guide

Get up and running with the EasyTrans Python SDK in 5 minutes.

## Installation

```bash
pip install easytrans-sdk
```

## 1. Configure Credentials

Create a `.env` file or set environment variables:

```bash
export EASYTRANS_SERVER="mytrans.nl"
export EASYTRANS_ENV="demo"
export EASYTRANS_USERNAME="your_username"
export EASYTRANS_PASSWORD="your_password"
```

## 2. Create Your First Order

```python
from easytrans import EasyTransClient, Order, Destination
import os

# Initialize client
client = EasyTransClient(
    server_url=os.getenv("EASYTRANS_SERVER"),
    environment_name=os.getenv("EASYTRANS_ENV"),
    username=os.getenv("EASYTRANS_USERNAME"),
    password=os.getenv("EASYTRANS_PASSWORD"),
)

# Create simple order
order = Order(
    productno=2,  # Get this from your carrier
    date="2026-02-18",
    order_destinations=[
        Destination(
            company_name="Pickup Company",
            postal_code="1234AB",
            city="Amsterdam",
        ),
        Destination(
            company_name="Delivery Company",
            postal_code="5678CD",
            city="Utrecht",
        ),
    ]
)

# Test first (recommended)
test_result = client.import_orders([order], mode="test")
print(f"✓ Validation passed!")

# Then submit
result = client.import_orders([order], mode="effect")
print(f"✓ Order created: {result.new_ordernos[0]}")
print(f"✓ Tracking: {result.order_tracktrace[str(result.new_ordernos[0])].local_trackingnr}")
```

## 3. Handle Webhooks (Optional)

Setup a webhook endpoint to receive status updates:

```python
from flask import Flask, request
from easytrans import EasyTransClient

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    webhook = EasyTransClient.parse_webhook(request.get_data())
    
    print(f"Order {webhook.order.orderNo} status: {webhook.order.status}")
    
    return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(port=5000)
```

Register this endpoint URL with your EasyTrans carrier.

## 4. Testing

### Unit Tests (no credentials needed)

```bash
pip install easytrans-sdk[dev]
pytest
```

### Integration Tests (validates against the real EasyTrans API)

The integration tests call the API in **`mode="test"`** — the server validates
every payload but **no real orders or customers are ever created**.

#### Environment variables

A `.env.example` template is included. Copy it and fill in your values:

```bash
cp .env.example .env
# edit .env
```

The variables it expects (`.env` is git-ignored):

```bash
EASYTRANS_SERVER=mytrans.nl        # hostname only, no https://
EASYTRANS_ENV=demo
EASYTRANS_USERNAME=your_username
EASYTRANS_PASSWORD=your_password
EASYTRANS_TEST_PRODUCTNO=2         # valid product number (Customer Portal → Products)
EASYTRANS_TEST_CUSTOMERNO=3        # only needed for branch accounts
```

#### Run

```bash
# Load .env and run (works in bash, zsh and sh)
export $(grep -v '^#' .env | grep -v '^$' | xargs)
pytest tests/integration/ -m integration -v --no-cov
```

#### What gets skipped automatically

| Condition | Tests skipped |
|---|---|
| `EASYTRANS_USERNAME` not set | Entire integration suite |
| `EASYTRANS_TEST_PRODUCTNO` not set | All order import tests |
| `EASYTRANS_TEST_CUSTOMERNO` not set | Nothing — `customerno=None` is omitted (correct for direct-customer accounts) |

See the [Testing section in README.md](README.md#testing) for the full
breakdown of what each test proves and which SDK bugs were found.

## Need Help?

- 📖 Full documentation: [README.md](README.md)
- 💡 Examples: [`examples/`](examples/) directory
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/easytrans-sdk/issues)
- 📧 EasyTrans Support: support@easytrans.nl

## Common Use Cases

### Get Rate Calculation

```python
result = client.import_orders([order], mode="test", return_rates=True)
rates = result.order_rates[str(result.new_ordernos[0])]
print(f"Price: €{rates.order_total_excluding_vat}")
```

### Request Shipping Label

```python
result = client.import_orders([order], mode="effect", return_documents="label10x15")
# Label is in result.order_documents as base64 PDF
```

### Create Customer

```python
from easytrans import Customer, CustomerContact

customer = Customer(
    company_name="New Customer Inc.",
    postal_code="1234AB",
    city="Amsterdam",
    customer_contacts=[
        CustomerContact(
            contact_name="John Doe",
            email="john@example.com"
        )
    ]
)

result = client.import_customers([customer], mode="effect")
print(f"Customer created: {result.new_customernos[0]}")
```

## Django Integration

See [`examples/django_integration.py`](examples/django_integration.py) for complete Django setup including:
- Settings configuration
- Service layer pattern
- Webhook handler view
- Management commands

---

**Ready to integrate?** Check out the full [README.md](README.md) for detailed documentation.
