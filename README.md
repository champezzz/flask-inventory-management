# Inventory Management System

A small admin portal for a retail company: a **Flask REST API** for inventory CRUD,
**OpenFoodFacts** integration for product details, a **command-line interface**, and a
**pytest** suite. Inventory is stored in memory (a list of dicts), so data resets when the
server restarts.

## Project structure

```
inventory/
  app.py            Flask app factory + all routes
  store.py          In-memory "database" (list of dicts)
  openfoodfacts.py  OpenFoodFacts API client
  cli.py            Command-line interface (talks to the API)
tests/
  test_api.py       CRUD + search route tests
  test_external.py  OpenFoodFacts client + route tests (HTTP mocked)
  test_cli.py       CLI tests (HTTP mocked)
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the API

```bash
python -m inventory.app        # http://127.0.0.1:5000
```

## API endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/inventory` | List all items |
| GET | `/inventory/<id>` | Get one item |
| GET | `/inventory/search?q=term` | Search by name or brand |
| POST | `/inventory` | Create item (`name` required) |
| PATCH | `/inventory/<id>` | Update any fields |
| DELETE | `/inventory/<id>` | Delete item |
| GET | `/external/barcode/<barcode>` | Look up product on OpenFoodFacts |
| GET | `/external/search?name=term` | Search OpenFoodFacts by name |
| POST | `/inventory/import/<barcode>` | Fetch by barcode **and add to inventory** (optional JSON `price`, `quantity`) |

Item fields: `id`, `name`, `brand`, `barcode`, `price`, `quantity`, `ingredients`.
Errors return JSON `{"error": "..."}` with 400 (bad input), 404 (not found) or 502
(OpenFoodFacts unreachable).

## CLI usage

With the server running, in another terminal:

```bash
python -m inventory.cli list
python -m inventory.cli add "Oat Milk" --brand Oatly --price 3.5 --quantity 10
python -m inventory.cli get 1
python -m inventory.cli update 1 --quantity 25
python -m inventory.cli search oat
python -m inventory.cli delete 1

# OpenFoodFacts
python -m inventory.cli lookup --barcode 3017620422003
python -m inventory.cli lookup --name nutella
python -m inventory.cli import 3017620422003 --price 4.99 --quantity 30
```

Use `--url http://host:port` to point the CLI at a different server.

## Tests

```bash
python -m pytest -v
```

External HTTP calls are mocked, so tests run offline and are deterministic.

## Git workflow

Each feature was built on its own branch (`feature/crud-api`, `feature/external-api`,
`feature/cli`, `docs/readme`), merged into `main` via pull request, and the branch deleted.

## Author
Osteen - Moringa School

## Author
Osteen 
