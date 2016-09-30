"""
    adbpy.transport.sync.tcp
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Contains functionality for a synchronous (blocking) TCP transport.
"""

import collections
import contextlib
import logging
import socket

from adbpy import transport


__all__ = ['Context', 'Transport']


LOGGER = logging.getLogger(__name__)
WIRE_LOGGER = LOGGER.getChild('wire')


#: Transport context object returned by :meth:`~adbpy.transport.sync.tcp.Transport.connect`.
Context = collections.namedtuple('Context', 'sock')


@contextlib.contextmanager
def socket_timeout_scope(sock, timeout):
    """
    Context manager responsible for patching the socket timeout for the specific time scope.

    :param sock: A :class:`~socket.socket` instance to set the timeout on
    :param timeout: A :class:`~float` that represents the socket timeout in seconds 
    """
    current_timeout = sock.gettimeout()
    sock.settimeout(timeout)
    try:
        yield
    finally:
        sock.settimeout(current_timeout)


class Transport(transport.Transport):
    """
    Class for interacting with a synchronous (blocking) TCP socket.
    """

    def __init__(self, host, port):
        self._host = host
        self._port = port

    def __repr__(self):
        return '<{}(host={}, port={})>'.format(self.__class__.__name__, self._host, self._port)

    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportConnectTimeout)
    def connect(self, sock=None, timeout=transport.DEFAULT_CONNECT_TIMEOUT_MS):
        """
        Connect to a synchronous (blocking) TCP socket at the defined host/port.

        :param sock: Optional :class:`~socket.socket` instance to re-use
        :param timeout: Optional timeout in seconds to use when opening the socket connection
        :return: A :class:`~adbpy.transport.sync.tcp.Context` instance used to communicate with the socket
        """
        sock = self._open_socket(self._host, self._port, sock, timeout)
        return Context(sock)

    @transport.requires_context(Context)
    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportDisconnectTimeout)
    def disconnect(self, context, timeout=transport.DEFAULT_DISCONNECT_TIMEOUT_MS):
        """
        Disconnect from the synchronous (blocking) TCP socket managed by the given context object.

        :param context: A :class:`~adbpy.transport.sync.tcp.Context` object whose socket we want to disconnect
        :param timeout: Optional timeout in seconds to use when disconnecting from the socket
        :return: `None`
        """
        self._close_socket(context.sock)

    @transport.requires_context(Context)
    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportSendTimeout)
    def send(self, context, data, timeout=transport.DEFAULT_SEND_TIMEOUT_MS):
        """
        Send data to the synchronous (blocking) TCP socket managed by the given context object.

        :param context: A :class:`~adbpy.transport.sync.tcp.Context` object whose socket we want send data to
        :param data: Byte buffer payload to write to the socket
        :param timeout: Optional timeout in seconds to use when sending to the socket
        :return: `None`
        """
        return self._write_bytes_to_socket(context.sock, data, timeout)

    @transport.requires_context(Context)
    @transport.rethrow_timeout_exception(socket.timeout, transport.TransportReceiveTimeout)
    def recv(self, context, num_bytes, timeout=transport.DEFAULT_RECV_TIMEOUT_MS):
        """
        Receive data from the synchronous (blocking) TCP socket managed by the given context object.

        :param context: A :class:`~adbpy.transport.sync.tcp.Context` object whose socket we want to receive data from
        :param num_bytes: Number of bytes to read from the socket
        :param timeout: Optional timeout in seconds to use when receiving from the socket
        :return: A :class:`bytes` buffer containing data read from the socket
        """
        return self._read_bytes_from_socket(context.sock, num_bytes, timeout)

    def _write_bytes_to_socket(self, sock, data, timeout):
        """
        Write a buffer of bytes to the given socket.

        :param sock: A :class:`~socket.socket` instance to write bytes to
        :param data: Buffer to write
        :param timeout: Timeout in seconds to set on the socket before writing
        :return: `None`
        """
        LOGGER.debug('Writing data to {}:{}, timeout={}, length={}'.format(self._host, self._port,
                                                                           timeout, len(data)))

        if WIRE_LOGGER.isEnabledFor(logging.DEBUG):
            WIRE_LOGGER.debug('>>> {}'.format(data))

        with socket_timeout_scope(sock, timeout):
            return sock.sendall(data)

    def _read_bytes_from_socket(self, sock, num_bytes, timeout):
        """
        Read a buffer of bytes from the given socket.

        :param sock: A :class:`~socket.socket` instance to read bytes from
        :param num_bytes: Number of bytes to read
        :param timeout: Timeout in seconds to set on the socket before reading
        :return: A :class:`~bytes` buffer read from the socket
        """
        LOGGER.debug('Reading data from {}:{}, timeout={}, length={}'.format(self._host, self._port,
                                                                             timeout, num_bytes))

        with socket_timeout_scope(sock, timeout):
            data = sock.recv(num_bytes)

        if WIRE_LOGGER.isEnabledFor(logging.DEBUG):
            WIRE_LOGGER.debug('<<< {}'.format(data))

        return data

    def _open_socket(self, host, port, sock=None, timeout=None):
        """
        Create a socket connection to the given host/port.

        :param host: Remote host to connect
        :param port: Remote port to connect
        :param sock: Optional :class:`~socket.socket` instance to re-use instead of creating a new one
        :param timeout: Optional timeout in seconds to use when creating the socket connection
        :return: A :class:`~socket.socket` instance connected to the remote host/port
        """
        if sock:
            LOGGER.debug('Reusing existing socket')
            return sock

        LOGGER.debug('Opening socket to {}:{}'.format(host, port))
        return socket.create_connection((host, port), timeout)

    def _close_socket(self, sock):
        """
        Close the given socket.

        :param sock: A :class:`~socket.socket` instance to close.
        :return: `None`
        """
        LOGGER.debug('Closing socket')
        sock.close()
