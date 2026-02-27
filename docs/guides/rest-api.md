# REST API

The EasyTrans REST API (`/api/v1/`) lets you **read** orders, customers, carriers, invoices and reference data.
All REST methods are available directly on [`EasyTransClient`](../api-reference/client.md).

## Reading Orders

```python
# Single order by number
order = client.get_order("ET-100001")
print(order.attributes.status)

# Include full tracking history
order = client.get_order("ET-100001", include_track_history=True)
for event in order.attributes.track_history:
    print(event.datetime, event.description)
```

## Listing and Filtering Orders

```python
from easytrans import EasyTransClient

# Basic list (first page)
response = client.list_orders()
for order in response.data:
    print(order.id, order.attributes.status)

# Filter by status and date range
response = client.list_orders(
    filter_status="delivered",
    filter_date_from="2026-01-01",
    filter_date_to="2026-01-31",
)

# Sort descending by creation date
response = client.list_orders(sort="-created_at")
```

## Pagination

```python
# Manual paging
page = 1
while True:
    response = client.list_orders(page=page, page_size=50)
    for order in response.data:
        process(order)
    if page >= response.meta.page_count:
        break
    page += 1
```

Or use the auto-paginating iterator:

```python
for order in client.iter_orders(filter_status="in_transit"):
    process(order)
```

## Updating an Order

```python
client.update_order("ET-100001", status="delivered", remarks="Left at door")
```

## Reference Data

```python
products   = client.list_products()
carriers   = client.list_carriers()
substatus  = client.list_substatuses()
pkg_types  = client.list_package_types()
veh_types  = client.list_vehicle_types()
```

## Customers, Carriers and Fleet

```python
customers = client.list_rest_customers()
fleet     = client.list_fleet_vehicles()
```

## Invoices

```python
invoices = client.list_invoices(filter_year=2026, filter_month=1)
for inv in invoices.data:
    print(inv.id, inv.attributes.total_amount)
```

## Working with Dates

Several REST model fields carry a raw `date` string in `YYYY-MM-DD` format.
Each of those fields is paired with a `date_parsed` computed property that
returns a [`datetime.date`](https://docs.python.org/3/library/datetime.html#datetime.date)
object — or `None` when the field is absent.

```python
from datetime import timedelta

order = client.get_order("ET-100001")

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
