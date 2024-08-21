from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .mongo_annotation import MongoAnnotation


@dataclass(frozen=True)
class MongoAnnotationPayload:
    annotation: "MongoAnnotation"
    key: str
    value: Any
