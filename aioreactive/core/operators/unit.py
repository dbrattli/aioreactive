import asyncio
import logging

from aioreactive.core import AsyncObservable
from aioreactive.core import AsyncSingleStream, chain_future

log = logging.getLogger(__name__)


class Unit(AsyncObservable):

    def __init__(self, value) -> None:
        self._value = value

    async def __asubscribe__(self, observer) -> AsyncSingleStream:
        """Start streaming."""

        async def worker(value) -> None:
            """Task for sending value."""

            try:
                log.debug("Unit:__asubscribe__:worker:sending: %s", value)
                await observer.asend(value)
            except Exception as ex:
                try:
                    await observer.athrow(ex)
                except Exception as ex:
                    log.error("Unhandled exception: ", ex)
                    return

            await observer.aclose()

        async def done() -> None:
            """Called when future resolves."""

            try:
                value = self._value.result()
            except asyncio.CancelledError:
                await observer.aclose()
            except Exception as ex:
                try:
                    await observer.athrow(ex)
                except Exception as ex:
                    log.error("Unhandled exception: ", ex)
                    return
            else:
                await worker(value)

        def done_callback(fut):
            asyncio.ensure_future(done())

        fut = AsyncSingleStream()

        # Check if plain value or Future (async value)
        if hasattr(self._value, "add_done_callback"):
            self._value.add_done_callback(done_callback)
            return chain_future(fut, self._value)
        else:
            asyncio.ensure_future(worker(self._value))

        log.debug("Unit:done")
        return fut


def unit(value) -> AsyncObservable:
    """Returns a source stream that sends a single value.

    Example:
    1. xs = unit(42)
    2. xs = unit(future)

    Keyword arguments:
    value -- Single value to send into the source stream.

    Returns a source stream that is sent the single specified value.
    """

    return Unit(value)
