# adbpy
Python implementation of the Android Debug Bridge (ADB) protocol using `libusb` and `asyncio`.

### Installation

To install adbpy from [pip](https://pypi.python.org/pypi/pip):
```bash
    $ pip install adbpy
```

To install adbpy from source:
```bash
    $ git clone git@github.com:ahawker/adbpy.git
    $ cd adbpy
    $ python setup.py install
```

### API - TBD

```
What _should_ the API look like?

# Synchronous Interface
from adb import Device

devices = Device.devices()
[('DEVICE, '12393012'), ('EMULATOR', '???'), ('127.0.0.1', '44444')]

device = Device.from_serial('0123456789ABCDEF')
device = Device.from_tcp('127.0.0.1', 5555)

# ADB Interface
device.adb.push(...)
device.adb.pull(...)

device.adb.sync(...)

device.adb.shell(...)  # Interactive?

device.adb.shell(...)  # Command
device.adb.shell.{command}(...)

# Logcat needs to support both command & interactive...
device.adb.logcat(...)

device.adb.forward(...)
device.adb.forward.remove(...)


# Asynchronous Interface
from adb.aio import AsyncDevice

devices = yield from AsyncDevice.devices()

device = yield from AsyncDevice.from_serial('0123456789ABCDEF')
device = yield from AsyncDevice.from_tcp('127.0.0.1', 5555)_
_
```

### License

[Apache 2.0](LICENSE)
