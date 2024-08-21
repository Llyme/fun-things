from dataclasses import dataclass
from typing import Callable, Optional
from pydantic import BaseModel  # type: ignore
from .mongo_annotation_post_processor import MongoAnnotationPostProcessor
from .mongo_annotation_payload import MongoAnnotationPayload


def ignore_null(payload: MongoAnnotationPayload):
    return payload.value != None


def default_post_processor(
    post_processor: MongoAnnotationPostProcessor,
):
    query = post_processor.query
    annotation = post_processor.payload.annotation
    key = post_processor.payload.key
    value = post_processor.payload.value

    if annotation.set:
        if "$set" not in query:
            query["$set"] = {}

        query["$set"][key] = value

    if annotation.set_on_insert:
        if "$setOnInsert" not in query:
            query["$setOnInsert"] = {}

        query["$setOnInsert"][key] = value

    return query


@dataclass(frozen=True)
class MongoAnnotation:
    set: bool = True
    set_on_insert: bool = False
    condition: Optional[
        Callable[
            [MongoAnnotationPayload],
            bool,
        ],
    ] = None
    post_processor: Callable[
        [MongoAnnotationPostProcessor],
        dict,
    ] = default_post_processor

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
        query = {}

        for key, value in dump.items():
            annotation = cls.__get_annotation(
                key,
                annotations,
            )

            if annotation.condition != None:
                if not annotation.condition(value):
                    continue

            annotation.post_processor(
                MongoAnnotationPostProcessor(
                    payload=MongoAnnotationPayload(
                        annotation=annotation,  # type: ignore
                        key=key,
                        value=value,
                    ),
                    query=query,
                ),
            )

        return query


MongoAnnotation(
    condition=ignore_null,
)
