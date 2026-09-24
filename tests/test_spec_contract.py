"""
Contract tests: the SDK against the official EasyTrans OpenAPI spec.

The spec is published by EasyTrans at
``https://www.mytrans3.nl/abtransport/api/docs.openapi`` and vendored in
``EasyTrans Documentation/openapi.yaml`` (refresh it with
``python scripts/sync_spec.py``).

These tests fail when the spec contains something the SDK does not handle:

* an operation without a client method,
* a response field (from the spec example) that no model reads,
* a request-body field or ``include_*`` query parameter that the client
  method does not expose as a keyword argument.

Intentional gaps go in the allow-lists below, each with a reason. When the
spec changes, a failure here is the to-do list for the SDK update.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pytest

yaml = pytest.importorskip("yaml")

from easytrans import EasyTransClient  # noqa: E402
from easytrans.rest_models import (  # noqa: E402
    PagedResponse,
    RestCarrier,
    RestCustomer,
    RestFleetVehicle,
    RestInvoice,
    RestOrder,
    RestPackageType,
    RestProduct,
    RestSubstatus,
    RestVehicleType,
)

SPEC_PATH = Path(__file__).resolve().parent.parent / "EasyTrans Documentation" / "openapi.yaml"

# (METHOD, path) -> (client method name or None, response item model, is_list)
OPERATIONS: Dict[Tuple[str, str], Tuple[Optional[str], Any, bool]] = {
    ("GET", "/v1/orders"): ("get_orders", RestOrder, True),
    ("GET", "/v1/orders/{orderNo}"): ("get_order", RestOrder, False),
    ("PUT", "/v1/orders/{orderNo}"): ("update_order", RestOrder, False),
    ("POST", "/v1/orders/{orderNo}/approve-quote"): ("approve_quote", RestOrder, False),
    ("GET", "/v1/products"): ("get_products", RestProduct, True),
    ("GET", "/v1/products/{productNo}"): ("get_product", RestProduct, False),
    ("GET", "/v1/substatuses"): ("get_substatuses", RestSubstatus, True),
    ("GET", "/v1/substatuses/{substatusNo}"): ("get_substatus", RestSubstatus, False),
    ("GET", "/v1/packagetypes"): ("get_package_types", RestPackageType, True),
    ("GET", "/v1/packagetypes/{packageTypeNo}"): ("get_package_type", RestPackageType, False),
    ("GET", "/v1/vehicletypes"): ("get_vehicle_types", RestVehicleType, True),
    ("GET", "/v1/vehicletypes/{vehicleTypeNo}"): ("get_vehicle_type", RestVehicleType, False),
    ("GET", "/v1/customers"): ("get_customers", RestCustomer, True),
    ("GET", "/v1/customers/{customerNo}"): ("get_customer", RestCustomer, False),
    ("PUT", "/v1/customers/{customerNo}"): ("update_customer", RestCustomer, False),
    ("GET", "/v1/carriers"): ("get_carriers", RestCarrier, True),
    ("GET", "/v1/carriers/{carrierNo}"): ("get_carrier", RestCarrier, False),
    ("GET", "/v1/fleet"): ("get_fleet", RestFleetVehicle, True),
    ("GET", "/v1/fleet/{fleetNo}"): ("get_fleet_vehicle", RestFleetVehicle, False),
    ("GET", "/v1/invoices"): ("get_invoices", RestInvoice, True),
    ("GET", "/v1/invoices/{invoiceId}"): ("get_invoice", RestInvoice, False),
    # Carrier-account endpoints: responses parse with RestOrder, but the
    # client has no methods for them yet (planned).
    ("GET", "/v1/carrier/orders"): (None, RestOrder, True),
    ("GET", "/v1/carrier/orders/{orderNo}"): (None, RestOrder, False),
    ("PUT", "/v1/carrier/orders/{orderNo}"): (None, RestOrder, False),
}

# Response fields that are intentionally not mapped onto a model attribute.
# Paths use "data" / "data[]" as root and "[]" for list items. JSON:API
# ``type`` discriminators of resources are ignored automatically.
UNMAPPED_RESPONSE_FIELDS: Set[str] = {
    # Laravel's numbered page links (meta.links[]); navigation uses the
    # top-level links.first/prev/next/last and meta.current_page instead.
    "meta.links",
    "meta.path",
    # Passed through untouched as raw dicts on RestDestination.documents,
    # so every key is available to callers without a typed model.
    "data.attributes.destinations[].documents",
    "data[].attributes.destinations[].documents",
}

# Query parameters that are deliberately not exposed as keyword arguments.
UNMAPPED_QUERY_PARAMS: Set[Tuple[str, str]] = set()

# Request-body fields that are deliberately not exposed as keyword arguments.
UNMAPPED_BODY_FIELDS: Set[Tuple[str, str]] = set()

# The client uses short names for some include_* flags.
QUERY_PARAM_ALIASES = {
    "include_invoice": "include_invoice_pdf",
}


# ---------------------------------------------------------------------------
# Spec helpers
# ---------------------------------------------------------------------------


def _load_spec() -> Dict[str, Any]:
    with SPEC_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


SPEC = _load_spec()


def _spec_operations() -> Dict[Tuple[str, str], Dict[str, Any]]:
    ops = {}
    for path, item in SPEC["paths"].items():
        for method, op in item.items():
            if method in ("get", "post", "put", "patch", "delete"):
                ops[(method.upper(), path)] = op
    return ops


SPEC_OPS = _spec_operations()


def _success_example(op: Dict[str, Any]) -> Dict[str, Any]:
    responses = op["responses"]
    resp = responses.get(200) or responses.get("200")
    return resp["content"]["application/json"]["schema"]["example"]


def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# ---------------------------------------------------------------------------
# Key-access recorder
# ---------------------------------------------------------------------------


class _Recorder(dict):
    """A dict that records every key read through get / [] / in."""

    def __init__(self, data: Dict[str, Any], prefix: str, seen: Set[str]):
        super().__init__({k: _wrap(v, _join(prefix, k), seen) for k, v in data.items()})
        self._prefix = prefix
        self._seen = seen

    def _mark(self, key: Any) -> None:
        self._seen.add(_join(self._prefix, key))

    def get(self, key: Any, default: Any = None) -> Any:
        self._mark(key)
        return super().get(key, default)

    def __getitem__(self, key: Any) -> Any:
        self._mark(key)
        return super().__getitem__(key)

    def __contains__(self, key: Any) -> bool:
        self._mark(key)
        return super().__contains__(key)

    def values(self):  # type: ignore[override]
        # Iterating values (e.g. contacts keyed by id) reads every key.
        for key in self.keys():
            self._mark(key)
        return super().values()


def _join(prefix: str, key: Any) -> str:
    return f"{prefix}.{key}" if prefix else str(key)


def _wrap(value: Any, path: str, seen: Set[str]) -> Any:
    if isinstance(value, dict):
        return _Recorder(value, path, seen)
    if isinstance(value, list):
        return [_wrap(v, path + "[]", seen) for v in value]
    return value


def _example_paths(value: Any, prefix: str = "") -> Iterable[str]:
    """Every key path present in an example payload."""
    if isinstance(value, dict):
        for key, sub in value.items():
            path = _join(prefix, key)
            yield path
            yield from _example_paths(sub, path)
    elif isinstance(value, list):
        for item in value:
            yield from _example_paths(item, prefix + "[]")


def _is_allowed(path: str, all_paths: Set[str]) -> bool:
    parent, _, leaf = path.rpartition(".")
    if leaf == "type" and f"{parent}.attributes" in all_paths:
        return True  # JSON:API resource type discriminator
    return any(
        path == allowed or path.startswith(allowed + ".") or path.startswith(allowed + "[]")
        for allowed in UNMAPPED_RESPONSE_FIELDS
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_every_spec_operation_is_known():
    """A new endpoint in the spec must be added to OPERATIONS (and the SDK)."""
    unknown = sorted(set(SPEC_OPS) - set(OPERATIONS))
    assert not unknown, f"Spec operations not handled by the SDK: {unknown}"


def test_no_stale_operations():
    """An endpoint removed from the spec must be removed from OPERATIONS."""
    stale = sorted(set(OPERATIONS) - set(SPEC_OPS))
    assert not stale, f"Operations no longer in the spec: {stale}"


@pytest.mark.parametrize(
    "key",
    [k for k, v in OPERATIONS.items() if v[0] is not None],
    ids=lambda k: f"{k[0]} {k[1]}",
)
def test_client_method_exists(key):
    method_name = OPERATIONS[key][0]
    assert callable(getattr(EasyTransClient, method_name, None)), method_name


@pytest.mark.parametrize("key", sorted(OPERATIONS), ids=lambda k: f"{k[0]} {k[1]}")
def test_response_example_fully_mapped(key):
    """Every field in the spec's response example is read by the model."""
    _, item_cls, is_list = OPERATIONS[key]
    example = _success_example(SPEC_OPS[key])
    seen: Set[str] = set()

    if is_list:
        result = PagedResponse.from_dict(_Recorder(example, "", seen), item_cls)
        assert len(result.data) == len(example["data"])
    else:
        seen.add("data")
        result = item_cls.from_dict(_Recorder(example["data"], "data", seen))
        assert isinstance(result, item_cls)

    all_paths = set(_example_paths(example))
    unmapped = sorted(p for p in all_paths - seen if not _is_allowed(p, all_paths))
    assert (
        not unmapped
    ), f"{key[0]} {key[1]}: spec fields not read by {item_cls.__name__}: {unmapped}"


@pytest.mark.parametrize(
    "key",
    [k for k, v in OPERATIONS.items() if v[0] is not None],
    ids=lambda k: f"{k[0]} {k[1]}",
)
def test_include_query_params_exposed(key):
    """Every include_* / sort query parameter is a keyword argument."""
    method = getattr(EasyTransClient, OPERATIONS[key][0])
    kwargs = set(inspect.signature(method).parameters)
    missing: List[str] = []
    for param in SPEC_OPS[key].get("parameters", []):
        name = param["name"]
        if param["in"] != "query" or name.startswith("filter"):
            continue
        if (key[1], name) in UNMAPPED_QUERY_PARAMS:
            continue
        if QUERY_PARAM_ALIASES.get(name, name) not in kwargs:
            missing.append(name)
    assert not missing, f"{method.__name__}() lacks query params: {missing}"


@pytest.mark.parametrize(
    "key",
    [k for k, v in OPERATIONS.items() if v[0] and SPEC_OPS[k].get("requestBody")],
    ids=lambda k: f"{k[0]} {k[1]}",
)
def test_request_body_fields_exposed(key):
    """Every top-level request-body field is a keyword argument."""
    method = getattr(EasyTransClient, OPERATIONS[key][0])
    kwargs = set(inspect.signature(method).parameters)
    schema = SPEC_OPS[key]["requestBody"]["content"]["application/json"]["schema"]
    missing = sorted(
        name
        for name in schema.get("properties", {})
        if _camel_to_snake(name) not in kwargs and (key[1], name) not in UNMAPPED_BODY_FIELDS
    )
    assert not missing, f"{method.__name__}() lacks body fields: {missing}"


def test_recorder_detects_unread_keys():
    """Self-check: the recorder must not mark keys the model never reads."""
    seen: Set[str] = set()
    RestProduct.from_dict(
        _Recorder({"id": 1, "attributes": {"productNo": 1, "bogus": 1}}, "data", seen)
    )
    assert "data.attributes.productNo" in seen
    assert "data.attributes.bogus" not in seen
