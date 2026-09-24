"""Unit tests for scripts/sync_spec.py (spec diffing; no network)."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("yaml")

_SPEC = importlib.util.spec_from_file_location(
    "sync_spec", Path(__file__).resolve().parent.parent / "scripts" / "sync_spec.py"
)
sync_spec = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sync_spec)


def _spec(attrs, code=200, extra_paths=None, components=None, query=None):
    op = {
        "summary": "Get product",
        "parameters": [
            {"in": "query", "name": n, "schema": {"type": "string"}} for n in (query or [])
        ],
        "responses": {
            code: {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "attributes": {"type": "object", "properties": attrs}
                                    },
                                }
                            },
                        }
                    }
                }
            }
        },
    }
    spec = {"openapi": "3.0.3", "paths": {"/v1/products/{productNo}": {"get": op}}}
    spec["paths"].update(extra_paths or {})
    if components:
        spec["components"] = {"schemas": components}
    return spec


def test_identical_specs_have_no_diff():
    s = _spec({"productNo": {"type": "integer"}})
    assert sync_spec.diff_specs(s, s) == []


def test_added_and_removed_response_field():
    old = _spec({"productNo": {"type": "integer"}, "legacy": {"type": "string"}})
    new = _spec({"productNo": {"type": "integer"}, "vat": {"type": "string"}})
    text = "\n".join(sync_spec.diff_specs(old, new))
    assert "response field **added**: `200:data.attributes.vat`" in text
    assert "response field **removed**: `200:data.attributes.legacy`" in text


def test_type_and_enum_change():
    old = _spec({"status": {"type": "string", "enum": ["a"]}})
    new = _spec({"status": {"type": "string", "enum": ["a", "b"]}})
    text = "\n".join(sync_spec.diff_specs(old, new))
    assert "changed: `200:data.attributes.status` string enum[a] → string enum[a, b]" in text


def test_new_operation_and_query_param():
    old = _spec({}, query=["include_customer"])
    new = _spec(
        {},
        query=["include_customer", "include_deleted"],
        extra_paths={"/v1/things": {"get": {"summary": "List things", "responses": {}}}},
    )
    text = "\n".join(sync_spec.diff_specs(old, new))
    assert "**New operation** `GET /v1/things` — List things" in text
    assert "query param **added**: `include_deleted`" in text


def test_response_code_int_vs_str_is_not_a_change():
    """YAML may key responses by 200 (int) or '200' (str)."""
    attrs = {"productNo": {"type": "integer"}}
    assert sync_spec.diff_specs(_spec(attrs, code=200), _spec(attrs, code="200")) == []


def test_refs_are_resolved():
    """A $ref'd schema must compare equal to the same schema inlined."""
    inline = _spec({"productNo": {"type": "integer"}})
    with_ref = _spec(
        {"productNo": {"$ref": "#/components/schemas/No"}},
        components={"No": {"type": "integer"}},
    )
    assert sync_spec.diff_specs(with_ref, inline) == []


def test_recursive_ref_does_not_loop():
    node = {
        "type": "object",
        "properties": {"child": {"$ref": "#/components/schemas/Node"}},
    }
    spec = _spec({"tree": {"$ref": "#/components/schemas/Node"}}, components={"Node": node})
    assert sync_spec.diff_specs(spec, spec) == []
