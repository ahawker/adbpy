"""
    tests/message/test_adb
    ~~~~~~~~~~~~~~~~~~~~~~

    Contains tests for the :mod:`~adbpy.message.adb` module.
"""

import pytest

from adbpy.message import adb


@pytest.mark.parametrize('data', [
    b'',
    b'foo',
    b'bar',
    b'baz',
    b'42'
])
def test_null_terminated_applies_null_byte_at_end(data):
    """
    Assert that :func:`~adbpy.message.adb._null_terminated` adds a NULL byte to the end of the given :class:`bytes`
    or :class:`str` instance.
    """
    assert adb._null_terminated(data) == data + b'\0'
    assert adb._null_terminated(data.decode()) == data.decode() + '\0'


@pytest.mark.parametrize('command', [
    adb.Command.sync,
    adb.Command.cnxn,
    adb.Command.auth,
    adb.Command.open,
    adb.Command.okay,
    adb.Command.clse,
    adb.Command.wrte
])
def test_apply_magic_applies_expected_xor(command):
    """
    Assert that :func:`~adbpy.message.adb._magic` generates the expected XOR of the given command.
    """
    assert adb._magic(command) == command ^ adb.COMMAND_MASK


@pytest.mark.parametrize('data', [
    b'',
    b'foo',
    b'bar',
    b'foobar',
    b'19d@#(@#fdkflsf',
    b'0101-1-1-$%$#(#@(#(#(#(#@@@@@'
])
def test_checksum_generates_expected_crc32_value(data):
    """
    Assert that :func:`~adbpy.message.adb._checksum` generates the expected checksum value.
    """
    assert adb._checksum(data) == sum(data) & adb.COMMAND_MASK
