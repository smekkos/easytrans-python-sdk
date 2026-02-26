# Managing Customers

Customer records are created and updated via the **JSON Import API**.

## Creating a Customer

```python
from easytrans import EasyTransClient, Customer

client = EasyTransClient(...)

customer = Customer(
    customercode="C001",
    company_name="ACME Logistics BV",
    street="Hoofdstraat",
    housenumber="42",
    postal_code="1234AB",
    city="Amsterdam",
    country="NL",
    phone="0201234567",
    email="info@acme.nl",
)

result = client.import_customers([customer], mode="effect")
print(result.new_customercodes)   # ['C001']
```

## Updating an Existing Customer

Submit a `Customer` with the same `customercode` — EasyTrans will update the existing record:

```python
customer = Customer(
    customercode="C001",     # must match an existing code
    email="new@acme.nl",
)

result = client.import_customers([customer], mode="effect")
print(result.updated_customercodes)
```

## Batch Import

```python
customers = [Customer(customercode=f"C{i:04d}", ...) for i in range(100)]
result = client.import_customers(customers, mode="effect")
```

## Result Object

[`import_customers()`](../api-reference/client.md) returns a [`CustomerResult`](../api-reference/models.md):

| Attribute | Type | Description |
|-----------|------|-------------|
| `new_customercodes` | `list[str]` | Codes of newly created customers |
| `updated_customercodes` | `list[str]` | Codes of updated customers |
| `errors` | `list[str]` | Any per-customer error messages |
