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


@pytest.mark.parametrize("zero", [False, True])
@responses.activate
def test_order_metrics_round_trip(zero):
    values = (0, 0, 0, 0, 0, 0.0) if zero else (120, 100, 3, 30, 45, 6.75)
    distance, purchase, stops, waiting, loading, hours = values
    metrics = dict(zip(("distance", "distancePurchase", "stops", "waitingTime",
                        "loadingUnloadingTime", "hours"), values))
    destination = {"stopNo": 2, "carrierNotes": "Delivered next door"}
    responses.put(BASE + "/orders/1234", json={"data": {"attributes": metrics}})
    client = EasyTransClient("example.invalid", "demo", "dummy", "dummy")
    order = client.update_order(1234, distance=distance, distance_purchase=purchase,
                                stops=stops, waiting_time=waiting, loading_unloading_time=loading,
                                hours=hours, destinations=[destination])
    assert json.loads(responses.calls[0].request.body) == {**metrics, "destinations": [destination]}
    assert order.attributes.distance_purchase == purchase
    assert order.attributes.hours == hours
