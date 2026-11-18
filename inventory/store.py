"""In-memory "database" (a list of dicts) for inventory items."""

ALLOWED_FIELDS = {"name", "brand", "barcode", "price", "quantity", "ingredients"}


class InventoryStore:
    def __init__(self):
        self.items = []
        self._next_id = 1

    def all(self):
        return list(self.items)

    def get(self, item_id):
        return next((i for i in self.items if i["id"] == item_id), None)

    def add(self, data):
        item = {
            "id": self._next_id,
            "name": data["name"],
            "brand": data.get("brand", ""),
            "barcode": data.get("barcode", ""),
            "price": float(data.get("price", 0)),
            "quantity": int(data.get("quantity", 0)),
            "ingredients": data.get("ingredients", ""),
        }
        self._next_id += 1
        self.items.append(item)
        return item

    def update(self, item_id, data):
        item = self.get(item_id)
        if item is None:
            return None
        for key, value in data.items():
            if key in ALLOWED_FIELDS:
                if key == "price":
                    value = float(value)
                elif key == "quantity":
                    value = int(value)
                item[key] = value
        return item

    def delete(self, item_id):
        item = self.get(item_id)
        if item is None:
            return False
        self.items.remove(item)
        return True

    def search(self, term):
        term = term.lower()
        return [
            i for i in self.items
            if term in i["name"].lower() or term in i["brand"].lower()
        ]
