"""Flask REST API: CRUD routes for inventory."""
from flask import Flask, jsonify, request

from . import openfoodfacts as off
from .store import InventoryStore


def create_app(store=None):
    app = Flask(__name__)
    app.config["STORE"] = store or InventoryStore()

    def db():
        return app.config["STORE"]

    def validate(data, require_name):
        """Return an error message, or None if the payload is valid."""
        if not isinstance(data, dict):
            return "JSON body required"
        if require_name and not data.get("name"):
            return "'name' is required"
        try:
            if "price" in data and float(data["price"]) < 0:
                return "'price' must be >= 0"
            if "quantity" in data and int(data["quantity"]) < 0:
                return "'quantity' must be >= 0"
        except (TypeError, ValueError):
            return "'price' must be a number and 'quantity' an integer"
        return None

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # ---- Read ----
    @app.get("/inventory")
    def list_items():
        return jsonify(db().all())

    @app.get("/inventory/search")
    def search_items():
        term = request.args.get("q", "")
        if not term:
            return jsonify({"error": "query parameter 'q' is required"}), 400
        return jsonify(db().search(term))

    @app.get("/inventory/<int:item_id>")
    def get_item(item_id):
        item = db().get(item_id)
        if item is None:
            return jsonify({"error": "item not found"}), 404
        return jsonify(item)

    # ---- Create ----
    @app.post("/inventory")
    def create_item():
        data = request.get_json(silent=True)
        error = validate(data, require_name=True)
        if error:
            return jsonify({"error": error}), 400
        return jsonify(db().add(data)), 201

    # ---- Update ----
    @app.patch("/inventory/<int:item_id>")
    def update_item(item_id):
        data = request.get_json(silent=True)
        error = validate(data, require_name=False)
        if error:
            return jsonify({"error": error}), 400
        item = db().update(item_id, data)
        if item is None:
            return jsonify({"error": "item not found"}), 404
        return jsonify(item)

    # ---- Delete ----
    @app.delete("/inventory/<int:item_id>")
    def delete_item(item_id):
        if not db().delete(item_id):
            return jsonify({"error": "item not found"}), 404
        return jsonify({"message": "item deleted"})

    # ---- External API (OpenFoodFacts) ----
    @app.get("/external/barcode/<barcode>")
    def external_barcode(barcode):
        try:
            product = off.fetch_by_barcode(barcode)
        except off.ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502
        if product is None:
            return jsonify({"error": "product not found"}), 404
        return jsonify(product)

    @app.get("/external/search")
    def external_search():
        name = request.args.get("name", "")
        if not name:
            return jsonify({"error": "query parameter 'name' is required"}), 400
        try:
            return jsonify(off.search_by_name(name))
        except off.ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502

    @app.post("/inventory/import/<barcode>")
    def import_from_barcode(barcode):
        """Fetch a product by barcode and add it to the inventory."""
        body = request.get_json(silent=True) or {}
        error = validate(body, require_name=False)
        if error:
            return jsonify({"error": error}), 400
        try:
            product = off.fetch_by_barcode(barcode)
        except off.ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502
        if product is None:
            return jsonify({"error": "product not found"}), 404
        product["price"] = body.get("price", 0)
        product["quantity"] = body.get("quantity", 0)
        return jsonify(db().add(product)), 201

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
