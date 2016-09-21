"""
    adbpy
    ~~~~~

    Python implementation of the Android Debug Bridge (ADB) protocol.
"""


def get_event_loop():
    """
    Return the default `asyncio` event loop with conditional `create_task` patch
    for versions < 3.4.2.
    """
    import asyncio
    import types

    loop = asyncio.get_event_loop()

    # Patch `create_task` method on loop if running older than 3.4.2.
    if not hasattr(loop, 'create_task'):
        loop.create_task = types.MethodType(lambda loop, coro: asyncio.async(coro, loop=loop), loop)

    return loop


__version__ = '0.0.1'
