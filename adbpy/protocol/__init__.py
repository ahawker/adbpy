"""
    adbpy.protocol
    ~~~~~~~~~~~~~~

    Contains functionality for protocols adb, fastboot, and filesync used to communicate with devices.
"""

import abc


__all__ = ['WireProtocol', 'FlowProtocol']


class ProtocolError(Exception):
    """
    Base exception for all protocol related errors.
    """


class ProtocolConnectionError(ProtocolError):
    """
    Exception raised when the underlying connection throws an exception.
    """


class ProtocolNoResponseError(ProtocolError):
    """
    Exception raised when a protocol request expects a response but does not receive one.
    """


class ProtocolInvalidResponseError(ProtocolError):
    """
    Exception raised when the protocol received a response that it did not expect.
    """


class WireProtocol(metaclass=abc.ABCMeta):
    """
    Abstract class that defines the interface a wire protocol must implement.

    A wire protocol is the low level bridge between the connection (transport) and the higher level flow protocol. A
    wire protocol is responsible for taking standard data bytes, packing/unpacking into the proper protocol message
    types and reading/writing this data from the wire (connection).

    A wire protocol should be in-different to the underlying connection/transport type it is using.
    """

    def __init__(self, connection):
        self._connection = connection

    def __repr__(self):
        return '<{}(connection={})>'.format(self.__class__.__name__, self._connection)

    @abc.abstractmethod
    def send(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def recv(self, *args, **kwargs):
        pass


class FlowProtocol(metaclass=abc.ABCMeta):
    """
    Abstract class that defines the interface a flow protocol must implement.

    A flow protocol is the higher level protocol that performs the "state machine" like functionality. A flow protocol
    is responsible for validating the "context" of the requests/responses send to/from the wire protocol and
    encapsulating any internals of both protocol types.

    A flow protocol should always be linked to a single type of wire protocol, i.e. an ADB flow protocol cannot work
    with a Fastboot wire protocol.
    """

    def __init__(self, wire_protocol):
        self._wire_protocol = wire_protocol

    def __repr__(self):
        return '<{}(wire_protocol={})>'.format(self.__class__.__name__, self._wire_protocol)
