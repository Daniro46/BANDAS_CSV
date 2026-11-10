"""Helper modules of the BANDAS .mdb -> .csv converter (see ../00_bandas_mdb_to_csv.py).

The modules are numbered in the order the data goes through them (01_paths.py,
02_access_reader.py, ...). A module name that starts with a digit cannot be
used in `from ... import ...`, so they are imported with load().
"""

from importlib import import_module


def load(module, *names):
    """Import `names` from a numbered module of this package, e.g. load("03_flags", "add_flag").

    Returns the object itself for one name, or a tuple for several.
    """
    loaded = import_module(f"{__name__}.{module}")
    objects = tuple(getattr(loaded, name) for name in names)
    return objects[0] if len(objects) == 1 else objects
