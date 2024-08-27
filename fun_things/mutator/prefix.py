from .payload import Payload


class Prefix(Payload):
    proceed: bool = True
    """
    If the process should proceed to call the function.
    """
