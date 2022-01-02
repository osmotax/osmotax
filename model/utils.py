import json
from datetime import datetime


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "attribute_values"):
            return obj.attribute_values
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
