"""
    adbpy.crypto
    ~~~~~~~~~~~~

    Contains functionality for dealing with RSA keys required for auth between host and device.
"""

import io
import os
import rsa

from pyasn1.type.univ import ObjectIdentifier
from pyasn1.codec.der import decoder

from rsa import pem


__all__ = ['sign', 'public_key_bytes_from_private_key_path', 'KeyLoadError', 'KeySignError']


#: Key marker used to identify "header" and "footer" of PKCS #8 key.
PKCS8_PRIVATE_KEY_MARKER = 'PRIVATE KEY'


#: Identifier for RSA encryption.
#: http://www.alvestrand.no/objectid/1.2.840.113549.1.1.1.html
RSA_OID = ObjectIdentifier('1.2.840.113549.1.1.1')


#: Name of hash function to use with a patched `rsa` module instead of 'SHA-1'
#: since `adbd` sends us an already hashed data payload.
PATCHED_HASH_KEY = 'ADB'


class KeyLoadError(Exception):
    """
    Exception raised when loading of the private key fails.
    """


class KeySignError(Exception):
    """
    Exception raised when signing of data with the key fails.
    """


def sign(path, data):
    """
    Sign the given bytes using the private key at the specified path.

    :param path: Path to private key to sign bytes with
    :param data: Bytes of data to sign
    :return: Signed bytes
    """
    private_key = _private_key_from_path(path)
    return rsa.sign(data, private_key, PATCHED_HASH_KEY)


def public_key_bytes_from_private_key_path(path):
    """
    Get the bytes of the public key for the corresponding private key file path.

    Note: This expects the public key to follow the format: "{path_to_private_key}.pub".

    :param path: Path to private key
    :return: Bytes of public key
    """
    if not path:
        raise ValueError('Path required')

    if not os.path.exists(path):
        raise ValueError('Private key path {} does not exist'.format(path))

    public_key_path = '{}.pub'.format(path)

    if not os.path.exists(public_key_path):
        raise ValueError('Public key path {} does not exist'.format(path))

    with io.open(public_key_path, 'rb') as public_key:
        return public_key.read()


def _private_key_from_path(path):
    """
    Load the PKCS #8 RSA private key from the given path.

    :param path: Path to PKCS #8 RSA key to load
    :return: A :class:`~rsa.PrivateKey` instance
    """
    if not path:
        raise ValueError('Path required')

    if not os.path.exists(path):
        raise ValueError('Private key path {} does not exist'.format(path))

    with io.open(path, 'rb') as private_key:
        pkcs1 = _pkcs1_der_from_pkcs8_bytes(private_key.read())
        return _pkcs1_private_key_from_der_bytes(pkcs1)


def _pkcs1_der_from_pkcs8_bytes(pkcs8):
    """
    Given a PKCS #8 key, extract the PKCS #1 DER from it.

    RFC: https://tools.ietf.org/html/rfc5208

    :param pkcs8: Bytes read from a PKCS #8 key
    :return: Bytes of PKCS #1 private key extracted from PKCS #8 key
    """
    # Load PKCS #8 PEM and decode it from b64 to ASN sequence.
    try:
        pkcs8_pem = pem.load_pem(pkcs8, PKCS8_PRIVATE_KEY_MARKER)
        private_key_info, _ = decoder.decode(pkcs8_pem)
    except Exception:
        raise KeyLoadError('Unable to load/decode PKCS #8 RSA key')

    # Try and pop out the version from the key info and validate that we're consuming an RSA key.
    try:
        identifier = private_key_info[1][0]
    except Exception:
        raise KeyLoadError('Unable to find algorithm identifier in sequence')
    else:
        if identifier != RSA_OID:
            raise KeyLoadError('Got algorithm identifier {}, expected {}', identifier, RSA_OID)

    # Try and pull out octet bytes from the private key.
    try:
        octet_str = private_key_info[2]
    except Exception:
        raise KeyLoadError('Unable to get octet bytes from private key')
    else:
        return octet_str.asOctets()


def _pkcs1_private_key_from_der_bytes(pkcs1_der):
    """
    Given a collection of bytes that represent a PKCS #1 in DER format, convert it to an
    :class:`~rsa.PrivateKey` instance.

    :param pkcs1_der: PKCS #1 DER format in bytes
    :return: A :class:`~rsa.PrivateKey` instance from PKCS #1 data
    """
    try:
        return rsa.PrivateKey.load_pkcs1(pkcs1_der, format='DER')
    except Exception:
        raise KeyLoadError('Failed to load RSA private key from PKCS #1 DER format')


class ADBHash(object):
    """
    A "nop" hash.

    During the authentication phase of connection between ADB endpoints, `adbd` will respond
    to a CNXN request with an AUTH response (in arg0) and a hashed data value. `adbd` expects
    the other end of the connection to sign the hashed data value and send it back, so it can confirm
    that the other end of the connection is using a trusted SHA key. If the key is not trusted, the device
    will generate a prompt that requires user interaction to accept.

    Since this value was already hashed, we need to create a "nop" hash that stops the `rsa` module
    from hashing it a second time. Otherwise, the device will _always_ think that the other end of the connection
    is using a new, untrusted RSA key.

    ---

    Per :mod:`~hashlib` documentation:

    Hash objects have these methods:
     - update(arg): Update the hash object with the bytes in arg. Repeated calls
                    are equivalent to a single call with the concatenation of all
                    the arguments.
     - digest():    Return the digest of the bytes passed to the update() method
                    so far.
     - hexdigest(): Like digest() except the digest is returned as a unicode
                    object of double length, containing only hexadecimal digits.
     - copy():      Return a copy (clone) of the hash object. This can be used to
                    efficiently compute the digests of strings that share a common
                    initial substring.
    """

    def __init__(self):
        self.bytes = bytes()

    def update(self, data):
        self.bytes += data

    def digest(self):
        return self.bytes

    def hexdigest(self):
        raise NotImplementedError('hexdigest not supported on {}'.format(self.__class__.__name__))

    def copy(self):
        raise NotImplementedError('copy not supported on {}'.format(self.__class__.__name__))


# Patch `rsa` module with our "nop" hash functionality.
rsa.pkcs1.HASH_METHODS[PATCHED_HASH_KEY] = ADBHash
rsa.pkcs1.HASH_ASN1[PATCHED_HASH_KEY] = rsa.pkcs1.HASH_ASN1['SHA-1']
