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

## Response Models

All REST responses are typed dataclasses. See [REST Models](../api-reference/rest-models.md) for the full reference.
