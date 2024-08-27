from dataclasses import dataclass
from .payload import Payload


@dataclass
class Prefix(Payload):
    proceed: bool = True
    """
    If the process should proceed to call the function.
    """
