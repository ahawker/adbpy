"""
    adbpy.message.adb
    ~~~~~~~~~~~~~~~~~

    Contains functionality for representing ADB protocol messages.
"""

import enum
import struct

from adbpy import message


__all__ = ['Message', 'Command', 'AuthType', 'to_bytes', 'from_bytes',
           'connect', 'auth', 'open', 'ready', 'write', 'close']


#: Protocol version.
VERSION = 0x01000000

#: Maximum message body size.
MAXDATA = 256 * 1024

#: Older ADB version max data size limit; required max for CONNECT and AUTH messages.
CONNECT_AUTH_MAXDATA = 4096

#: Size of a serialized ADB message in bytes.
MESSAGE_SIZE = 24

#: Bitmask applied to the "magic" value of ADB messages.
COMMAND_MASK = 0xffffffff

#: Struct pack/unpack string for handling six unsigned integers.
MESSAGE_FORMAT = '<6I'


class Command(enum.IntEnum):
    """
    Enumeration for supported command types by the ADB protocol.
    """

    sync = 0x434e5953  # Internal only.
    cnxn = 0x4e584e43
    auth = 0x48545541
    open = 0x4e45504f
    okay = 0x59414b4f
    clse = 0x45534c43
    wrte = 0x45545257


class CommandResponse(enum.Enum):
    """
    Enumeration for support response message types from ADB connection requests.
    """

    okay = 'OKAY'
    fail = 'FAIL'


class AuthType(enum.IntEnum):
    """
    Enumeration for supported authentication types by the ADB protocol.
    """

    token = 1
    signature = 2
    rsa_public_key = 3


class SystemType(enum.Enum):
    """
    Enumeration for supported "systemtype" values of the "system-identity-string".
    """

    bootloader = 'bootloader'
    device = 'device'
    host = 'host'


class StreamIdentifierFormat(enum.Enum):
    """
    Enumeration for common stream "destination" strings.
    """

    tcp = 'tcp:{host}:{port}'
    udp = 'udp:{host}:{port}'
    local_dgram = 'local-dgram:{identifier}'
    local_stream = 'local-stream:{identifier}'
    shell = 'shell'
    upload = 'upload'
    fs_bridge = 'fs-bridge'


class Message:
    """
    Represents an ADB protocol message.

    A message consists of a 24-byte header followed by an optional data payload. The header is serialized over the
    wire as 6, 32-bit words in little-endian format.
    """

    __slots__ = ['command', 'arg0', 'arg1', 'data_length', 'data_checksum', 'magic', 'data']

    def __init__(self, command, arg0=None, arg1=None, data_length=None, data_checksum=None, magic=None, data=b''):
        self.command = command
        self.arg0 = arg0
        self.arg1 = arg1
        self.data_length = data_length
        self.data_checksum = data_checksum
        self.magic = magic
        self.data = data

    def __repr__(self):
        return ('<{}(command={}, arg0={}, arg1={}, data_length={}, '
                'data_checksum={}, magic={})>').format(self.__class__.__name__, hex(self.command), self.arg0,
                                                       self.arg1, self.data_length, self.data_checksum, self.magic)

    @property
    def is_connect(self):
        """
        Return `True` if message is a "A_CNXN" command, `False` otherwise.
        """
        return self.command == Command.cnxn

    @property
    def is_auth(self):
        """
        Return `True` if message is a "A_AUTH" command, `False` otherwise.
        """
        return self.command == Command.auth

    @property
    def is_open(self):
        """
        Return `True` if message is a "A_OPEN" command, `False` otherwise.
        """
        return self.command == Command.open

    @property
    def is_ready(self):
        """
        Return `True` if message is a "A_OKAY" command, `False` otherwise.
        """
        return self.command == Command.okay

    @property
    def is_write(self):
        """
        Return `True` if message is a "A_WRTE" command, `False` otherwise.
        """
        return self.command == Command.wrte

    @property
    def is_close(self):
        """
        Return `True` if message is a "A_CLSE" command, `False` otherwise.
        """
        return self.command == Command.clse

    @property
    def is_sync(self):
        """
        Return `True` if message is a "A_SYNC" command, `False` otherwise.
        """
        return self.command == Command.sync

    @property
    def is_okay(self):
        """
        Return `True` if message is an "OKAY" response, `False` otherwise.
        """
        return self.command == CommandResponse.okay.value

    @property
    def is_fail(self):
        """
        Return `True` if message is an "FAIL" response, `False` otherwise.
        """
        return self.command == CommandResponse.fail.value


def to_bytes(msg):
    """
    Pack the given :class:`~adbpy.message.adb.Message` instance into six, four-byte unsigned little-endian integers.

    >>> msg = message.connect('0123456789ABCDEF', 'foobarbaz')
    '<Message(command=0x4e584e43, arg0=16777216, arg1=4096, data_length=32, data_checksum=2442, magic=2980557244)>'
    >>> message.to_bytes(msg)
    b'CNXN\x00\x00\x00\x01\x00\x10\x00\x00 \x00\x00\x00\x8a\t\x00\x00\xbc\xb1\xa7\xb1'

    :param msg: :class:`~adbpy.message.adb.Message` instance to convert to bytes
    :return: Byte representation of :class:`~adbpy.message.adb.Message` instance
    """
    try:
        return struct.pack(MESSAGE_FORMAT, msg.command, msg.arg0, msg.arg1,
                           msg.data_length, msg.data_checksum, msg.magic)
    except struct.error:
        raise message.MessagePackError('Unable to pack message into byte buffer')


def from_bytes(msg_bytes):
    """
    Unpack the given bytes into a :class:`~adbpy.message.adb.Message` instance.

    The `msg_bytes` buffer should contain six, four-byte unsigned little-endian integers.

    >>> data = b'CNXN\x00\x00\x00\x01\x00\x10\x00\x00 \x00\x00\x00\x8a\t\x00\x00\xbc\xb1\xa7\xb1'
    >>> msg = message.from_bytes(data)
    '<Message(command=0x4e584e43, arg0=16777216, arg1=4096, data_length=32, data_checksum=2442, magic=2980557244)>'

    :param msg_bytes: Bytes to convert to :class:`~adbpy.message.adb.Message` instance
    :return: A :class:`~adbpy.message.adb.Message` created from the given bytes
    """
    try:
        command, arg0, arg1, data_length, data_checksum, magic = struct.unpack(MESSAGE_FORMAT, msg_bytes)
    except struct.error:
        raise message.MessageUnpackError('Unable to unpack message from byte buffer')
    else:
        return _response(command, arg0, arg1, data_length, data_checksum, magic)


def attach_data(msg, data):
    """
    Mutate the given message by attaching a data payload.

    :param msg: :class:`~adbpy.message.adb.Message` instance receiving a data payload
    :param data: Data payload to attach to the message instance
    :return: `None`
    """
    # Validate the data payload checksum matches the checksum received in the message header.
    checksum = _checksum(data)
    if msg.data_checksum != checksum:
        raise message.MessageChecksumError('Checksum {} != {}'.format(msg.data_checksum, checksum))

    msg.data = data


def connect(serial, banner, system_type=SystemType.host.value):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a connect message.

    :param serial: Unique identifier
    :param banner: Human readable version/identifier string
    :param system_type: System type creating the message; default: "host"
    :return: A :class:`~adbpy.adb.message.adb.Message` instance for connecting to a remote system
    """
    system_identity_string = _null_terminated(':'.join((system_type, serial, banner)))
    return _request(Command.cnxn, VERSION, CONNECT_AUTH_MAXDATA, system_identity_string)


def auth(auth_type, data):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a authentication message.

    :param auth_type: Authentication type to use between the two parties
    :param data: Payload signed with private key or random token to resign when private key not accepted
    :return: A :class:`~adbpy.adb.message.adb.Message` instance for authenticating to a remote system
    """
    return _request(Command.auth, int(auth_type), 0, data)


def auth_signature(signature):
    """
    Create a :class`~adbpy.message.adb.Message` instance that represents a authentication message
    of type "SIGNATURE (2)".

    :param signature: Signature data
    :return: A :class:`~adbpy.adb.message.adb.Message` instance for signature authentication
    """
    return auth(AuthType.signature, signature)


def auth_rsa_public_key(public_key):
    """
    Create a :class`~adbpy.message.adb.Message` instance that represents a authentication message
    of type "RSAPUBLICKEY (3)".

    :param public_key: Public key for remote system to accept
    :return: A :class:`~adbpy.adb.message.adb.Message` instance for RSA authentication
    """
    return auth(AuthType.rsa_public_key, _null_terminated(public_key))


def open(local_id, destination):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a open message to connect
    to a stream of a specific id.

    :param local_id: Stream id on remote system to connect with
    :param destination: Stream destination, See: `~adbpy.message.adb.StreamIdentifierFormat`
    :return: A :class:`~adbpy.adb.message.Message` instance to open a stream by id on a remote system
    """
    return _request(Command.open, local_id, 0, _null_terminated(destination))


def ready(local_id, remote_id):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a ready message indicating that the stream
    is ready for write messages.

    :param local_id: Identifier for the stream on the local end
    :param remote_id: Identifier for the stream on the remote system
    :return: A :class:`~adbpy.message.adb.Message` instance to inform the remote system it's ready for write messages
    """
    return _request(Command.okay, local_id, remote_id)


def okay(local_id, remote_id):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a ready message indicating that the stream
    is ready for write messages.

    :param local_id: Identifier for the stream on the local end
    :param remote_id: Identifier for the stream on the remote system
    :return: A :class:`~adbpy.message.adb.Message` instance to inform the remote system it's ready for write messages
    """
    return ready(local_id, remote_id)


def write(local_id, remote_id, data):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a write message sending a data payload
    to a specific stream id.

    :param local_id: Identifier for the stream on the local end
    :param remote_id: Identifier for the stream on the remote system
    :param data: Data payload sent to the stream
    :return: A :class:`~adbpy.message.adb.Message` instance with a data payload for a specific remote stream
    """
    if not data:
        raise ValueError('data must not be empty')
    if data > MAXDATA:
        raise ValueError('data must be <= {}'.format(MAXDATA))

    return _request(Command.wrte, local_id, remote_id, data)


def close(local_id, remote_id):
    """
    Create a :class:`~adbpy.message.adb.Message` instance that represents a close message informing the remote system
    that a stream should be closed.

    :param local_id: Identifier for the stream on the local end
    :param remote_id: Identifier for the stream on the remote system
    :return: A :class:`~adbpy.message.adb.Message` instance to inform the remote system of stream closing
    """
    return _request(Command.clse, local_id, remote_id)


def _request(command, arg0=None, arg1=None, data=b''):
    """
    Create a :class:`~adbpy.message.adb.Message` instance with the given header information and optional data payload
    that represents a new request being sent to a remote system.

    :param command: Command value as :class:`int` or :class:`~adbpy.message.adb.Command` enum value
    :param arg0: Optional message header arg0 value
    :param arg1: Optional message header arg1 value
    :param data: Optional data payload
    :return: A :class:`~adbpy.message.adb.Message` instance with the given header data and optional data payload
    """
    data = _data_to_bytes(data)
    return Message(int(command), arg0, arg1, len(data), _checksum(data), _magic(command), data)


def _response(command, arg0, arg1, data_length, data_checksum, magic):
    """
    Create a :class:`~adbpy.message.adb.Message` instance with the given header information and no data payload
    that represents a response being sent to a remote system based on a message received from it.

    :param command: The :class:`int` representation of a specific :class:`~adbpy.message.adb.Command` enum value
    :param arg0: Header arg0 value
    :param arg1: Header arg1 value
    :param data_length: Length of data payload that will be sent
    :param data_checksum: Checksum of data payload
    :param magic: Magic bit calculated for this specific header
    :return: A :class:`~adbpy.message.adb.Message` instance with the given header data
    """
    return Message(Command(command), arg0, arg1, data_length, data_checksum, magic)


def _data_to_bytes(data, encoding='utf-8', errors='strict'):
    """
    Convert the message data payload to bytes.

    If `data` is already a :class:`~bytes` instance, it is returned unmodified.

    :param data: bytes/str instance to convert to bytes
    :param encoding:
    :param errors:
    :return: data as :class:`~bytes` instance
    """
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode(encoding, errors)

    raise ValueError('Expected bytes/str; got {}'.format(type(data)))


def _null_terminated(data):
    """
    NULL terminates the given buffer.

    :param data: str or bytes object to null-terminate
    :return: null-terminated copy of the passed in data buffer
    """
    terminator = b'\0' if isinstance(data, bytes) else '\0'
    return data + terminator


def _magic(command):
    """
    Compute the "magic" integer value of a specific command type.

    :param command: The :class:`int` value of the command type
    :return: command ^ 0xffffffff
    """
    return command ^ COMMAND_MASK


def _checksum(data):
    """
    Compute the checksum of the given data payload.

    :param data: Data payload to consume the checksum
    :return: A :class:`int` representing the computed checksum of the data payload
    """
    return sum(data) & COMMAND_MASK
