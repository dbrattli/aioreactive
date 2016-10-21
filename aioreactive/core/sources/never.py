from aioreactive.core import AsyncSink, AsyncSource, AsyncSingleStream


class Never(AsyncSource):
    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        return AsyncSingleStream()


def never() -> AsyncSource:
    """Returns an asynchronous source where nothing happens.

    Example:
    xs = never()

    Returns a source steam where nothing happens.
    """

    return Never()
