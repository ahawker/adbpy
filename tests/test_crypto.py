"""
    test_crypto
    ~~~~~~~~~~~

    Tests for the :mod:`~adbpy.crypto` module.
"""

import pytest

from adbpy import crypto


@pytest.fixture(scope='function')
def adb_hash():
    """
    Fixture that returns a :class:`~adbpy.crypto.ADBHash` instance.
    """
    return crypto.ADBHash()


@pytest.fixture(scope='module', params=[
    b'',
    b'foo',
    b'bar',
    b'baz',
    b'foobar',
    b'foobarbaz'
])
def hash_bytes(request):
    """
    Fixture that yields collections of bytes that should be fed into a hash algorithm.
    """
    return request.param


@pytest.fixture(scope='module', params=[

])
def valid_pkcs_1_def_format_bytes(request):
    """
    TODO
    """
    return request.param


def test_adb_hash_initially_empty_digest(adb_hash):
    """
    Assert that :class:`~adbpy.crypto.ADBHash` initially starts up with an empty digest.
    """
    assert not adb_hash.digest()


def test_adb_hash_appends_bytes(adb_hash, hash_bytes):
    """
    Assert that :class:`~adbpy.crypto.ADBHash` appends bytes to digest during update.
    """
    prev = adb_hash.digest()
    adb_hash.update(hash_bytes)
    assert prev + hash_bytes == adb_hash.digest()


def test_module_import_patches_rsa_package_globals():
    """
    Assert that importing the :mod:`~adbpy.crypto` package automatically patches the HASH_METHODS and HASH_ASN1
    globals with a :class:`~adbpy.crypto.ADBHash`.
    """
    import rsa

    hash_method = rsa.pkcs1.HASH_METHODS.get(crypto.PATCHED_HASH_KEY)
    hash_key = rsa.pkcs1.HASH_ASN1.get(crypto.PATCHED_HASH_KEY)

    assert hash_method == crypto.ADBHash
    assert hash_key == rsa.pkcs1.HASH_ASN1['SHA-1']


def test_pkcs_1_private_key_raises_on_empty_data():
    """
    Assert that :func:`~adbpy.crypyto._pkcs1_private_key_from_der_bytes` raises a :class:`~adbpy.crypto.KeyLoadError`
    exception when given an empty data buffer.
    """
    with pytest.raises(crypto.KeyLoadError):
        crypto._pkcs1_private_key_from_der_bytes(b'')


def test_pkcs_1_der_from_pkcs_8_raises_on_empty_data():
    """
    Assert that :func:`~adbpy.crypyto._pkcs1_der_from_pkcs8_bytes` raises a :class:`~adbpy.crypto.KeyLoadError`
    exception when given an empty data buffer.
    """
    with pytest.raises(crypto.KeyLoadError):
        crypto._pkcs1_der_from_pkcs8_bytes(b'')


def test_sign_raises_on_empty_path():
    """
    Assert that :func:`~adbpy.crypto.sign` raises a :class:`~ValueError`
    exception when given an empty path string.
    """
    with pytest.raises(ValueError):
        crypto.sign('', None)


@pytest.mark.xfail(reason='TODO')
def test_sign_raises_on_non_existent_path():
    """
    Assert that :func:`~adbpy.crypto.sign` raises a :class:`~ValueError`
    exception when given a file path that does not exist.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_sign_raises_on_malformed_pkcs8_pem_file():
    """
    Assert that :func:`~adbpy.crypto.sign` raises a :class:`~adbpy.crypto.KeyLoadError`
    exception when given a file path that points to a file containing malformed PKCS #8 PEM data.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_sign_raises_on_pkcs8_pem_file_without_identifier():
    """
    Assert that :func:`~adbpy.crypto.sign` raises a :class:`~adbpy.crypto.KeyLoadError`
    exception when given a file path that points to a PKCS #8 PEM file that does not contain an RSA identifier.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_sign_raises_on_pkcs8_pem_file_with_incorrect_identifier():
    """
    Assert that :func:`~adbpy.crypto.sign` raises a :class:`~adbpy.crypto.KeyLoadError`
    exception when given a file path that points to a PKCS #8 PEM file that does not contain the expected
    identifier (RSA).
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_sign_raises_on_pkcs8_pem_file_without_octet_bytes():
    """
    Assert that :func:`~adbpy.crypto.sign` raises a :class:`~adbpy.crypto.KeyLoadError`
    exception when given a file path that points to a PKCS #8 PEM file that does not contain the expected
    RSA private key bytes as octets.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_sign_returns_bytes_on_valid_input():
    """
    Assert that :func:`~adbpy.crypto.sign` returns a non-empty byte array (private key as octets) when given
    input to a valid PKCS #8 PEM file.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_sign_invokes_adb_hash_on_valid_input():
    """
    Assert that :func:`~adbpy.crypto.sign` invokes the :class:`~adbpy.crypto.ADBHash` instance that has been
    patched into the :mod:`~rsa` module.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_public_key_bytes_from_private_key_raises_on_non_existent_path():
    """
    Assert that :func:`~adbpy.crypto.public_key_bytes_from_private_key_path` raises a :class:`~ValueError`
    exception when given a file path that does not exist.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_public_key_bytes_from_private_key_raises_on_private_key_without_corresponding_public_key():
    """
    Assert that :func:`~adbpy.crypto.public_key_bytes_from_private_key_path` raises a :class:`~ValueError`
    exception when given a private key file path that does not have a corresponding public key.
    """
    assert False


@pytest.mark.xfail(reason='TODO')
def test_public_key_bytes_from_private_key_returns_bytes_on_valid_input():
    """
    Assert that :func:`~adbpy.crypto.public_key_bytes_from_private_key_path` returns a non-empty collection of bytes
    when given a valid private key path.
    """
    assert False


def test_public_key_bytes_from_private_key_raises_on_empty_path():
    """
    Assert that :func:`~adbpy.crypto.public_key_bytes_from_private_key_path` raises a :class:`~ValueError`
    exception when given an empty path string.
    """
    with pytest.raises(ValueError):
        crypto.public_key_bytes_from_private_key_path('')
