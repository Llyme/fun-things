from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Tuple,
    TypeVar,
)

T = TypeVar("T")


class Categorizer(Generic[T]):
    delimiter = "_"
    """
    The separator when splitting values into keywords.
    """

    def __keyword_sorting_order(self, keyword: str):
        try:
            # Numbers are less prioritized.
            int(keyword)

            return 1
        except:
            pass

        # The rest are prioritized.
        return 2

    def __sorting_order(self, item: Tuple[str, List[T]]):
        return len(item[1]) * self.__keyword_sorting_order(item[0])

    def __by_keywords(
        self,
        values: Iterable[T],
    ):
        """
        Groups the values by keywords.
        """
        result: Dict[str, List[T]] = {}
        values = filter(
            lambda value: value not in self.__ignored_values,
            values,
        )

        for raw_value in values:
            value = self.__get_value(raw_value)
            keywords = value.split(self.delimiter)

            for keyword in keywords:
                if keyword not in result:
                    result[keyword] = []

                result[keyword].append(raw_value)

        return sorted(
            result.items(),
            key=self.__sorting_order,
        )

    def __get_array(
        self,
        grouped: List[Tuple[str, List[T]]],
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

            return sorted(
                result,
                key=self.__get_value,
            )

        all_one = map(
            lambda value: len(value[1]) == 1,
            grouped,
        )
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

            return sorted(
                result,
                key=self.__get_value,
            )

        return None

    def __normalize(self, keyword: str, items: Any):
        while len(items) == 1 and isinstance(items, dict):
            # Normalize singular sub-categories containing
            # only 1 sub-category.

            sub_keyword, sub_category = next(
                iter(
                    items.items(),
                )
            )

            if sub_keyword != "*":
                keyword = f"{sub_keyword}_{keyword}"

            items = sub_category

            continue

        return keyword, items

    def __categorize(
        self,
        values: Iterable[T],
        ignored_keywords: List[str],
    ):
        grouped = self.__by_keywords(values)
        all_one = self.__get_array(grouped)

        if all_one != None:
            return all_one

        result = {}
        others = []

        while len(grouped) > 0:
            keyword, children = grouped.pop()

            if keyword in ignored_keywords:
                continue

            children = [
                *filter(
                    lambda child: child not in self.__ignored_values,
                    children,
                )
            ]

            if children == []:
                # Nothing to categorize here.
                continue

            category = self.__categorize(
                children,
                [*ignored_keywords, keyword],
            )

            if category == []:
                continue

            if category == {}:
                continue

            keyword, category = self.__normalize(
                keyword,
                category,
            )

            if len(category) == 1 and isinstance(category, list):
                # Category is an array with only 1 item.
                # Put in 'others'.
                others.append(category[0])
                continue

            # Result

            result[keyword] = category

            for item in category:
                self.__ignored_values.add(item)

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
        self.__ignored_values: set = set()
        self.__values: Dict[T, str] = {}
        self.__value_selector = value_selector

        result = self.__categorize(values, [])

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
