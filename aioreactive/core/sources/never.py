from aioreactive.core import AsyncSink, AsyncSource, Subscription


class Never(AsyncSource):
    async def __alisten__(self, sink: AsyncSink) -> Subscription:
        return Subscription()


def never() -> AsyncSource:
    """Returns an asynchronous source where nothing happens.

    Example:
    xs = never()

    Returns a source steam where nothing happens.
    """

    return Never()
