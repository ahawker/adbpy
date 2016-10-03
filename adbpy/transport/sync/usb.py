"""
    adbpy.transport.sync.usb
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Contains functionality for a synchronous (blocking) USB transport powered by `libusb`.
"""

import functools
import logging
import usb1

from adbpy import iterutil, transport


__all__ = ['Context', 'Transport']


LOGGER = logging.getLogger(__name__)
WIRE_LOGGER = LOGGER.getChild('wire')


#: Default timeout in milliseconds for a USB transport connect attempt.
DEFAULT_CONNECT_TIMEOUT_MS = 0

#: Default timeout in milliseconds for a USB transport disconnect attempt.
DEFAULT_DISCONNECT_TIMEOUT_MS = 0

#: Default timeout in milliseconds for a USB transport send attempt.
DEFAULT_SEND_TIMEOUT_MS = 0

#: Default timeout in milliseconds for a USB transport receive attempt.
DEFAULT_RECV_TIMEOUT_MS = 0

#: USB interface endpoint address flag value indicating it is used for reading.
ENDPOINT_DIRECTION_IN = 0x80


class USBError(transport.TransportError):
    """
    Generic exception for USB transport related errors.
    """


class USBHandleRequiredError(USBError):
    """
    Exception raised when a function decorated with :func:`~adbpy.transport.sync.usb.requires_handle` does not
    receive a valid handle object.
    """


class USBDeviceNotFound(USBError):
    """
    Exception raised when the transport cannot communicate with a specific USB device.
    """


class USBDeviceAccessDenied(USBError):
    """
    Exception raised when the transport does not have access to the USB device interface.
    """


class Context:
    """
    Transport context object returned by :meth:`~adbpy.transport.sync.usb.Transport.connect`.
    """

    __slots__ = ['ctx', 'device', 'settings', 'read_endpoint', 'read_endpoint_address', 'write_endpoint',
                 'write_endpoint_address', 'handle', 'interface']

    def __init__(self, ctx, device, settings, read_endpoint, write_endpoint, handle, interface):
        self.ctx = ctx
        self.device = device
        self.settings = settings
        self.read_endpoint = read_endpoint
        self.read_endpoint_address = read_endpoint.getAddress() if read_endpoint else ''
        self.write_endpoint = write_endpoint
        self.write_endpoint_address = write_endpoint.getAddress() if write_endpoint else ''
        self.handle = handle
        self.interface = interface


def requires_handle(func):
    """
    Decorator that enforces the first function argument to be a :class:`~adbpy.transport.sync.usb.Context` object
    with a valid handle set.
    """
    @functools.wraps(func)
    def decorator(self, context, *args, **kwargs):
        if not context.handle:
            raise USBHandleRequiredError('{} requires an open handle'.format(func.__name__))
        return func(self, context, *args, **kwargs)
    return decorator


def libusb_exception_handler(func):
    """
    Decorator that catches low level exceptions from the :mod:`libusb` module and re-raises `adbpy` specific
    exceptions instead.
    """
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except usb1.USBError as e:
            if e.value == usb1.ERROR_NO_DEVICE:
                raise USBDeviceNotFound('Device has been disconnected')
            elif e.value == usb1.ERROR_ACCESS:
                raise USBDeviceAccessDenied('Insufficient permissions or interface is already claimed')
            elif e.value == usb1.ERROR_TIMEOUT:
                raise transport.TransportTimeoutError('Exceeded timeout')
            else:
                raise USBError('Unhandled USB error: {}'.format(getattr(e, '__name__', str(e))))
    return decorator


class Transport(transport.Transport):
    """
    Class for interacting with a synchronous (blocking) USB device.
    """

    def __init__(self, serial=None, vid=None, pid=None, usb_class=None, usb_subclass=None, usb_protocol=None):
        self._serial = serial
        self._vid = vid
        self._pid = pid
        self._usb_class = usb_class
        self._usb_subclass = usb_subclass
        self._usb_protocol = usb_protocol

    def __repr__(self):
        s = _usb_filter_str(self._serial, self._vid, self._pid, self._usb_class, self._usb_subclass, self._usb_protocol)
        return '<{}({})>'.format(self.__class__.__name__, s)

    @transport.rethrow_timeout_exception(transport.TransportTimeoutError, transport.TransportConnectTimeout)
    @libusb_exception_handler
    def connect(self, libusb_ctx=None, timeout=DEFAULT_CONNECT_TIMEOUT_MS):
        """
        Connect to a USB device at the defined serial/vid/pid.

        :param libusb_ctx: Optional :class:`~usb1.USBContext` object to re-use
        :param timeout: Optional timeout in milliseconds to use when connecting to the device
        :return: A :class:`~adbpy.transport.sync.usb.Context` instance used to communicate with a USB device
        """
        # Create or re-use a libusb USBContext for every separate connection. This should
        # work just fine and allow us to configure them independently.
        ctx = _open_context(libusb_ctx)

        # Grab the first device based on the optional serial/vid/pid criteria. If no filters are given, this will
        # yield back the first USB device of the supported class/subclass/protocol. If none are found, an exception is
        # thrown.
        device, settings = _find_device_by_serial_vid_pid(ctx, self._serial, self._vid, self._pid,
                                                          self._usb_class, self._usb_subclass, self._usb_protocol)

        # Grab the first read/write endpoints for the device we're using. These are used for future read/write calls.
        read_endpoint = _find_device_read_endpoint(settings)
        write_endpoint = _find_device_write_endpoint(settings)

        # Open a new handle and connect/claim our target interface. This will hold it for libusb so it won't
        # be accessible to other consumers until we release it.
        handle, interface = _open_device_handle(device, settings)

        # Detach existing kernel driver if it happens to be there.
        _detach_kernel_interface(handle, interface)

        # Claim the device interface. Doing so means this device will not be usable from other USB clients,
        # such as other command-line tools.
        _claim_interface(handle, interface)

        return Context(ctx, device, settings, read_endpoint, write_endpoint, handle, interface)

    @transport.requires_context(Context)
    @requires_handle
    @transport.rethrow_timeout_exception(transport.TransportTimeoutError, transport.TransportDisconnectTimeout)
    @libusb_exception_handler
    def disconnect(self, context, timeout=DEFAULT_DISCONNECT_TIMEOUT_MS):
        """
        Disconnect from the USB device managed by the given conext object.

        :param context: A :class:`~adbpy.transport.sync.usb.Context` object whose device we want to disconnect
        :param timeout: Optional timeout in milliseconds to use when disconnecting from the device
        :return: `None`
        """
        _release_interface(context.handle, context.interface)
        _close_handle(context.handle)
        _close_context(context.ctx)

    @transport.requires_context(Context)
    @requires_handle
    @transport.rethrow_timeout_exception(transport.TransportTimeoutError, transport.TransportSendTimeout)
    @libusb_exception_handler
    def send(self, context, data, timeout=DEFAULT_SEND_TIMEOUT_MS):
        """
        Send data to the USB device managed by the given context object in a synchronous (blocking) call.

        :param context: A :class:`~adbpy.transport.sync.usb.Context` object whose device we want to send data to
        :param data: Byte buffer payload to write to the USB device
        :param timeout: Optional timeout in milliseconds to use when sending to the device
        :return: `None`
        """
        endpoint_address = context.write_endpoint_address
        return _write_bytes_to_endpoint_address(context.handle, endpoint_address, data, timeout)

    @transport.requires_context(Context)
    @requires_handle
    @transport.rethrow_timeout_exception(transport.TransportTimeoutError, transport.TransportReceiveTimeout)
    @libusb_exception_handler
    def recv(self, context, num_bytes, timeout=DEFAULT_RECV_TIMEOUT_MS):
        """
        Receive data from the USB device managed by the given context object in a synchronous (blocking) call.

        :param context: A :class:`~adbpy.transport.sync.usb.Context` object whose device we want to receive data from
        :param num_bytes: Number of bytes to read from the device
        :param timeout: Optional timeout in milliseconds to use when receiving from the socket
        :return: A :class:`~bytes` buffer containing data read from the device
        """
        endpoint_address = context.read_endpoint_address
        return _read_bytes_from_endpoint_address(context.handle, endpoint_address, num_bytes, timeout)


def _usb_filter_str(serial, vid, pid, usb_class, usb_subclass, usb_protocol):
    """
    Build a human readable string from the given USB device filter params.

    :param serial: Device serial number
    :param vid: Device vendor ID
    :param pid: Device product ID
    :param usb_class: Device USB class
    :param usb_subclass: Device USB subclass
    :param usb_protocol: Device USB protocol
    :return: A :class:`~str` containing information about the USB device filter params
    """
    filter_vars = locals()
    return ', '.join(('{}={}'.format(k, filter_vars[k]) for k in
                      ('serial', 'vid', 'pid', 'usb_class', 'usb_subclass', 'usb_protocol')))


def _open_context(libusb_ctx=None):
    """
    Create and open a :class:`~usb1.USBContext` instance used for communicating with `libusb`.

    :param libusb_ctx: Optional :class:`~usb1.USBContext` instance to re-use
    :return: A :class:`~usb1.USBContext` instance
    """
    ctx = libusb_ctx or usb1.USBContext().open()
    LOGGER.debug('Using USB context {}'.format(id(ctx)))
    return ctx


def _find_device_by_serial_vid_pid(ctx, serial, vid, pid, usb_class, usb_subclass, usb_protocol):
    """
    Find the first USB device that matches the given serial, vid, or pid. If a match is found, return a tuple
    of the :class:`~usb1.USBDevice` instance and :class:`~usb1.USBInterfaceSetting` for the matching device.

    If no device is found matching the given criteria, raise a :class:`~adbpy.transport.sync.usb.USBDeviceNotFound`
    exception.

    :param ctx: A :class:`~usb1.USBContext` instance used to query local USB devices
    :param serial: Serial number of local USB device we want
    :param vid: Vendor ID of USB device we want
    :param pid: Product ID of USB device we want
    :param usb_class: Specific class of local USB device we want
    :param usb_subclass: Specific subclass of USB device we want
    :param usb_protocol: Specific protocol of USB device we want
    :return: A :class:`tuple` of :class:`~usb1.USBDevice` instance and :class:`~usb1.USBInterfaceSetting`
    """
    filter_str = _usb_filter_str(serial, vid, pid, usb_class, usb_subclass, usb_protocol)
    try:
        LOGGER.debug('Looking for USB device with filter {}').format(filter_str)
        device, settings = iterutil.first(_yield_matching_devices, ctx, serial, vid, pid,
                                          usb_class, usb_subclass, usb_protocol)
    except iterutil.IterableEmpty:
        raise USBDeviceNotFound('No matching device for filter {}'.format(filter_str))
    else:
        LOGGER.debug('Found USB device with serial={}, vid={}, pid={}'.format(device.getSerialNumber(),
                                                                              device.getVendorID(),
                                                                              device.getProductID()))
        return device, settings


def _find_device_read_endpoint(settings):
    """
    Find the correct USB endpoint for reading from the device.

    :param settings: A :class:`~usb1.USBSetting` instance to scan endpoints for
    :return: A :class:`~usb1.USBEndpoint` instance that we can read from
    """
    read_endpoint = iterutil.first(_yield_read_endpoints, settings)
    LOGGER.debug('Found read endpoint at address {}'.format(read_endpoint.getAddress()))
    return read_endpoint


def _find_device_write_endpoint(settings):
    """
    Find the correct USB endpoint for writing to the device.

    :param settings: A :class:`~usb1.USBSetting` instance to scan endpoints for
    :return: A :class:`~usb1.USBEndpoint` instance that we can write to
    """
    write_endpoint = iterutil.first(_yield_write_endpoints, settings)
    LOGGER.debug('Found write endpoint at address {}'.format(write_endpoint.getAddress()))
    return write_endpoint


def _open_device_handle(device, settings):
    """
    Open the given device and get a handle used to communicate with it.

    :param device: A :class:`~usb1.USBDevice` to open
    :param settings: A :class:`~usb1.USBSetting` for the given device
    :return: A tuple of :class:`usb1.USBDeviceHandle` and :class:`int` representing the interface number
    """
    handle, interface = device.open(), settings.getNumber()
    LOGGER.debug('Opened USB device handle {} with interface {}'.format(id(handle), interface))
    return handle, interface


def _detach_kernel_interface(handle, interface):
    """
    Detach any active kernel driver for the given interface number.

    :param handle: A :class:`~usb1.USBDeviceHandle` to modify
    :param interface: A :class:`int` that represents the interface to detach
    :return: `None`
    """
    if handle.kernelDriverActive(interface):
        LOGGER.debug('Detaching existing kernel driver for interface {}'.format(interface))
        handle.detachKernelDriver(interface)


def _claim_interface(handle, interface):
    """
    Claim the given interface for use.

    A claimed interface will make it unusable to other consumers outside of `libusb`.

    :param handle: A :class:`~usb1.USBDeviceHandle` to modify
    :param interface: A :class:`int` that represents the interface to claim
    :return: `None`
    """
    LOGGER.debug('Claiming interface {}'.format(interface))
    handle.claimInterface(interface)


def _release_interface(handle, interface):
    """
    Release a previously claimed interface.

    Releasing a claimed interface will enable it for use by consumers outside of `libusb`.

    :param handle: A :class:`~usb1.USBDeviceHandle` to modify
    :param interface: A :class:`int` that represents the interface to release
    :return: `None`
    """
    LOGGER.debug('Releasing interface {}'.format(interface))
    handle.releaseInterface(interface)


def _close_handle(handle):
    """
    Close the given USB handle.

    :param handle: A :class:`~usb1.USBDeviceHandle` to close
    :return: `None`
    """
    LOGGER.debug('Closing USB device handle {}'.format(id(handle)))
    handle.close()


def _close_context(ctx):
    """
    Close the given USB context.

    :param ctx: A :class:`~usb1.USBContext` to close
    :return: `None`
    """
    LOGGER.debug('Exiting USB context {}'.format(id(ctx)))
    ctx.exit()


def _write_bytes_to_endpoint_address(handle, endpoint_address, data, timeout):
    """
    Write a buffer of bytes to a given USB device endpoint.

    :param handle: A :class:`~usb1.USBDeviceHandle` that manages the endpoint
    :param endpoint_address: Address of the USB endpoint to write to
    :param data: Buffer to write
    :param timeout: Timeout in milliseconds for the write to complete
    :return: A :class:`~int` that represents the number of bytes actually written to the endpoint
    """
    LOGGER.debug('Writing data to endpoint_address={}, timeout={}, length={}'.format(endpoint_address,
                                                                                     timeout, len(data)))

    if WIRE_LOGGER.isEnabledFor(logging.DEBUG):
        WIRE_LOGGER.debug('>>> {}'.format(data))

    return handle.bulkWrite(endpoint_address, data, timeout)


def _read_bytes_from_endpoint_address(handle, endpoint_address, num_bytes, timeout):
    """
    Read a buffer of bytes from the given USB device endpoint.

    :param handle: A :class:`~usb1.USBDeviceHandle` that manages the endpoint
    :param endpoint_address: Address of the USB endpoint to read from
    :param num_bytes: Number of bytes to read
    :param timeout: Timeout in milliseconds for the read to complete
    :return: A :class:`~bytes` buffer of data read from the endpoint
    """
    LOGGER.debug('Reading data from endpoint_address={}, timeout={}, length={}'.format(endpoint_address,
                                                                                       timeout, num_bytes))

    data = handle.bulkRead(endpoint_address, num_bytes, timeout)

    if WIRE_LOGGER.isEnabledFor(logging.DEBUG):
        WIRE_LOGGER.debug('<<< {}'.format(data))

    return data


def _is_read_endpoint(address):
    """
    Check to see if the given address is a read endpoint.

    :param address: Address to check
    :return: A :class:`bool` indicating if the endpoint is for reading
    """
    return address & ENDPOINT_DIRECTION_IN == ENDPOINT_DIRECTION_IN


def _is_write_endpoint(address):
    """
    Check to see if the given address is a write endpoint.

    :param address: Address to check
    :return: A :class:`bool` indicating if the endpoint is for writing
    """
    return not _is_read_endpoint(address)


def _yield_read_endpoints(setting):
    """
    Generator function that yields back USB interface endpoints that support reading.

    :param setting: USB device setting to check for endpoints
    """
    return filter(lambda endpoint: _is_read_endpoint(endpoint.getAddress()), setting.iterEndpoints())


def _yield_write_endpoints(settings):
    """
    Generator function that yields back USB interface endpoints that support writing.

    :param setting: USB device setting to check for endpoints
    """
    return filter(lambda endpoint: _is_write_endpoint(endpoint.getAddress()), settings.iterEndpoints())


def _yield_devices(ctx):
    """
    Generator function that yields back a tuple of USB device and settings for all local USB devices.

    :param ctx: A :class:`~usb1.USBContext` instance used to query available USB devices
    :return: Generator that yields back matching :class:`~usb1.USBDevice` and :class:`~usb1.USBInterfaceSetting` tuples
    """
    for device in ctx.getDeviceList(skip_on_error=True):
        for setting in device.iterSettings():
            yield device, setting


def _yield_matching_devices(ctx, serial, vid, pid, usb_class, usb_subclass, usb_protocol):
    """
    Generator function that yields back devices that meet the given filter criteria.

    :param ctx: A :class:`~usb1.USBContext` instance used to query for USB devices.
    :param serial: USB serial number filter
    :param vid: USB vendor id filter
    :param pid: USB product id filter
    :param usb_class: USB class filter
    :param usb_subclass: USB subclass filter
    :param usb_protocol: USB protocol filter
    :return: Generator that yield back :class:`~usb1.USBDevice` instances that match all filters
    """
    def _is_match(device, setting):
        """
        Predicate function that returns `True` when a USB device matches all requirements and `False` otherwise.
        """
        serial_match = not serial or device.getSerialNumber() == serial
        vid_match = not vid or device.getVendorId() == vid
        pid_match = not pid or device.getProductId() == pid
        usb_class_match = not usb_class or setting.getClass() == usb_class
        usb_subclass_match = not usb_subclass or setting.getSubClass() == usb_subclass
        usb_protocol_match = not usb_protocol or setting.getProtocol() == usb_protocol
        return all((serial_match, vid_match, pid_match, usb_class_match, usb_subclass_match, usb_protocol_match))

    return (device for device in _yield_devices(ctx) if _is_match(*device))
