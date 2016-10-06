import asyncio
import logging

from aioreactive.abc import AsyncSource
from aioreactive.core import Subscription, chain_future

log = logging.getLogger(__name__)


class Unit(AsyncSource):
    def __init__(self, value):
        self._value = value

    async def __alisten__(self, sink):
        async def worker(value):
            try:
                await sink.send(value)
            except Exception as ex:
                try:
                    await sink.throw(ex)
                except Exception as ex:
                    log.error("Unhandled exception: ", ex)
                    return

            await sink.close()

        async def done():
            try:
                value = self._value.result()
            except asyncio.CancelledError:
                await sink.close()
            except Exception as ex:
                await sink.throw(ex)
            else:
                await worker(value)

        sub = Subscription()

        # Check if plain value or Future (async value)
        if hasattr(self._value, "add_done_callback"):
            self._value.add_done_callback(asyncio.ensure_future(done()))
            return chain_future(sub, self._value)
        else:
            asyncio.ensure_future(worker(self._value))

        return sub


def unit(value) -> AsyncSource:
    """Returns a source stream that sends a single value.

    Example:
    1. xs = unit(42)
    2. xs = unit(future)

    Keyword arguments:
    value -- Single value to send into the source stream.

    Returns a source stream that is sent the single specified value.
    """

    return Unit(value)
