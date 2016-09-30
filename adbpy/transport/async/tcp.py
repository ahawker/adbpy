"""
    adbpy.transport.async.tcp
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Contains functionality for an asynchronous (non-blocking) TCP transport based on `asyncio`
"""

import asyncio
import collections
import logging
import socket

from adbpy import transport


__all__ = ['Context', 'Transport']


LOGGER = logging.getLogger(__name__)
WIRE_LOGGER = LOGGER.getChild('wire')


#: Transport context object returned by :meth:`~adbpy.transport.async.tcp.Transport.connect`.
Context = collections.namedtuple('Context', 'reader writer loop')


class Transport(transport.Transport):
    """
    Class for interacting with an asynchronous (non-blocking) TCP socket.
    """

    def __init__(self, host, port):
        self._host = host
        self._port = port

    def __repr__(self):
        return '<{}(host={}, port={})>'.format(self.__class__.__name__, self._host, self._port)

    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportConnectTimeout)
    def connect(self, reader=None, writer=None, loop=None, timeout=transport.DEFAULT_CONNECT_TIMEOUT_MS):
        """
        Connect to an asynchronous (non-blocking) TCP socket at the defined host/port.

        :param reader: Optional :class:`~asyncio.streams.StreamReader` instance to re-use
        :param writer: Optional :class:`~asyncio.streams.StreamWriter` instance to re-use
        :param loop: Optional :class:`~asyncio.events.AbstractEventLoop` instance to use
        :param timeout: Optional timeout in seconds to use when connecting to the socket
        :return: A :class:`~adbpy.transport.async.tcp.Context` instance used to communicate with the socket
        """
        reader, writer = self._open_socket(self._host, self._port, reader, writer, loop)
        return Context(reader, writer, loop)

    @transport.requires_context(Context)
    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportDisconnectTimeout)
    def disconnect(self, context, timeout=transport.DEFAULT_DISCONNECT_TIMEOUT_MS):
        """
        Disconnect from the asynchronous (non-blocking) TCP socket managed by the given context object.

        :param context: A :class:`~adbpy.transport.async.tcp.Context` object whose socket we want to disconnect
        :param timeout: Optional timeout in seconds to use when disconnecting fromt he socket
        :return: `None`
        """
        self._close_socket(context.reader, context.writer, context.loop)

    @transport.requires_context(Context)
    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportSendTimeout)
    def send(self, context, data, timeout=transport.DEFAULT_SEND_TIMEOUT_MS):
        """
        Send data to the asynchronous (non-blocking) TCP socket managed by the given context object.

        :param context: A :class:`~adbpy.transport.async.tcp.Context` object whose socket we want to send data to
        :param data: Byte buffer payload to write to the socket
        :param timeout: Optional timeout in seconds to use when sending to the socket
        :return: `None`
        """
        return self._write_bytes_to_socket(context.writer, data, timeout, context.loop)

    @transport.requires_context(Context)
    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportReceiveTimeout)
    def recv(self, context, num_bytes, timeout=transport.DEFAULT_RECV_TIMEOUT_MS):
        """
        Receive data from the asynchronous (non-blocking) TCP socket managed by the given context object.

        :param context: A :class:`~adbpy.transport.async.tcp.Context` object whose socket want to receive data from
        :param num_bytes: Number of bytes to read from the socket
        :param timeout: Optional timeout in seconds to use when receiving from the socket
        :return: A :class:`bytes` buffer containing data read from the socket
        """
        return self._read_bytes_from_socket(context.reader, num_bytes, timeout, context.loop)

    def _write_bytes_to_socket(self, writer, data, timeout, loop=None):
        """
        Write a buffer of bytes to the given writer.

        :param writer: A :class:`~asyncio.streams.StreamWriter` instance to write bytes to
        :param data: Buffer to write
        :param timeout: Timeout in seconds for the write to complete
        :param loop: Optional event loop instance to use
        :return: `None`
        """
        LOGGER.debug('Writing data to {}:{}, timeout={}, length={}'.format(self._host, self._port,
                                                                           timeout, len(data)))

        if WIRE_LOGGER.isEnabledFor(logging.DEBUG):
            WIRE_LOGGER.debug('>>> {}'.format(data))

        writer.write(data)
        result = yield from asyncio.wait_for(writer.drain(), timeout=timeout, loop=loop)
        return result

    def _read_bytes_from_socket(self, reader, num_bytes, timeout, loop=None):
        """
        Read a buffer of bytes from the given reader.

        :param reader: A :class:`~asyncio.streams.StreamReader` instance to read bytes from
        :param num_bytes: Number of bytes to read
        :param timeout: Timeout in seconds for the read to complete
        :param loop: Optional event loop instance to use
        :return: A :class:`~bytes` buffer read from the socket
        """
        LOGGER.debug('Reading data from {}:{}, timeout={}, length={}'.format(self._host, self._port,
                                                                             timeout, num_bytes))

        data = yield from asyncio.wait_for(reader.read(num_bytes), timeout=timeout, loop=loop)

        if WIRE_LOGGER.isEnabledFor(logging.DEBUG):
            WIRE_LOGGER.debug('<<< {}'.format(data))

        return data

    def _open_socket(self, host, port, reader=None, writer=None, loop=None):
        """
        Create a socket connection to the given host/port and return back reader/writers for it.

        :param host: Remote host to connect
        :param port: Remote port to connect
        :param reader: Optional :class:`~asyncio.streams.StreamReader` instance to re-use
        :param writer: Optional :class:`~asyncio.streams.StreamWriter` instance to re-use
        :param loop: Optional event loop instance to use
        :return: A tuple of :class:`~asyncio.streams.StreamReader` and :class:`~asyncio.streams.StreamWriter` instances
        """
        if reader and writer:
            LOGGER.debug('Reusing existing reader/writer')
            return reader, writer

        LOGGER.debug('Opening socket to {}:{}'.format(host, port))

        reader, writer = yield from asyncio.open_connection(host, port, loop=loop)
        return reader, writer

    def _close_socket(self, reader, writer, loop=None):
        """
        Close the given writer.

        :param reader: A :class:`~asyncio.streams.StreamReader` instance to close
        :param writer: A :class:`~asyncio.streams.StreamWriter` instance to close
        :param loop: Optional event loop instance to use
        :return: `None`
        """
        LOGGER.debug('Closing socket')
        writer.close()
