from datetime import datetime
from enum import Enum
from json import JSONEncoder

try:
    from bson import ObjectId

except Exception:
    ObjectId = None


class GenericJSONEncoder(JSONEncoder):
    def default(self, o):
        if ObjectId and isinstance(o, ObjectId):
            return str(o)

        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, Enum):
            return o.value

        return JSONEncoder.default(self, o)
