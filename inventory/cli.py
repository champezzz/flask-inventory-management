"""Command-line interface for the inventory API.

Start the server first (python -m inventory.app), then e.g.:
    python -m inventory.cli list
    python -m inventory.cli add "Oat Milk" --price 3.5 --quantity 10
"""
import argparse
import json
import sys

import requests

DEFAULT_URL = "http://127.0.0.1:5000"


def build_parser():
    p = argparse.ArgumentParser(prog="inventory", description="Inventory CLI")
    p.add_argument("--url", default=DEFAULT_URL, help="API base URL")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all items")

    g = sub.add_parser("get", help="Show one item")
    g.add_argument("id", type=int)

    s = sub.add_parser("search", help="Search inventory by name/brand")
    s.add_argument("term")

    a = sub.add_parser("add", help="Add an item manually")
    a.add_argument("name")
    a.add_argument("--brand", default="")
    a.add_argument("--barcode", default="")
    a.add_argument("--price", type=float, default=0)
    a.add_argument("--quantity", type=int, default=0)

    u = sub.add_parser("update", help="Update fields of an item")
    u.add_argument("id", type=int)
    u.add_argument("--name")
    u.add_argument("--brand")
    u.add_argument("--price", type=float)
    u.add_argument("--quantity", type=int)

    d = sub.add_parser("delete", help="Delete an item")
    d.add_argument("id", type=int)

    f = sub.add_parser("lookup", help="Look up a product on OpenFoodFacts")
    f.add_argument("--barcode")
    f.add_argument("--name")

    i = sub.add_parser("import", help="Fetch a product by barcode and add it")
    i.add_argument("barcode")
    i.add_argument("--price", type=float, default=0)
    i.add_argument("--quantity", type=int, default=0)
    return p


def run(args):
    """Send the request for the parsed args; return the requests.Response."""
    base = args.url.rstrip("/")
    c = args.command
    if c == "list":
        return requests.get(f"{base}/inventory", timeout=15)
    if c == "get":
        return requests.get(f"{base}/inventory/{args.id}", timeout=15)
    if c == "search":
        return requests.get(f"{base}/inventory/search", params={"q": args.term}, timeout=15)
    if c == "add":
        body = {"name": args.name, "brand": args.brand, "barcode": args.barcode,
                "price": args.price, "quantity": args.quantity}
        return requests.post(f"{base}/inventory", json=body, timeout=15)
    if c == "update":
        body = {k: getattr(args, k) for k in ("name", "brand", "price", "quantity")
                if getattr(args, k) is not None}
        return requests.patch(f"{base}/inventory/{args.id}", json=body, timeout=15)
    if c == "delete":
        return requests.delete(f"{base}/inventory/{args.id}", timeout=15)
    if c == "lookup":
        if args.barcode:
            return requests.get(f"{base}/external/barcode/{args.barcode}", timeout=15)
        if args.name:
            return requests.get(f"{base}/external/search", params={"name": args.name}, timeout=15)
        raise ValueError("lookup needs --barcode or --name")
    if c == "import":
        body = {"price": args.price, "quantity": args.quantity}
        return requests.post(f"{base}/inventory/import/{args.barcode}", json=body, timeout=15)
    raise ValueError(f"unknown command {c}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        res = run(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except requests.ConnectionError:
        print(f"Error: cannot reach API at {args.url}. Is the server running?", file=sys.stderr)
        return 1
    print(json.dumps(res.json(), indent=2))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
