# Managing Customers

Customer records can be created or updated via the **JSON Import API**, and
updated individually via the **REST API**.

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

The EasyTrans OpenAPI spec documents server-side filtering on nested contact
and address sub-fields (e.g. `filter[contacts[name]`, `filter[contacts[email]`,
`filter[businessAddress[city]`). Whether these are available depends on the
API version deployed on your tenant — some environments return HTTP 400
"Invalid filter" for these parameters even with a syntactically correct
request.

When contact sub-field filtering is available, use **bracket notation** for
the SDK filter key. The key must be the literal sub-key without a closing
bracket — the SDK wraps it in `filter[{key}]` automatically:

```python
# filter[contacts[email]=kevin@example.nl  (bracket notation — spec-correct)
response = client.get_customers(filter={"contacts[email": "kevin@example.nl"})

# filter[contacts[name]=Kevin van Beek
response = client.get_customers(filter={"contacts[name": "Kevin van Beek"})

# filter[businessAddress[city]=DEVENTER
response = client.get_customers(filter={"businessAddress[city": "DEVENTER"})
```

!!! warning "Common mistake — dot notation always returns HTTP 400"
    `"contacts.email"` generates `filter[contacts.email]=…` (dot notation),
    which the API rejects. Always use the opening-bracket form:
    `"contacts[email"`.

### Client-side contact search (works on all tenants)

If your deployed API version does not support contact sub-field filtering,
scan all pages in Python instead:

```python
def find_customers_by_contact_email(client, email: str):
    """Return every customer that has a contact with the given e-mail."""
    return [
        customer
        for customer in client.get_customers().data
        if any(c.email == email for c in customer.contacts)
    ]
```

## Updating a Customer via REST (PUT)

`update_customer()` sends a `PUT /api/v1/customers/{customerNo}` request and
returns the updated [`RestCustomer`](../api-reference/rest-models.md).
This is available to **branch accounts only**.

`company_name` is required by the API on every call.  All other arguments are
optional — only the ones you supply are sent; the rest remain unchanged.

```python
# Update financial details
customer = client.update_customer(
    2001,
    "ACME Logistics BV",
    debtor_no="D-0042",
    payment_period=30,
    iban_no="NL63INGB0004511811",
)
print(customer.updated_at)

# Update a contact by userId
customer = client.update_customer(
    2001,
    "ACME Logistics BV",
    contacts=[{"userId": 271, "email": "new@acme.nl"}],
)

# Update opening hours
customer = client.update_customer(
    2001,
    "ACME Logistics BV",
    opening_hours={"from": "08:30", "to": "17:30"},
)
if customer.opening_hours:
    print(customer.opening_hours.from_time, "–", customer.opening_hours.to_time)

# Deactivate a customer
customer = client.update_customer(2001, "ACME Logistics BV", active=False)
```

### Two update paths compared

| | Import API (`import_customers`) | REST PUT (`update_customer`) |
|---|---|---|
| Identify by | `customercode` (string) | `customerNo` (integer) |
| Mode | `"test"` (validate) / `"effect"` (save) | Always writes immediately |
| Contacts | Replaces all contacts | Updates individual contacts by `userId`/`contactNo` |
| Branch only | No (customer accounts can import) | Yes |
| Use when | Bulk data sync, creating customers | Targeted field updates on individual customers |
