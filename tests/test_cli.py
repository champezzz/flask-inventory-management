from unittest.mock import MagicMock, patch

import requests

from inventory import cli


def ok(data, status=200):
    r = MagicMock()
    r.json.return_value = data
    r.ok = status < 400
    return r


@patch("inventory.cli.requests.get")
def test_list(mock_get, capsys):
    mock_get.return_value = ok([{"id": 1, "name": "Rice"}])
    assert cli.main(["list"]) == 0
    assert "Rice" in capsys.readouterr().out
    assert mock_get.call_args[0][0].endswith("/inventory")


@patch("inventory.cli.requests.post")
def test_add(mock_post, capsys):
    mock_post.return_value = ok({"id": 1, "name": "Milk"}, 201)
    assert cli.main(["add", "Milk", "--price", "2.5", "--quantity", "4"]) == 0
    body = mock_post.call_args.kwargs["json"]
    assert body["name"] == "Milk" and body["price"] == 2.5 and body["quantity"] == 4


@patch("inventory.cli.requests.patch")
def test_update_only_sends_given_fields(mock_patch):
    mock_patch.return_value = ok({"id": 1})
    cli.main(["update", "1", "--quantity", "9"])
    assert mock_patch.call_args.kwargs["json"] == {"quantity": 9}


@patch("inventory.cli.requests.delete")
def test_delete(mock_delete):
    mock_delete.return_value = ok({"message": "item deleted"})
    assert cli.main(["delete", "3"]) == 0
    assert mock_delete.call_args[0][0].endswith("/inventory/3")


@patch("inventory.cli.requests.get")
def test_get_not_found_returns_error_code(mock_get):
    mock_get.return_value = ok({"error": "item not found"}, 404)
    assert cli.main(["get", "9"]) == 1


@patch("inventory.cli.requests.get")
def test_search(mock_get):
    mock_get.return_value = ok([])
    cli.main(["search", "rice"])
    assert mock_get.call_args.kwargs["params"] == {"q": "rice"}


@patch("inventory.cli.requests.get")
def test_lookup_by_barcode_and_name(mock_get):
    mock_get.return_value = ok({})
    cli.main(["lookup", "--barcode", "123"])
    assert mock_get.call_args[0][0].endswith("/external/barcode/123")
    cli.main(["lookup", "--name", "nutella"])
    assert mock_get.call_args.kwargs["params"] == {"name": "nutella"}


def test_lookup_requires_argument(capsys):
    assert cli.main(["lookup"]) == 2
    assert "needs --barcode or --name" in capsys.readouterr().err


@patch("inventory.cli.requests.post")
def test_import(mock_post):
    mock_post.return_value = ok({"id": 1}, 201)
    assert cli.main(["import", "123", "--quantity", "5"]) == 0
    assert mock_post.call_args[0][0].endswith("/inventory/import/123")
    assert mock_post.call_args.kwargs["json"]["quantity"] == 5


@patch("inventory.cli.requests.get", side_effect=requests.ConnectionError)
def test_server_down(_, capsys):
    assert cli.main(["list"]) == 1
    assert "cannot reach API" in capsys.readouterr().err
