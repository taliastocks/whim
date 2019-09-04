try:
    import importlib.resources as importlib_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources


def get(path):
    return importlib_resources.open_binary(__name__, path)
