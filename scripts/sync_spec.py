#!/usr/bin/env python3
"""
Sync the vendored EasyTrans OpenAPI spec with the one EasyTrans publishes.

    python scripts/sync_spec.py            # fetch, update file if changed, print diff
    python scripts/sync_spec.py --check    # exit 1 if the published spec differs
    python scripts/sync_spec.py --url URL  # use another environment's spec

The published spec is at ``https://www.mytrans3.nl/abtransport/api/docs.openapi``
(no authentication needed). The vendored copy lives in
``EasyTrans Documentation/openapi.yaml`` and drives ``tests/test_spec_contract.py``.

The diff is a readable summary of API-level changes (operations, parameters,
request-body and response fields, types, enums), written as Markdown so the
scheduled GitHub workflow can drop it straight into a pull request. Pass
``--summary FILE`` to also write it to a file.

Exit codes: 0 = up to date or updated, 1 = differs (with ``--check``),
2 = fetch/parse error.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import yaml  # type: ignore[import-untyped]

DEFAULT_URL = "https://www.mytrans3.nl/abtransport/api/docs.openapi"
REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "EasyTrans Documentation" / "openapi.yaml"
HTTP_METHODS = ("get", "post", "put", "patch", "delete")

OpKey = Tuple[str, str]
FieldInfo = Tuple[Optional[str], Optional[Tuple[Any, ...]]]


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def fetch(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "easytrans-sdk-spec-sync"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        body: bytes = resp.read()
    return body.decode("utf-8")


# ---------------------------------------------------------------------------
# Flattening a spec into comparable pieces
# ---------------------------------------------------------------------------


def operations(spec: Dict[str, Any]) -> Dict[OpKey, Dict[str, Any]]:
    ops: Dict[OpKey, Dict[str, Any]] = {}
    for path, item in (spec.get("paths") or {}).items():
        for method, op in item.items():
            if method in HTTP_METHODS:
                ops[(method.upper(), path)] = op
    return ops


def _resolve(
    schema: Any, root: Dict[str, Any], seen: Tuple[str, ...]
) -> Tuple[Any, Tuple[str, ...]]:
    """Follow local ``$ref`` pointers; returns (schema, refs followed so far)."""
    while isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen or not ref.startswith("#/"):
            return {}, seen
        seen = seen + (ref,)
        node: Any = root
        for part in ref[2:].split("/"):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        schema = node
    return schema, seen


def flatten_schema(
    schema: Any,
    prefix: str = "",
    root: Optional[Dict[str, Any]] = None,
    _seen: Tuple[str, ...] = (),
) -> Dict[str, FieldInfo]:
    """Map dotted field paths (``[]`` for arrays) to (type, enum)."""
    out: Dict[str, FieldInfo] = {}
    schema, _seen = _resolve(schema, root or {}, _seen)
    if not isinstance(schema, dict):
        return out
    for part in schema.get("allOf") or []:
        out.update(flatten_schema(part, prefix, root, _seen))
    if "items" in schema:
        out.update(flatten_schema(schema["items"], prefix + "[]", root, _seen))
    for name, sub in (schema.get("properties") or {}).items():
        path = f"{prefix}.{name}" if prefix else name
        resolved, sub_seen = _resolve(sub, root or {}, _seen)
        resolved = resolved if isinstance(resolved, dict) else {}
        enum = tuple(resolved["enum"]) if resolved.get("enum") else None
        out[path] = (resolved.get("type"), enum)
        out.update(flatten_schema(resolved, path, root, sub_seen))
    return out


def query_params(op: Dict[str, Any]) -> Dict[str, Optional[str]]:
    return {
        p["name"]: (p.get("schema") or {}).get("type")
        for p in op.get("parameters", [])
        if p.get("in") == "query"
    }


def request_fields(op: Dict[str, Any], root: Dict[str, Any]) -> Dict[str, FieldInfo]:
    content = (op.get("requestBody") or {}).get("content") or {}
    schema = (content.get("application/json") or {}).get("schema")
    return flatten_schema(schema, root=root)


def response_fields(op: Dict[str, Any], root: Dict[str, Any]) -> Dict[str, FieldInfo]:
    responses = op.get("responses") or {}
    out: Dict[str, FieldInfo] = {}
    for code, resp in responses.items():
        schema = (((resp or {}).get("content") or {}).get("application/json") or {}).get("schema")
        for path, info in flatten_schema(schema, root=root).items():
            out[f"{code}:{path}"] = info
    return out


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------


def _fmt_info(info: FieldInfo) -> str:
    typ, enum = info
    text = typ or "?"
    if enum:
        text += " enum[" + ", ".join(map(str, enum)) + "]"
    return text


def _diff_maps(
    label: str,
    old: Dict[str, Any],
    new: Dict[str, Any],
    fmt: Callable[[Any], str] = str,
) -> List[str]:
    lines: List[str] = []
    for name in sorted(set(new) - set(old)):
        lines.append(f"  - {label} **added**: `{name}` ({fmt(new[name])})")
    for name in sorted(set(old) - set(new)):
        lines.append(f"  - {label} **removed**: `{name}`")
    for name in sorted(set(old) & set(new)):
        if old[name] != new[name]:
            lines.append(f"  - {label} changed: `{name}` {fmt(old[name])} → {fmt(new[name])}")
    return lines


def diff_specs(old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
    """Return Markdown lines describing API-level differences."""
    lines: List[str] = []
    if old.get("openapi") != new.get("openapi"):
        lines.append(f"- `openapi`: {old.get('openapi')} → {new.get('openapi')}")
    old_ver = (old.get("info") or {}).get("version")
    new_ver = (new.get("info") or {}).get("version")
    if old_ver != new_ver:
        lines.append(f"- `info.version`: {old_ver} → {new_ver}")

    old_ops, new_ops = operations(old), operations(new)
    for key in sorted(set(new_ops) - set(old_ops), key=lambda k: (k[1], k[0])):
        lines.append(f"- **New operation** `{key[0]} {key[1]}` — {new_ops[key].get('summary', '')}")
    for key in sorted(set(old_ops) - set(new_ops), key=lambda k: (k[1], k[0])):
        lines.append(f"- **Removed operation** `{key[0]} {key[1]}`")

    for key in sorted(set(old_ops) & set(new_ops), key=lambda k: (k[1], k[0])):
        o, n = old_ops[key], new_ops[key]
        changes: List[str] = []
        changes += _diff_maps("query param", query_params(o), query_params(n))
        changes += _diff_maps(
            "request field", request_fields(o, old), request_fields(n, new), _fmt_info
        )
        changes += _diff_maps(
            "response field", response_fields(o, old), response_fields(n, new), _fmt_info
        )
        if changes:
            lines.append(f"- `{key[0]} {key[1]}`")
            lines.extend(changes)
    return lines


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _write_summary(path: Optional[str], lines: Iterable[str]) -> None:
    if path:
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--check", action="store_true", help="don't write; exit 1 on drift")
    parser.add_argument("--summary", help="also write the Markdown diff to this file")
    args = parser.parse_args(argv)

    try:
        new_text = fetch(args.url)
        new_spec = yaml.safe_load(new_text)
        if not isinstance(new_spec, dict) or "paths" not in new_spec:
            raise ValueError("response is not an OpenAPI document")
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not fetch/parse {args.url}: {exc}", file=sys.stderr)
        return 2

    old_text = args.spec.read_text(encoding="utf-8") if args.spec.exists() else ""
    if new_text == old_text:
        print("Spec is up to date.")
        _write_summary(args.summary, [])
        return 0

    old_spec = yaml.safe_load(old_text) if old_text else {}
    lines = diff_specs(old_spec or {}, new_spec)
    if not lines:
        lines = ["- Text-only changes (descriptions/examples); no API-level differences."]
    report = ["## EasyTrans OpenAPI spec changes", "", f"Source: {args.url}", ""] + lines
    print("\n".join(report))
    _write_summary(args.summary, report)

    if args.check:
        return 1
    args.spec.write_text(new_text, encoding="utf-8")
    print(f"\nUpdated {args.spec.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
