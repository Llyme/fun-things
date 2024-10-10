def merge_dict(
    *dicts: dict,
    **kwargs,
):
    result = {}

    for dict in dicts:
        result.update(dict)

    result.update(kwargs)

    return result
