"""
MongoDB transaction operations.

This module provides dataclasses and operations for executing MongoDB
transactions with various operation types.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pymongo import DeleteMany, DeleteOne, InsertOne, ReplaceOne, UpdateMany, UpdateOne
from pymongo.client_session import ClientSession
from pymongo.collection import Collection

if TYPE_CHECKING:
    from .builder import MongoTransactionBuilder


@dataclass
class MongoTransaction:
    """
    Represents a single MongoDB transaction operation.

    This class encapsulates a MongoDB operation (insert, update, delete, etc.)
    to be executed within a session, along with associated metadata.

    Attributes:
        builder (MongoTransactionBuilder): Reference to the parent transaction builder.
        collection (Collection): MongoDB collection to operate on.
        requests (list): List of pymongo operation requests.
        messages (List[str]): Log messages associated with this transaction.
    """

    builder: "MongoTransactionBuilder"
    collection: Collection
    ordered: bool
    requests: list
    messages: list

    @property
    def name(self):
        """
        Get the fully qualified name of the collection.

        Returns:
            str: Collection name in format "database.collection".
        """
        return f"{self.collection.database.name}.{self.collection.name}"

    def do(self, session: ClientSession):
        """
        Execute the transaction operation within a MongoDB session.

        For single operations, uses specific pymongo methods (insert_one, update_one, etc.).
        For multiple operations, uses bulk_write for efficiency.

        Args:
            session (ClientSession): MongoDB client session for transaction context.

        Returns:
            tuple: A tuple of (operation_name, result) where operation_name is a string
                   describing the operation type and result is the pymongo operation result.

        Raises:
            ValueError: If an unknown request type is encountered.
        """
        if len(self.requests) == 1:
            request = self.requests[0]

            if isinstance(request, InsertOne):
                return "insert_one", self.collection.insert_one(
                    document=request._doc,
                    session=session,
                )

            if isinstance(request, UpdateOne):
                return "update_one", self.collection.update_one(
                    filter=request._filter,
                    update=request._doc,
                    upsert=request._upsert or False,
                    session=session,
                )

            if isinstance(request, UpdateMany):
                return "update_many", self.collection.update_many(
                    filter=request._filter,
                    update=request._doc,
                    upsert=request._upsert or False,
                    session=session,
                )

            if isinstance(request, DeleteOne):
                return "delete_one", self.collection.delete_one(
                    filter=request._filter,
                    session=session,
                )

            if isinstance(request, DeleteMany):
                return "delete_many", self.collection.delete_many(
                    filter=request._filter,
                    session=session,
                )

            if isinstance(request, ReplaceOne):
                return "replace_one", self.collection.replace_one(
                    filter=request._filter,
                    replacement=request._doc,
                    upsert=request._upsert or False,
                    session=session,
                )

            raise ValueError(
                f"Unknown request type: {type(request)}",
            )

        return "bulk_write", self.collection.bulk_write(
            requests=self.requests,
            session=session,
            ordered=self.ordered,
        )
