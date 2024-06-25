from typing import Dict, Iterable, List, Optional, Tuple


class Categorizer:
    delimiter = "_"
    """
    The separator when splitting values into keywords.
    """

    def __order(self, item: Tuple[str, List[str]]):
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
        values: Iterable[str],
    ) -> List[Tuple[Optional[str], List[str]]]:
        """
        Group & sorts the values.

        Keywords already visited are ignored.

        Values already categorized are marked as 'others'.
        """
        result: Dict[str, list] = {}
        values = filter(
            lambda value: value not in self.__ignored_values,
            values,
        )
        others = []

        for value in values:
            keywords = value.split(self.delimiter)
            ok = False

            for keyword in keywords:
                if keyword in self.__ignored_keywords:
                    continue

                if keyword not in result:
                    result[keyword] = []

                result[keyword].append(value)

                ok = True

            if not ok:
                # Value was ignored.
                # Mark as 'others'.
                others.append(value)

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
        grouped: List[Tuple[Optional[str], List[str]]],
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

            return [*sorted(result)]

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

            return [*sorted(result)]

    def __categorize(self, values: Iterable[str]):
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

            children = list(
                filter(
                    lambda child: child not in self.__ignored_values,
                    children,
                )
            )

            if children == []:
                # Nothing to categorize here.
                continue

            self.__ignored_keywords.add(keyword)

            category = self.__categorize(children)

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
                others.append(category[0])
                continue

            # Result

            result[keyword] = category

        if len(others) > 0:
            result["*"] = [*sorted(others)]

        return result

    def categorize(self, values: Iterable[str]) -> dict:
        self.__ignored_keywords: set = set()
        self.__ignored_values: set = set()

        result = self.__categorize(values)

        if isinstance(result, list):
            return {
                "*": result,
            }

        return result


def categorizer(values: Iterable[str]):
    return Categorizer().categorize(values)
