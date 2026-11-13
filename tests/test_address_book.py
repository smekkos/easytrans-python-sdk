"""Offline address-book compatibility against the published response examples."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import responses
import yaml

from easytrans import EasyTransClient

BASE = "https://example.invalid/demo/api/v1"
SPEC = yaml.safe_load(
    (Path(__file__).parents[1] / "EasyTrans Documentation/openapi.yaml").read_text()
)


@pytest.fixture
def client():
    return EasyTransClient("example.invalid", "demo", "dummy", "dummy")


def example(path):
    return SPEC["paths"][path]["get"]["responses"][200]["content"]["application/json"]["schema"][
        "example"
    ]


@responses.activate
def test_address_book_reads_parse_examples_and_query_parameters(client):
    from easytrans import RestAddressBookEntry

    responses.get(BASE + "/address-book", json=example("/v1/address-book"))
    result = client.get_address_book(
        filter={"addressNo": {"gte": 0}, "customerNo": 2001}, sort="-company", page=2
    )
    entry = result.data[0]
    assert isinstance(entry, RestAddressBookEntry)
    assert entry.id == entry.address_no == 1892
    assert entry.customer_no == 2001
    assert entry.company == "EasyTrans Software B.V."
    assert entry.opening_hours.from_time == "09:00"
    assert result.meta.total == 1
    assert result.has_next is False
    assert parse_qs(urlparse(responses.calls[0].request.url).query) == {
        "filter[addressNo][gte]": ["0"],
        "filter[customerNo]": ["2001"],
        "sort": ["-company"],
        "page": ["2"],
    }
    responses.get(BASE + "/address-book/1892", json=example("/v1/address-book/{addressNo}"))
    assert client.get_address_book_entry(1892) == entry
    assert RestAddressBookEntry.from_dict({"id": 1, "attributes": {}}).opening_hours is None


@pytest.mark.parametrize(
    "method,address_no", [("create_address_book_entry", None), ("update_address_book_entry", 1892)]
)
@responses.activate
def test_address_book_writes_preserve_partial_payloads(client, method, address_no):
    verb = "POST" if address_no is None else "PUT"
    url = BASE + "/address-book" + ("" if address_no is None else "/1892")
    # The spec has no success schema for these operations. Raw JSON must survive.
    responses.add(verb, url, json={"unmodelled": "result"}, status=200)
    hours = {"from": None, "to": "17:00"}
    args = [] if address_no is None else [address_no]
    result = getattr(client, method)(*args, customer_no=0, notes="", opening_hours=hours)
    assert result == {"unmodelled": "result"}
    assert json.loads(responses.calls[0].request.body) == {
        "customerNo": 0,
        "notes": "",
        "openingHours": hours,
    }
    assert hours == {"from": None, "to": "17:00"}


@responses.activate
def test_delete_address_book_entry_accepts_no_content(client):
    responses.delete(BASE + "/address-book/1892", status=204)
    assert client.delete_address_book_entry(1892) is None
    assert responses.calls[0].request.body is None


@responses.activate
def test_address_book_write_accepts_no_content(client):
    responses.post(BASE + "/address-book", status=204)
    assert client.create_address_book_entry(customer_no=2001) is None


@pytest.mark.parametrize(
    "method,path,args",
    [
        ("get_address_book_entry", "/address-book/1892", [1892]),
        ("create_address_book_entry", "/address-book", []),
        ("update_address_book_entry", "/address-book/1892", [1892]),
        ("delete_address_book_entry", "/address-book/1892", [1892]),
    ],
)
@pytest.mark.parametrize("status", [401, 404, 422, 429])
@responses.activate
def test_address_book_errors_use_existing_exceptions(client, method, path, args, status):
    from easytrans.exceptions import (
        EasyTransAuthError,
        EasyTransNotFoundError,
        EasyTransRateLimitError,
        EasyTransValidationError,
    )

    exceptions = {
        401: EasyTransAuthError,
        404: EasyTransNotFoundError,
        422: EasyTransValidationError,
        429: EasyTransRateLimitError,
    }
    verb = {"get": "GET", "create": "POST", "update": "PUT", "delete": "DELETE"}[
        method.split("_")[0]
    ]
    responses.add(verb, BASE + path, json={"message": "Rejected"}, status=status)
    with pytest.raises(exceptions[status]):
        getattr(client, method)(*args)


@pytest.mark.parametrize(
    "method,address_no", [("create_address_book_entry", None), ("update_address_book_entry", 1892)]
)
@responses.activate
def test_every_address_book_request_field_reaches_the_wire(client, method, address_no):
    schema = SPEC["paths"]["/v1/address-book"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    body = {key: field["example"] for key, field in schema["properties"].items()}
    body["openingHours"] = {"from": "09:00", "to": None}
    body["additionalField1"] = "extra"
    aliases = {
        "customerNo": "customer_no",
        "openingHours": "opening_hours",
        "additionalField1": "additional_field1",
    }
    kwargs = {aliases.get(key, key): value for key, value in body.items()}
    responses.add(
        "POST" if address_no is None else "PUT",
        BASE + "/address-book" + ("" if address_no is None else "/1892"),
        json={},
    )
    getattr(client, method)(*([] if address_no is None else [address_no]), **kwargs)
    assert json.loads(responses.calls[0].request.body) == body


@responses.activate
def test_address_book_next_page_uses_standard_metadata(client):
    from copy import deepcopy

    payload = deepcopy(example("/v1/address-book"))
    payload["links"]["next"] = BASE + "/address-book?page=2"
    payload["meta"].update(current_page=1, last_page=2, total=2)
    responses.get(BASE + "/address-book", json=payload)
    response = client.get_address_book()
    assert response.has_next is True
    assert response.meta.current_page + 1 == 2


@responses.activate
def test_delete_rejects_malformed_json_in_non_204_success(client):
    from easytrans.exceptions import EasyTransAPIError

    responses.delete(BASE + "/address-book/1892", body="not JSON", status=200)
    with pytest.raises(EasyTransAPIError, match="Invalid JSON"):
        client.delete_address_book_entry(1892)
