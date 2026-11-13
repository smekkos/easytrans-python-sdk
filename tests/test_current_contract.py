"""Characterization: automation prerequisites already implemented on main."""

import json
from pathlib import Path

import pytest
import responses
import yaml

from easytrans import EasyTransClient

SPEC = yaml.safe_load(
    (Path(__file__).parents[1] / "EasyTrans Documentation/openapi.yaml").read_text()
)
BASE = "https://example.invalid/demo/api/v1"
STATUS_SCHEMA = SPEC["paths"]["/v1/orders/{orderNo}"]["put"]["requestBody"]["content"][
    "application/json"
]["schema"]["properties"]["status"]


def example(path):
    return SPEC["paths"][path]["get"]["responses"][200]["content"]["application/json"]["schema"][
        "example"
    ]


@pytest.mark.parametrize("status", STATUS_SCHEMA["enum"])
@responses.activate
def test_every_published_status_and_zero_substatus_are_forwarded(status):
    responses.put(BASE + "/orders/1234", json=example("/v1/orders/{orderNo}"))
    client = EasyTransClient("example.invalid", "demo", "dummy", "dummy")
    client.update_order(1234, status=status, substatus_no=0, fleet_no=0)
    assert json.loads(responses.calls[0].request.body) == {
        "status": status,
        "substatusNo": 0,
        "fleetNo": 0,
    }


@pytest.mark.parametrize(
    "path,method,field",
    [
        ("/v1/products/{productNo}", "get_product", "product_no"),
        ("/v1/fleet/{fleetNo}", "get_fleet_vehicle", "fleet_no"),
    ],
)
@responses.activate
def test_product_and_fleet_identifiers_are_preserved(path, method, field):
    payload = example(path)
    number = payload["data"]["attributes"]["productNo" if field == "product_no" else "fleetNo"]
    url = BASE + path[len("/v1") :].split("{")[0] + str(number)
    responses.get(url, json=payload)
    client = EasyTransClient("example.invalid", "demo", "dummy", "dummy")
    assert getattr(getattr(client, method)(number), field) == number
