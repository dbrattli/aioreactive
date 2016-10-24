import asyncio

from aioreactive.core import AsyncSink, AsyncSource


class Empty(AsyncSource):
    async def __astart__(self, sink: AsyncSink):
        """Start streaming."""

        async def worker():
            await sink.aclose()

        return asyncio.ensure_future(worker())


def empty() -> AsyncSource:
    """Returns an empty source sequence.

    1 - xs = empty()

    Returns a source sequence with no items."""

    return Empty()
