# REST API

The EasyTrans REST API (`/api/v1/`) lets you **read** orders, customers, carriers, invoices and reference data.
All REST methods are available directly on [`EasyTransClient`](../api-reference/client.md).

## Reading Orders

```python
# Single order by number
order = client.get_order(35558)
print(order.attributes.status)

# Include full tracking history
order = client.get_order(35558, include_track_history=True)
for event in order.attributes.track_history:
    print(event.date, event.time, event.name)
```

## Listing and Filtering Orders

```python
# Basic list (first page)
response = client.get_orders()
for order in response.data:
    print(order.attributes.order_no, order.attributes.status)

# Filter by status and date range
response = client.get_orders(
    filter={"status": "planned", "date": {"gte": "2026-01-01", "lte": "2026-01-31"}},
)

# Filter on the waybill number of any destination
response = client.get_orders(filter={"waybillNo": "123456"})

# Sort descending by order date
response = client.get_orders(sort="-date")
```

### Attachments

Destination `photos`, `signature_url` and `documents` are requested with
`include_attachments`. The API documentation states list responses only carry
them when the flag is set — some installations return them regardless, so
treat the flag as the documented way to ask for them rather than a guarantee
either way.

```python
response = client.get_orders(include_attachments=True)
for order in response.data:
    for dest in order.attributes.destinations:
        print(dest.documents, dest.photos, dest.signature_url)
```

!!! note
    The parameter is only available on the list endpoint. `get_order()` does
    not accept it.

## Pagination

Results are paginated at 100 orders per page.

```python
response = client.get_orders()
while True:
    for order in response.data:
        process(order)
    if not response.has_next:
        break
    response = client.get_orders(page=response.meta.current_page + 1)
```

## Updating an Order

```python
client.update_order(
    35558,
    date="2026-08-20",
    time="09:30",
    status="checked",          # "signed-off" or "checked"
    substatus_no=12,           # 0 clears the substatus
    waybill_notes="Left at door",
)
```

Destinations, goods lines and rates are updated by passing dicts that identify
the row to change:

```python
client.update_order(
    35558,
    destinations=[{"stopNo": 2, "date": "2026-12-31", "fromTime": "09:00"}],
    goods=[{"packageNo": 1, "amount": 20}],
)
```

Documents are uploaded per destination as base64-encoded PDFs (max 20MB each):

```python
import base64, pathlib

encoded = base64.b64encode(pathlib.Path("POD.pdf").read_bytes()).decode()

client.update_order(
    35558,
    destinations=[{
        "stopNo": 2,
        "documents": [{
            "documentName": "POD.pdf",
            "category": "delivery_note",
            "internal": False,
            "base64EncodedDocument": encoded,
        }],
    }],
)
```

## Approving a Quote

Orders with status `quote` are converted into regular transport orders with
`approve_quote()`. Any other status is rejected by the API.

```python
order = client.approve_quote(35558)
print(order.attributes.status)   # "planned"
```

## Order Effort Fields

Alongside `distance`, orders carry the planned effort for the job:

| Attribute | Unit | Description |
|-----------|------|-------------|
| `stops` | count | Number of stops on the order |
| `waiting_time` | minutes | Waiting time |
| `loading_unloading_time` | minutes | Loading and unloading time |
| `hours` | hours | Total hours registered for the order |
| `composite_order_no` | — | Order number of the composite order, `0` when standalone |

```python
attrs = client.get_order(35558).attributes
print(attrs.stops, attrs.waiting_time, attrs.loading_unloading_time, attrs.hours)
```

## Reference Data

Products, substatuses, package types and vehicle types share the same shape:
a list method that accepts an optional `filter_name`, and a single-item method
that takes the number. All of them accept `include_deleted` (branch accounts).

```python
products   = client.get_products()
substatus  = client.get_substatuses()
pkg_types  = client.get_package_types()
veh_types  = client.get_vehicle_types()

for product in products.data:
    print(product.product_no, product.name)

# Single item by number
product = client.get_product(1)

# Filter by name, or include soft-deleted records
planned = client.get_substatuses(filter_name="Out for delivery")
all_types = client.get_vehicle_types(include_deleted=True)
```

## Customers, Carriers and Fleet

```python
# Customers (branch accounts only) — same filter/sort/page arguments as orders
customers = client.get_customers(filter={"companyName": "EasyTrans"}, sort="customerNo")
for customer in customers.data:
    print(customer.customer_no, customer.company_name)

customer = client.get_customer(2001)

# Carriers
carriers = client.get_carriers()
carrier  = client.get_carrier(44)
print(carrier.name, carrier.email)

# Fleet — filter on registration rather than a generic filter dict
fleet = client.get_fleet(filter_registration="AB-123-C")
for vehicle in fleet.data:
    print(vehicle.fleet_no, vehicle.license_plate, vehicle.active)

vehicle = client.get_fleet_vehicle(5)
```

Individual customer fields can be updated with `update_customer()`. Note that
`company_name` is required by the API on every call — see
[Managing Customers](customers.md) for details.

## Invoices

```python
invoices = client.get_invoices(filter={"invoiceDate": {"gte": "2026-01-01"}})
for inv in invoices.data:
    print(inv.invoice_no, inv.invoice_date, inv.total_amount, inv.paid)

# Embed the customer record, or fetch the PDF as base64
invoice = client.get_invoice(12345, include_customer=True, include_invoice_pdf=True)
print(invoice.customer.company_name)
print(invoice.invoice_pdf[:32])
```

## Working with Dates

Several REST model fields carry a raw `date` string in `YYYY-MM-DD` format.
Each of those fields is paired with a `date_parsed` computed property that
returns a [`datetime.date`](https://docs.python.org/3/library/datetime.html#datetime.date)
object — or `None` when the field is absent.

```python
from datetime import timedelta

order = client.get_order(35558)

# Raw string — always available, safe to serialise
print(order.attributes.date)           # "2026-02-18"

# Parsed date — enables arithmetic and formatting without extra imports
if order.attributes.date_parsed:
    deadline = order.attributes.date_parsed + timedelta(days=30)
    print(f"Invoice deadline: {deadline.isoformat()}")  # "2026-03-20"
    print(deadline.strftime("%d %B %Y"))                # "20 March 2026"

# Destination time windows
for dest in order.attributes.destinations:
    if dest.date_parsed:
        print(f"Stop {dest.stop_no}: scheduled {dest.date_parsed:%A, %d %b %Y}")

# Track & trace history
for event in order.attributes.track_history:
    if event.date_parsed:
        print(f"{event.date_parsed:%d-%m-%Y}  {event.name}")
```

!!! note
    The raw `date` string field is unchanged — existing code that reads or
    compares `order.attributes.date` as a string continues to work without
    modification.

## Response Models

All REST responses are typed dataclasses. See [REST Models](../api-reference/rest-models.md) for the full reference.
