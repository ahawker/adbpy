"""
    adbpy.connection.sync
    ~~~~~~~~~~~~~~~~~~~~~

    Contains functionality for dealing with synchronous (blocking) connections.
"""

from adbpy import connection, exception, transport


__all__ = ['Connection']


class Connection(connection.Connection):
    """
    Connection that defines a synchronous (blocking) interface and a wraps synchronous transport.
    """

    @classmethod
    @exception.rethrow_timeout(transport.TransportConnectTimeout, connection.ConnectionTimeoutError)
    @exception.rethrow(transport.TransportError, connection.ConnectionError)
    def connect(cls, transport, *args, **kwargs):
        """
        Create a new connection based on the given transport.

        :param transport: Transport to connect
        :param args: Optional positional args to pass to the :meth:`~adbpy.transport.Transport.connect` method
        :param kwargs: Optional keyword args to pass to the :meth:`~adbpy.transport.Transport.connect` method
        :return: A :class:`~adbpy.connection.sync.Connection` instance that wraps the newly connected transport
        """
        context = transport.connect(*args, **kwargs)
        return cls(transport, context)

    @connection.requires_active_connection
    @exception.rethrow_timeout(transport.TransportDisconnectTimeout, connection.ConnectionTimeoutError)
    @exception.rethrow(transport.TransportError, connection.ConnectionError)
    def disconnect(self, *args, **kwargs):
        """
        Disconnect the connection.

        :param args: Optional positional args to pass to the :meth:`~adbpy.transport.Transport.disconnect` method
        :param kwargs: Optional keyword args to pass to the :meth:`~adbpy.transport.Transport.disconnect` method
        :return: `None`
        """
        self._transport.disconnect(self._context, *args, **kwargs)
        self._transport = None
        self._context = None

    @connection.requires_active_connection
    @exception.rethrow_timeout(transport.TransportSendTimeout, connection.ConnectionTimeoutError)
    @exception.rethrow(transport.TransportError, connection.ConnectionError)
    def send(self, data, *args, **kwargs):
        """
        Send the given data buffer over the connection.

        :param data: Buffer to send
        :param args: Optional positional args to pass to the :meth:`~adbpy.transport.Transport.send` method
        :param kwargs: Optional keyword args to pass to the :meth:`~adbpy.transport.Transport.send` method
        :return: `None`
        """
        return self._transport.send(self._context, data, **kwargs)

    @connection.requires_active_connection
    @exception.rethrow_timeout(transport.TransportReceiveTimeout, connection.ConnectionTimeoutError)
    @exception.rethrow(transport.TransportError, connection.ConnectionError)
    def recv(self, num_bytes, *args, **kwargs):
        """
        Read bytes from the connection.

        :param num_bytes: Number of bytes to read
        :param args: Optional positional args to pass to the :meth:`~adbpy.transport.Transport.recv` method
        :param kwargs: Optional keyword args to pass to the :meth:`~adbpy.transport.Transport.recv` method
        :return: Bytes read
        """
        if not num_bytes:
            return None

        buf = b''
        remaining = num_bytes
        while remaining > 0:
            data = self._transport.recv(self._context, remaining, **kwargs)
            if not data:
                break
            buf += data
            remaining -= len(data)

        return buf
