import pytest

from inventory.app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def make(client, **kw):
    payload = {"name": "Oat Milk", "brand": "Oatly", "price": 3.5, "quantity": 10}
    payload.update(kw)
    return client.post("/inventory", json=payload)


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_list_empty(client):
    assert client.get("/inventory").get_json() == []


def test_create_item(client):
    res = make(client)
    assert res.status_code == 201
    body = res.get_json()
    assert body["id"] == 1 and body["name"] == "Oat Milk" and body["quantity"] == 10


def test_create_requires_name(client):
    assert client.post("/inventory", json={"price": 1}).status_code == 400


def test_create_rejects_bad_values(client):
    assert make(client, price=-1).status_code == 400
    assert make(client, quantity="abc").status_code == 400


def test_create_without_json(client):
    assert client.post("/inventory").status_code == 400


def test_get_item(client):
    make(client)
    assert client.get("/inventory/1").get_json()["name"] == "Oat Milk"


def test_get_missing_item(client):
    assert client.get("/inventory/99").status_code == 404


def test_list_returns_all(client):
    make(client)
    make(client, name="Rice")
    assert len(client.get("/inventory").get_json()) == 2


def test_patch_item(client):
    make(client)
    res = client.patch("/inventory/1", json={"quantity": 4, "price": 2.25})
    assert res.status_code == 200
    assert res.get_json()["quantity"] == 4
    assert res.get_json()["price"] == 2.25
    assert res.get_json()["name"] == "Oat Milk"


def test_patch_ignores_unknown_fields_and_id(client):
    make(client)
    body = client.patch("/inventory/1", json={"id": 50, "bogus": 1}).get_json()
    assert body["id"] == 1 and "bogus" not in body


def test_patch_missing_item(client):
    assert client.patch("/inventory/9", json={"quantity": 1}).status_code == 404


def test_patch_invalid_value(client):
    make(client)
    assert client.patch("/inventory/1", json={"quantity": -5}).status_code == 400


def test_delete_item(client):
    make(client)
    assert client.delete("/inventory/1").status_code == 200
    assert client.get("/inventory/1").status_code == 404


def test_delete_missing_item(client):
    assert client.delete("/inventory/1").status_code == 404


def test_search(client):
    make(client)
    make(client, name="Basmati Rice", brand="Tilda")
    assert len(client.get("/inventory/search?q=rice").get_json()) == 1
    assert len(client.get("/inventory/search?q=oatly").get_json()) == 1
    assert client.get("/inventory/search?q=zzz").get_json() == []


def test_search_requires_query(client):
    assert client.get("/inventory/search").status_code == 400
