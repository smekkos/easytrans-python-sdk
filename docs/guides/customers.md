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

## Reading Customers via REST

```python
# List customers (branch accounts only)
response = client.get_customers(filter={"companyName": "ACME"})
for customer in response.data:
    print(customer.customer_no, customer.company_name)
```

### Filtering by contact or address fields

The EasyTrans API **does** support server-side filtering on nested contact
and address sub-fields, but uses a **bracket notation** key syntax.
The filter key must be the literal sub-key without a closing bracket — the
SDK's `_build_rest_params` adds the outer wrapping automatically.

```python
# Search by contact e-mail (server-side)
response = client.get_customers(filter={"contacts[email": "kevin@example.nl"})

# Search by contact name
response = client.get_customers(filter={"contacts[name": "Kevin van Beek"})

# Filter by city in the business address
response = client.get_customers(filter={"businessAddress[city": "DEVENTER"})
```

!!! warning "Common mistake — dot notation returns HTTP 400"
    The following **does not work** and will raise an `EasyTransAPIError`
    (HTTP 400 "Invalid filter"):

    ```python
    # WRONG — generates filter[contacts.email]=… which the API rejects
    client.get_customers(filter={"contacts.email": "kevin@example.nl"})
    ```

    The correct key uses an opening bracket: `"contacts[email"`, not
    `"contacts.email"`.
