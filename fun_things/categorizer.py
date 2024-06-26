from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
)

T = TypeVar("T")


class Categorizer(Generic[T]):
    delimiter = "_"
    """
    The separator when splitting values into keywords.
    """

    def __order(self, item: Tuple[str, List[T]]):
        """
        The sorting order.
        """
        try:
            # Numbers are less prioritized.
            int(item[0])

            return 0
        except:
            pass

        if item[0] == None:
            # Non-categorized are last.
            return -99

        # The rest are prioritized.
        return 99

    def __group(
        self,
        values: Iterable[T],
    ) -> List[Tuple[Optional[str], List[T]]]:
        """
        Group & sorts the values.

        Keywords already visited are ignored.

        Values already categorized are marked as 'others'.
        """
        result: Dict[str, List[T]] = {}
        values = filter(
            lambda value: value not in self.__ignored_values,
            values,
        )
        others: List[T] = []

        for raw_value in values:
            value = self.__get_value(raw_value)
            keywords = value.split(self.delimiter)
            ok = False

            for keyword in keywords:
                if keyword in self.__ignored_keywords:
                    continue

                if keyword not in result:
                    result[keyword] = []

                result[keyword].append(raw_value)

                ok = True

            if not ok:
                # Value was ignored.
                # Mark as 'others'.
                others.append(raw_value)

        sorted_result = sorted(
            result.items(),
            key=lambda v: len(v[1]),
        )
        sorted_result = sorted(
            sorted_result,
            key=self.__order,
        )

        if len(others) == 0:
            return sorted_result  # type: ignore

        return [
            (None, others),
            *sorted_result,
        ]

    def __get_array(
        self,
        grouped: List[Tuple[Optional[str], List[T]]],
    ):
        """
        Check if the categories can be a single array.
        """

        if len(grouped) == 1:
            # There's only 1 category.
            # Transform into an array.
            result = []

            for value in grouped[0][1]:
                if value not in self.__ignored_values:
                    self.__ignored_values.add(value)
                    result.append(value)

            return [*sorted(result, key=self.__get_value)]

        all_one = map(lambda v: len(v[1]) == 1, grouped)
        all_one = all(all_one)

        if all_one:
            # All categories only have 1 item.
            # Combine them.
            result = []

            for _, (value,) in grouped:
                if value in self.__ignored_values:
                    continue

                self.__ignored_values.add(value)
                result.append(value)

            return [*sorted(result, key=self.__get_value)]

    def __categorize(self, values: Iterable[T]):
        grouped = self.__group(values)
        all_one = self.__get_array(grouped)

        if all_one != None:
            return all_one

        result = {}
        others = []

        while len(grouped) > 0:
            keyword, children = grouped.pop()

            if keyword in self.__ignored_keywords:
                continue

            children = [
                *filter(
                    lambda child: child not in self.__ignored_values,
                    children,
                ),
                *others,
            ]

            if children == []:
                # Nothing to categorize here.
                continue

            self.__ignored_keywords.add(keyword)

            category = self.__categorize(children)

            if category == []:
                continue

            if category == {}:
                continue

            # Category Normalization

            for _ in range(10):
                if len(category) == 1 and isinstance(category, dict):
                    # Normalize singular sub-categories containing
                    # only 1 sub-category.

                    sub_keyword, sub_category = next(
                        iter(
                            category.items(),
                        )
                    )

                    if sub_keyword != "*":
                        keyword = f"{sub_keyword}_{keyword}"

                    category = sub_category

                    continue

                break

            if len(category) == 1 and isinstance(category, list):
                # Category is an array with only 1 item.
                # Put in 'others'.
                # self.__ignored_keywords.remove(keyword)
                others.append(category[0])
                continue

            # Result

            result[keyword] = category

        others = [
            *filter(
                lambda value: value in self.__ignored_values,
                others,
            )
        ]

        if len(others) > 0:
            result["*"] = [
                *sorted(
                    others,
                    key=self.__get_value,
                )
            ]

        return result

    def categorize(
        self,
        values: Iterable[T],
        value_selector: Callable[[T], str],
    ) -> dict:
        self.__ignored_keywords: set = set()
        self.__ignored_values: set = set()
        self.__values: Dict[T, str] = {}
        self.__value_selector = value_selector

        result = self.__categorize(values)

        if isinstance(result, list):
            return {
                "*": result,
            }

        return result

    def __get_value(self, key: T):
        if key not in self.__values:
            self.__values[key] = self.__value_selector(key)

        return self.__values[key]


def categorizer(
    values: Iterable[T],
    value_selector: Callable[[T], str] = lambda v: v,  # type: ignore
):
    return Categorizer().categorize(values, value_selector)
