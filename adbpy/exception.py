"""
    adb.exceptions
    ~~~~~~~~~~~~~~

    Contains functionality for dealing with exceptions.
"""

import functools


def rethrow(catch_exc, raise_exc, raise_exc_fmt='{catch_exc.message}'):
    """
    Decorator to catch a specific exception type and rethrow it as another.

    :param catch_exc: Type of exception to catch
    :param raise_exc: Type of exception to throw
    :param raise_exc_fmt: Format string to generate message of new exception
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except catch_exc as e:
                raise raise_exc(raise_exc_fmt.format(catch_exc=catch_exc)) from e
        return wrapper
    return decorator


def rethrow_timeout(catch_exc, raise_exc):
    """
    Decorator to catch specific timeout exception types and rethrow it as another.

    :param catch_exc: Type of timeout exception to catch
    :param raise_exc: Type of timeout exception to throw
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except catch_exc as e:
                timeout = kwargs.get('timeout')
                timeout_msg = '' if not timeout else ' of {} ms'.format(timeout)
                exc_msg = '{} exceeded timeout{}'.format(func.__name__, timeout_msg)
                raise raise_exc(exc_msg) from e
        return wrapper
    return decorator
