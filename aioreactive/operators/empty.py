import asyncio

from aioreactive.core import AsyncObserver, AsyncObservable


class Empty(AsyncObservable):
    async def __asubscribe__(self, sink: AsyncObserver):
        """Start streaming."""

        async def worker():
            await sink.aclose()

        return asyncio.ensure_future(worker())


def empty() -> AsyncObservable:
    """Returns an empty source sequence.

    1 - xs = empty()

    Returns a source sequence with no items."""

    return Empty()
