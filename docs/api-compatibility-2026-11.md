# API compatibility verification — 2026-11-13

## Official sources

Public, unauthenticated GETs only; no API records were read or written.

- REST: https://www.mytrans3.nl/abtransport/api/docs.openapi
  (`python scripts/sync_spec.py --check` confirms the vendored YAML matches).
- Developer downloads: https://www.easytrans.nl/kennisbank/koppelingen/module-koppeling-externe-systemen/developers-api-documentation/
- Order import and status/POD webhooks: https://www.easytrans.nl/wp-content/uploads/EasyTrans-JSON-order-import-v5.4.zip
  (PDF revision history: v5.1 POD documents, v5.2 document categories,
  v5.3 earliest destination date, v5.4 customer contact assignment).
- Customer import: https://www.easytrans.nl/wp-content/uploads/EasyTrans-JSON-customer-import-v2.2.zip
  (the published version is still v2.2, matching the repository bundle).

The REST endpoint remains `/api/v1/`; no separate “new API” version was identified.
The old v5.0 documentation bundle is retained for compatibility/history, not claimed
as the current contract. `tests/fixtures/webhook_v54.json` is the current official
webhook example from the v5.4 ZIP, including its illustrative `xxx` document data.

## Actual drift fixed

- Reuse the spec already proposed in sync PR #1; add five address-book operations.
  Read responses use exported `RestAddressBookEntry`; write keywords mirror every
  top-level request property, including `additionalField1`.
- DELETE transport and HTTP 204 handling; existing error translation is retained.
- JSON import fields: `Order.userid` (branch-only customer contact assignment),
  `Destination.delivery_date_from`, `Document.category`. New defaulted fields are
  appended so existing positional construction and omitted-field payloads survive.
- Webhook destination `date`, `fromTime`, `toTime`; task-result `documents` retains
  each document's `name` and `base64EncodedDocument` as dictionaries.
- Refresh the order-update status documentation for the published enum expansion.

## Automation prerequisites already supported on main

| Need | Existing public interface / semantics |
| --- | --- |
| Status/substatus writes | `update_order(status=..., substatus_no=...)`; zero substatus clears. Current enum: quote, open, signed-off, checked; server enforces transitions. |
| Rate activation | `sales_rates` / `purchase_rates` dictionaries pass `rateNo` and boolean `isActive`; price is not mandatory for an activation-only update. Response `RestRate.is_active` distinguishes omitted/unknown (`None`) from false. Already added in main commit `5b8aeda`; an older consumer pin is not an SDK gap. |
| Unit pricing | `ratePerUnit` is the price per unit, not a calculated total. No invented writes for quantity, order hours or loading/unloading time. |
| Pagination | List methods expose `page`; `PagedResponse` exposes `links`, `meta`, `has_next`; existing iterators advance pages. |
| Product/fleet identifiers | `get_products()` / `get_product(product_no)`, `get_fleet()` / `get_fleet_vehicle(fleet_no)`; order attributes carry `product_no` / `fleet_no`; `update_order(fleet_no=...)` is already supported. JSON import uses `productno` / `fleetno`. |

No customer/product heuristic, hourly-pricing policy, tenant-specific status workaround,
48-hour review rule, or HourRegistration integration belongs in this SDK change.

## Contract limitations

Address-book POST/PUT document only 422 responses and DELETE has no response schema.
Writes therefore return raw JSON (`Any`) or `None` for HTTP 204; there is deliberately
no guessed success response model. GET responses are typed and tested against official
examples. A malformed non-204 JSON response still raises `EasyTransAPIError`.

POST marks `customerNo` required but describes it as branch-only. The SDK exposes an
optional keyword for customer-account use and leaves account validation to the server;
no assertion is made about untested runtime acceptance. New REST writes are immediate:
JSON-import `default_mode="test"` never makes REST writes safe/test-only.

No authenticated/live integration tests were run. Mocked tests prove serialization,
parsing, pagination and exception mapping, not tenant deployment behavior. The existing
carrier-account order endpoint allow-list remains unchanged; this is not a claim that
every previously planned endpoint has been implemented.
