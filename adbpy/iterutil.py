"""
    adbpy.iterutil
    ~~~~~~~~~~~~~~

    Contains common helpers when dealing with iterables, iteration, and generators.
"""
import collections


__all__ = ['IterableEmpty', 'iterable', 'first']


DEFAULT_SENTINEL = object()


class IterableEmpty(Exception):
    """
    Exception raised when an iterable is completely empty.
    """


def iterable(item):
    """
    Return an iterable that contains the given item or itself if it already is one.
    """
    if isinstance(item, collections.Iterable) and not isinstance(item, (str, bytes)):
        return item

    return [item] if item is not None else []


def first(func, *args, **kwargs):
    """
    Return the first item from the given function that returns an iterable or
    raise a :class:`~adbpy.iterutil.IterableEmpty`.

    :param func: Iterable to consume the first item from
    :param args: Positional args to pass to the iterable
    :param kwargs: Keyword args to pass to the iterable
    :return: First item from the iterable if non-empty otherwise raise :class:`~adbpy.iterutil.IterableEmpty`
    """
    item = next(iter(func(*args, **kwargs)), DEFAULT_SENTINEL)
    if item is DEFAULT_SENTINEL:
        raise IterableEmpty('Iterable did not yield any items')

    return item
