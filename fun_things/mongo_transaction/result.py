"""
MongoDB transaction result handling.

This module provides classes and utilities for representing and formatting
MongoDB transaction operation results.
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from pymongo import MongoClient
from pymongo.results import (
    BulkWriteResult,
    ClientBulkWriteResult,
    DeleteResult,
    InsertManyResult,
    InsertOneResult,
    UpdateResult,
)


@dataclass(frozen=True)
class MongoTransactionResult:
    """
    Represents the result of a MongoDB operation with session tracking.

    This immutable dataclass encapsulates the results of MongoDB operations
    executed within a transaction, including success status and any errors.

    Attributes:
        mongo (MongoClient): The MongoDB client used for the operation.
        results (List[Union[...]]): List of operation results from the session.
        ok (bool): Whether the operation completed successfully.
        error (Optional[Exception]): Any exception that occurred during the operation.
    """

    mongo: MongoClient
    results: List[
        Union[
            UpdateResult,
            DeleteResult,
            InsertOneResult,
            InsertManyResult,
            BulkWriteResult,
        ]
    ]
    ok: bool
    error: Optional[Exception]

    def __pretty(self, value):
        """
        Format a MongoDB operation result for human-readable display.

        Args:
            value: A pymongo operation result object.

        Returns:
            str: Human-readable formatted string describing the operation result.
        """
        if isinstance(value, UpdateResult):
            upserted_part = (
                f", {value.upserted_id} upserted"
                if value.upserted_id is not None
                else ""
            )

            return f"UpdateResult: {value.matched_count} matched, {value.modified_count} modified{upserted_part}"

        if isinstance(value, DeleteResult):
            return f"DeleteResult: {value.deleted_count} deleted"

        if isinstance(value, InsertOneResult):
            return f"InsertOneResult: {value.inserted_id} inserted"

        if isinstance(value, InsertManyResult):
            return f"InsertManyResult: {value.inserted_ids} inserted"

        if isinstance(value, BulkWriteResult):
            return f"BulkWriteResult: {value.matched_count} matched, {value.modified_count} modified, {value.upserted_count} upserted, {value.deleted_count} deleted"

        if isinstance(value, ClientBulkWriteResult):
            return f"ClientBulkWriteResult: {value.matched_count} matched, {value.modified_count} modified, {value.upserted_count} upserted, {value.deleted_count} deleted"

        return value

    @property
    def pretty(self):
        """
        Get pretty-formatted representations of all operation results.

        Returns:
            List[str]: List of human-readable strings describing each operation result.
        """
        return [self.__pretty(value) for value in self.results]
