from unittest.mock import MagicMock, patch

import pytest
import requests

from inventory import openfoodfacts as off
from inventory.app import create_app

PRODUCT_JSON = {
    "status": 1,
    "product": {
        "code": "3017620422003",
        "product_name": "Nutella",
        "brands": "Ferrero, Other",
        "ingredients_text": "Sugar, palm oil, hazelnuts",
    },
}


def fake_response(json_data, status=200):
    res = MagicMock()
    res.json.return_value = json_data
    res.raise_for_status.side_effect = (
        requests.HTTPError("boom") if status >= 400 else None
    )
    return res


@pytest.fixture
def client():
    return create_app().test_client()


# ---- client module ----
@patch("inventory.openfoodfacts.requests.get")
def test_fetch_by_barcode_success(mock_get):
    mock_get.return_value = fake_response(PRODUCT_JSON)
    product = off.fetch_by_barcode("3017620422003")
    assert product == {
        "name": "Nutella", "brand": "Ferrero",
        "barcode": "3017620422003", "ingredients": "Sugar, palm oil, hazelnuts",
    }


@patch("inventory.openfoodfacts.requests.get")
def test_fetch_by_barcode_not_found(mock_get):
    mock_get.return_value = fake_response({"status": 0})
    assert off.fetch_by_barcode("000") is None


@patch("inventory.openfoodfacts.requests.get")
def test_fetch_by_barcode_network_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("down")
    with pytest.raises(off.ExternalAPIError):
        off.fetch_by_barcode("123")


@patch("inventory.openfoodfacts.requests.get")
def test_search_by_name(mock_get):
    mock_get.return_value = fake_response({"products": [PRODUCT_JSON["product"]] * 3})
    assert len(off.search_by_name("nutella", limit=2)) == 2


@patch("inventory.openfoodfacts.requests.get")
def test_search_http_error(mock_get):
    mock_get.return_value = fake_response({}, status=500)
    with pytest.raises(off.ExternalAPIError):
        off.search_by_name("x")


# ---- API routes ----
@patch("inventory.app.off.fetch_by_barcode")
def test_route_external_barcode(mock_fetch, client):
    mock_fetch.return_value = {"name": "Nutella"}
    assert client.get("/external/barcode/123").get_json() == {"name": "Nutella"}


@patch("inventory.app.off.fetch_by_barcode", return_value=None)
def test_route_external_barcode_404(_, client):
    assert client.get("/external/barcode/123").status_code == 404


@patch("inventory.app.off.fetch_by_barcode", side_effect=off.ExternalAPIError("x"))
def test_route_external_barcode_502(_, client):
    assert client.get("/external/barcode/123").status_code == 502


@patch("inventory.app.off.search_by_name", return_value=[{"name": "A"}])
def test_route_external_search(_, client):
    assert client.get("/external/search?name=a").get_json() == [{"name": "A"}]


def test_route_external_search_requires_name(client):
    assert client.get("/external/search").status_code == 400


@patch("inventory.app.off.fetch_by_barcode")
def test_import_adds_to_inventory(mock_fetch, client):
    mock_fetch.return_value = {"name": "Nutella", "brand": "Ferrero",
                               "barcode": "123", "ingredients": "x"}
    res = client.post("/inventory/import/123", json={"price": 4.5, "quantity": 20})
    assert res.status_code == 201
    assert res.get_json()["quantity"] == 20
    assert client.get("/inventory").get_json()[0]["name"] == "Nutella"


@patch("inventory.app.off.fetch_by_barcode", return_value=None)
def test_import_unknown_barcode(_, client):
    assert client.post("/inventory/import/000").status_code == 404
    assert client.get("/inventory").get_json() == []
