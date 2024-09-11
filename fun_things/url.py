from typing import Union
from urllib.parse import ParseResult, quote, unquote, urlparse, urlunparse


def re_escape_special_chars(
    text: str,
    safe: str = "/",
):
    """
    Undoes the special character escaping and
    re-encodes the text.
    """
    for _ in range(10):
        new_text = unquote(text)

        if new_text == text:
            break

        text = new_text

    return quote(
        text,
        safe=safe,
    )


def re_escape_url(value: Union[str, ParseResult]):
    """
    Undoes the special character escaping and
    re-encodes the url.
    """
    try:
        url = value

        if isinstance(url, str):
            url = urlparse(url)

        url = url._replace(
            path=re_escape_special_chars(url.path, safe="/@"),
            params=re_escape_special_chars(url.params),
            query=re_escape_special_chars(url.query, safe="=&"),
            fragment=re_escape_special_chars(url.fragment),
        )

        return urlunparse(url)

    except:
        pass

    if isinstance(value, str):
        return value

    return urlunparse(value)
