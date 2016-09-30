"""
    adbpy.message
    ~~~~~~~~~~~~~

    Contains functionality for representing protocol messages.
"""


class MessageError(Exception):
    """
    Base exception class for dealing with all message related errors.
    """


class MessagePackError(MessageError):
    """
    Exception raised when unable to pack/serialize a message into bytes.
    """


class MessageUnpackError(MessageError):
    """
    Exception raised when unable to unpack/deserialize bytes into a message.
    """


class MessageChecksumError(MessageError):
    """
    Exception raised when a data payload checksum does not match the message header checksum.

    TODO - This is the ADB specific or generic to fastboot and filesync as well?
    """
