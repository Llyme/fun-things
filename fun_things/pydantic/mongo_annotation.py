from dataclasses import dataclass
from typing import final
from pydantic import BaseModel  # type: ignore


@dataclass(frozen=True)
class MongoAnnotation:
    set: bool = True
    set_on_insert: bool = False

    @classmethod
    def __get_annotation(cls, key, annotations):
        if key not in annotations:
            return cls

        metadata = annotations[key].__dict__

        if "__metadata__" not in metadata:
            return cls

        metadata = metadata["__metadata__"]

        for annotation in metadata:
            if isinstance(annotation, MongoAnnotation):
                return annotation

        return cls

    @classmethod
    def query_update(cls, model: BaseModel):
        """
        Returns a query object for updating in MongoDB.
        """
        dump = model.model_dump()
        annotations = model.__class__.__dict__["__annotations__"]
        _set = {}
        _set_on_insert = {}

        for key, value in dump.items():
            annotation = cls.__get_annotation(
                key,
                annotations,
            )

            if annotation.set:
                _set[key] = value

            if annotation.set_on_insert:
                _set_on_insert[key] = value

        return {
            "$set": _set,
            "$setOnInsert": _set_on_insert,
        }
