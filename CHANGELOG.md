# Changelog

## Unreleased

- `update_order()` now accepts `distance`, `distance_purchase`, `stops`,
  `waiting_time`, `loading_unloading_time`, and decimal `hours`. Order responses
  expose `order.attributes.distance_purchase`. The REST guide also shows how to
  update `carrierNotes` on a single destination.

- Align the vendored REST spec with the current official API; add address-book
  list/get/create/update/delete methods, a typed read model, DELETE transport and
  HTTP 204 handling. Address-book writes return raw JSON because their success
  schemas are not published.
- Support JSON order import v5.4 fields: customer contact `userid`, destination
  `delivery_date_from` and document `category`.
- Preserve webhook destination scheduling fields and task-result POD documents.
- Document the expanded order status enum and verify existing status/substatus,
  rate activation/unit-price, pagination and product/fleet support without changing
  those existing behaviors. No package version bump or consumer upgrade.
