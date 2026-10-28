"""Read only primitive values from the application's previous local format."""

import pickle
from pathlib import Path


class PrimitiveUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError("Legacy settings cannot contain executable globals")

    def persistent_load(self, pid):
        raise ValueError("Legacy settings cannot contain persistent references")


def load_legacy(path: Path) -> dict:
    try:
        with path.open("rb") as stream:
            value = PrimitiveUnpickler(stream).load()
        if not isinstance(value, dict):
            raise ValueError("Legacy settings must be an object")
        return value
    except (pickle.UnpicklingError, EOFError, TypeError) as exc:
        raise ValueError("Invalid legacy settings") from exc
