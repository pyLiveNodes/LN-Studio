import importlib

def noop(*args, **kwargs):
    pass

def is_installed(name):
    return importlib.util.find_spec(name) is not None