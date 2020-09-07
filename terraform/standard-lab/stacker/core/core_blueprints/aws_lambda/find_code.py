"""Helpers for locating lambda functions."""
from os import path


def dirname(name):
    """Return the path on disk for requested directories."""
    if path.isabs(name):
        return name
    else:
        return path.join(path.dirname(path.realpath(__file__)),
                         name)
