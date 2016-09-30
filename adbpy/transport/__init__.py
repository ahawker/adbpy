"""
    adbpy.transport
    ~~~~~~~~~~~~~~~

    Contains functionality for transports (TCP, UDP, USB) used to communicate with devices.
"""

import abc
import functools


__all__ = ['Transport', 'requires_context', 'rethrow_timeout_exception']


#: Default timeout in milliseconds for transport connect attempt.
DEFAULT_CONNECT_TIMEOUT_MS = None

#: Default timeout in milliseconds for transport disconnect attempt.
DEFAULT_DISCONNECT_TIMEOUT_MS = None

#: Default timeout in milliseconds for transport send attempt.
DEFAULT_SEND_TIMEOUT_MS = None

#: Default timeout in milliseconds for transport receive attempt.
DEFAULT_RECV_TIMEOUT_MS = None


class TransportError(Exception):
    """
    Base exception for all transport related errors.
    """


class TransportTimeoutError(TransportError):
    """
    Base exception for all transport timeout related errors.
    """


class TransportConnectTimeout(TransportTimeoutError):
    """
    Exception raised when a transport connect attempt exceeds its timeout.
    """


class TransportDisconnectTimeout(TransportTimeoutError):
    """
    Exception raised when a transport disconnect attempt exceeds its timeout.
    """


class TransportSendTimeout(TransportTimeoutError):
    """
    Exception raised when a transport send attempt exceeds its timeout.
    """


class TransportReceiveTimeout(TransportTimeoutError):
    """
    Exception raised when a transport recv attempt exceeds its timeout.
    """


class TransportContextRequiredError(TransportError):
    """
    Exception raised when a function decorated with :func:`~adbpy.transport.requires_context` does not receive
    a valid transport context object.
    """


def requires_context(context_type):
    """
    Decorator that enforces the first function argument be a valid transport context object of the specified type.

    :param context_type: Type of transport context object
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, context, *args, **kwargs):
            if not isinstance(context, context_type):
                raise TransportContextRequiredError(
                    '{} requires a valid transport context of type {}'.format(func.__name__, context_type))
            return func(self, context, *args, **kwargs)
        return wrapper
    return decorator


def rethrow_timeout_exception(catch_exc, raise_exc):
    """
    Decorator that catches low level transport timeout related exception and raises an `adbpy` specific one.

    :param catch_exc: Underlying transport timeout exception to catch
    :param raise_exc: General transport timeout exception to raise
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


class Transport(metaclass=abc.ABCMeta):
    """
    Abstract class that defines the interface a transport must implement.
    """

    @abc.abstractmethod
    def connect(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def disconnect(self, context, **kwargs):
        pass

    @abc.abstractmethod
    def send(self, context, data, **kwargs):
        pass

    @abc.abstractmethod
    def recv(self, context, num_bytes, **kwargs):
        pass
