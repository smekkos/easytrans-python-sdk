# Creating Orders

Transport orders are created via the **JSON Import API** (`import_json.php`).

## Minimal Order

```python
from easytrans import EasyTransClient, Order, Destination

client = EasyTransClient(...)

order = Order(
    productno=2,
    date="2026-02-18",
    order_destinations=[
        Destination(company_name="Sender BV",   postal_code="1234AB", city="Amsterdam"),
        Destination(company_name="Receiver BV", postal_code="5678CD", city="Utrecht"),
    ],
)

result = client.import_orders([order], mode="effect")
print(result.new_ordernos)   # ['ET-100001']
```

## Batch Submission

Submit multiple orders in a single API call:

```python
orders = [build_order(row) for row in my_dataset]
result = client.import_orders(orders, mode="effect")

for orderno in result.new_ordernos:
    print(f"Created: {orderno}")
```

## Extended Order with Packages

```python
from easytrans import Order, Destination, Package

order = Order(
    productno=2,
    date="2026-02-18",
    reference="MY-REF-001",
    order_destinations=[
        Destination(
            company_name="Sender BV",
            street="Keizersgracht",
            housenumber="100",
            postal_code="1015CJ",
            city="Amsterdam",
            country="NL",
            contact_name="Jan de Vries",
            phone="0201234567",
            email="jan@example.nl",
            remarks="Ring bell",
        ),
        Destination(
            company_name="Receiver BV",
            postal_code="5678CD",
            city="Utrecht",
            country="NL",
            packages=[
                Package(amount=2, weight=5.0, length=30, width=20, height=15),
            ],
        ),
    ],
)
```

## Dry-Run (Test Mode)

Use `mode="test"` to validate an order without creating it in EasyTrans:

```python
result = client.import_orders([order], mode="test")
# No order numbers are returned for test-mode submissions
```

## Attaching a Document

```python
import base64, pathlib

pdf_bytes = pathlib.Path("label.pdf").read_bytes()

order = Order(
    productno=2,
    date="2026-02-18",
    order_destinations=[...],
    document=base64.b64encode(pdf_bytes).decode(),
    document_name="label.pdf",
)
```

## Result Object

[`import_orders()`](../api-reference/client.md) returns an [`OrderResult`](../api-reference/models.md):

| Attribute | Type | Description |
|-----------|------|-------------|
| `new_ordernos` | `list[str]` | EasyTrans order numbers for created orders |
| `updated_ordernos` | `list[str]` | Order numbers of updated orders |
| `errors` | `list[str]` | Any per-order error messages |
