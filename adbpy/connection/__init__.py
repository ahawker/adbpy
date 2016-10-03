"""
    adbpy.connection
    ~~~~~~~~~~~~~~~~

    Contains functionality for dealing with an abstraction that encapsulates a transport and state.
"""

import abc
import functools


__all__ = ['Connection', 'requires_active_connection']


class ConnectionError(Exception):
    """
    Base exception for all connection related errors.
    """


class ConnectionRequiredError(ConnectionError):
    """
    Exception raised when a function decorated with :func:`~adbpy.connection.requires_active_connection` is called
    with a closed connection.
    """


class ConnectionTimeoutError(ConnectionError):
    """
    Exception raised when the wrapped transport raises a timeout related exception.
    """


def requires_active_connection(func):
    """
    Decorator that enforces calls on the :class:`~adbpy.connection.Connection` instance to only be allowed on
    active connections.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_connected:
            raise ConnectionRequiredError('{} requires an active connection'.format(func.__name__))
        return func(self, *args, **kwargs)
    return wrapper


class Connection(metaclass=abc.ABCMeta):
    """
    Abstract class that defines the interface a connection must implement.
    """

    @classmethod
    @abc.abstractclassmethod
    def connect(cls, *args, **kwargs):
        pass

    def __init__(self, transport, context):
        self._transport = transport
        self._context = context

    def __repr__(self):
        return '<{}(transport={}, context={})>'.format(self.__class__.__name__, self._transport, self._context)

    @property
    def is_connected(self):
        return bool(self._transport) and bool(self._context)

    @abc.abstractmethod
    def disconnect(self, **args, **kwargs):
        pass

    @abc.abstractmethod
    def send(self, data, *args, **kwargs):
        pass

    @abc.abstractmethod
    def recv(self, num_bytes, *args, **kwargs):
        pass
