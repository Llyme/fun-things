from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Union,
)

from pymongo import (
    DeleteMany,
    DeleteOne,
    InsertOne,
    MongoClient,
    ReplaceOne,
    UpdateMany,
    UpdateOne,
)
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from fun_things import undefined
from fun_things.tenacity.generic_retry import generic_retry

from .result import MongoTransactionResult
from .transaction import MongoTransaction

_WriteOp = Union[
    InsertOne,
    DeleteOne,
    DeleteMany,
    ReplaceOne,
    UpdateOne,
    UpdateMany,
]

try:
    import tenacity
except Exception:
    tenacity = None


class MongoTransactionBuilder:
    """
    A builder class for creating and executing MongoDB transactions with optimization capabilities.

    This class allows you to build up a series of MongoDB operations and execute them
    within a single transaction. It provides optimization features to consolidate
    operations on the same collection and includes retry logic for transaction execution.

    Attributes:
        client (MongoClient): The MongoDB client instance
        transactions (List[MongoTransaction]): List of transactions to be executed
        fast_optimize (bool): Whether to use fast optimization mode
        on_write (Callable): Callback function executed after each transaction

    Example:
        >>> builder = MongoTransactionBuilder(client)
        >>> builder.do(collection, requests=InsertOne({"name": "John"}), message="Adding user")
        >>> result = builder.track()
    """

    def __init__(
        self,
        *,
        warning_logger: Optional[Callable[[str], Any]] = print,
        error_logger: Optional[Callable[[str], Any]] = print,
        info_logger: Optional[Callable[[str], Any]] = print,
        client: Union[MongoClient, Callable[..., MongoClient]],
        fast_optimize: bool = False,
        on_write: Callable[[MongoTransaction, str, Any], Any] = undefined,  # type: ignore
    ):
        """
        Initialize the MongoTransactionBuilder.

        Args:
            client (MongoClient): The MongoDB client to use for transactions
            fast_optimize (bool, optional): If True, uses fast optimization that groups
                operations by collection key. If False, uses sequential optimization.
                Defaults to False.
            on_write (Callable, optional): Custom callback function called after each
                transaction execution. Should accept (transaction, operation_name, result).
                If not provided, uses default logging behavior.
        """
        self.warning_logger = warning_logger
        self.error_logger = error_logger
        self.info_logger = info_logger
        self.client = client
        self.transactions: List[MongoTransaction] = []
        self.fast_optimize = fast_optimize
        self.__optimized = False

        if on_write is undefined:

            def fn(
                transaction: MongoTransaction,
                operation_name: str,
                result: Any,
            ):
                if not transaction.messages:
                    return result

                message = "\n".join(
                    text
                    for text in (
                        message(result)
                        if isinstance(message, Callable)
                        else str(message)
                        for message in transaction.messages
                    )
                    if text is not None
                )

                if not message:
                    return result

                if len(transaction.messages) > 1:
                    message = f"\n{message}"

                if self.info_logger:
                    self.info_logger(f"[{operation_name}@{transaction.name}] {message}")

                return result

            self.on_write = fn

        else:
            self.on_write = on_write

    @property
    def __client(self):
        return self.client() if callable(self.client) else self.client

    def __fast_optimize_transactions(self):
        """
        Fast optimization that groups transactions by collection key (database$collection).

        This method consolidates all operations targeting the same collection into a single
        transaction, regardless of their original order. This is more aggressive optimization
        but may change execution order.

        Note:
            This method is called automatically during execution and should not be called directly.
        """
        if self.__optimized:
            return

        new_transactions: Dict[str, MongoTransaction] = {}

        for transaction in self.transactions:
            if not transaction.requests:
                continue

            key = (
                f"{transaction.collection.database.name}${transaction.collection.name}"
            )

            if key in new_transactions:
                new_transactions[key].requests.extend(transaction.requests)
                new_transactions[key].messages.extend(transaction.messages)
                continue

            new_transactions[key] = transaction
            # Order is no longer important for fast optimization
            transaction.ordered = False

        self.transactions = list(new_transactions.values())

        self.__optimized = True

    def __optimize_transactions(self):
        """
        Sequential optimization that consolidates adjacent transactions on the same collection.

        This method merges consecutive transactions that target the same collection while
        preserving the original execution order. This is safer than fast optimization
        but may be less efficient.

        Note:
            This method is called automatically during execution and should not be called directly.
        """
        if self.__optimized:
            return

        new_transactions: List[MongoTransaction] = []

        for transaction in self.transactions:
            if not transaction.requests:
                continue

            if not new_transactions:
                new_transactions.append(transaction)
                continue

            current_transaction = new_transactions[-1]

            if (
                current_transaction.collection.database.name
                == transaction.collection.database.name
                and current_transaction.collection.name == transaction.collection.name
            ):
                current_transaction.requests.extend(transaction.requests)
                current_transaction.messages.extend(transaction.messages)
                continue

            new_transactions.append(transaction)

        self.transactions = new_transactions
        self.__optimized = True

    @contextmanager
    def __make_session(
        self,
        reraise=True,
    ):
        """
        Context manager for creating and managing MongoDB sessions with transactions.

        Args:
            reraise (bool, optional): Whether to reraise exceptions. Defaults to True.

        Yields:
            ClientSession: The MongoDB client session within a transaction context

        Note:
            This method handles transaction commit/abort automatically and should not
            be called directly.
        """
        with self.__client.start_session() as session:
            with session.start_transaction(
                # max_commit_time_ms=1_000,
            ):
                try:
                    yield session

                    session.commit_transaction()

                except Exception as e:
                    try:
                        session.abort_transaction()
                    except Exception:
                        pass

                    if reraise:
                        raise e

                    return

    def __track_session_internal(
        self,
        fn: Callable[
            [ClientSession],
            Generator[Any, Any, None],
        ],
    ):
        with self.__make_session() as session:
            result = [*fn(session)]

        return MongoTransactionResult(
            mongo=self.__client,
            results=result,
            ok=True,
            error=None,
        )

    def __track_session(
        self,
        fn: Callable[
            [ClientSession],
            Generator[Any, Any, None],
        ],
    ):
        """
        Execute a function within a MongoDB session and return the results.

        Args:
            fn (Callable): Function that takes a ClientSession and yields results

        Returns:
            MongoTransactionResult: Result object containing execution status and results

        Note:
            This method is used internally by track() and should not be called directly.
        """
        try:
            if tenacity:
                return generic_retry(
                    error_logger=self.error_logger,
                    warning_logger=self.warning_logger,
                    retry=tenacity.retry_if_not_exception_type(DuplicateKeyError),
                    retry_message=lambda _: "Transaction failed. Retrying...",
                )(self.__track_session_internal)(fn)

            return self.__track_session_internal(fn)

        except Exception as e:
            return MongoTransactionResult(
                mongo=self.__client,
                results=[],
                ok=False,
                error=e,
            )

    def do(
        self,
        collection: Collection,
        *,
        requests: Union[
            Sequence[_WriteOp],
            _WriteOp,
        ],
        message: Union[
            Any,
            Callable[..., Any],
            Sequence[Union[Any, Callable[..., Any]]],
        ] = None,
        ordered: bool = True,
    ):
        """
        Add a MongoDB operation to the transaction builder.

        Args:
            collection (Collection): The MongoDB collection to operate on
            requests (Union[InsertOne, DeleteOne, DeleteMany, ReplaceOne, UpdateOne, UpdateMany]):
                The MongoDB operation(s) to perform. Can be a single operation or a sequence.
            message (Optional[Union[Any, Sequence[Any]]], optional): Optional message(s) for
                logging purposes. If a sequence is provided, items will be joined with spaces.

        Returns:
            MongoTransactionBuilder: Returns self for method chaining

        Example:
            >>> builder.do(
            ...     collection=users_collection,
            ...     requests=InsertOne({"name": "John", "age": 30}),
            ...     message="Creating new user"
            ... )
        """
        self.__optimized = False

        messages = (
            list(message)
            if isinstance(message, Sequence) and not isinstance(message, str)
            else ([message] if message is not None else [])
        )

        self.transactions.append(
            MongoTransaction(
                builder=self,
                collection=collection,
                requests=list(requests)
                if isinstance(
                    requests,
                    Sequence,
                )
                else [requests],
                messages=messages,
                ordered=ordered,
            )
        )

        return self

    def clear(self):
        self.transactions = []

    def track(self):
        """
        Execute all queued transactions with retry logic and optimization.

        This method optimizes the transaction queue (either fast or sequential based on
        the fast_optimize setting), executes all transactions within a MongoDB session,
        and returns the results.

        Returns:
            MongoTransactionResult: Result object containing:
                - ok (bool): Whether all transactions succeeded
                - results (List[Any]): List of results from each transaction
                - error (Exception, optional): Exception if any transaction failed
                - mongo (MongoClient): Reference to the MongoDB client

        Raises:
            Exception: Any exception that occurs during transaction execution
            (after 3 retry attempts with exponential backoff)

        Example:
            >>> result = builder.track()
            >>> if result.ok:
            ...     print("All transactions completed successfully")
            ...     for res in result.results:
            ...         print(f"Operation result: {res}")
            >>> else:
            ...     print(f"Transaction failed: {result.error}")
        """

        def fn(session: ClientSession):
            if self.fast_optimize:
                self.__fast_optimize_transactions()
            else:
                self.__optimize_transactions()

            for transaction in self.transactions:
                operation_name, result = transaction.do(session)

                if self.on_write:
                    result = (
                        self.on_write(
                            transaction,
                            operation_name,
                            result,
                        )
                        or result
                    )

                yield result

        return self.__track_session(fn)
