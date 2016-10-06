import asyncio

from aioreactive.abc import AsyncSink, AsyncSource


class Empty(AsyncSource):
    async def __alisten__(self, sink: AsyncSink):
        async def worker():
            await sink.close()

        return asyncio.ensure_future(worker())


def empty() -> AsyncSource:
    """Returns an empty source sequence.using

    1 - xs = empty()

    Returns a source sequence with no elements."""

    return Empty()
