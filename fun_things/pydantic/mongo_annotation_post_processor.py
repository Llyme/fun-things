from dataclasses import dataclass
from .mongo_annotation_payload import MongoAnnotationPayload


@dataclass(frozen=True)
class MongoAnnotationPostProcessor:
    payload: MongoAnnotationPayload
    query: dict
