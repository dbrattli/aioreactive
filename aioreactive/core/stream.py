import logging

from aioreactive.abc import AsyncSink

from .futures import Subscription

log = logging.getLogger(__name__)


class Stream(AsyncSink):
    """The Stream.

    The stream is both a source and a sink. Thus you can both listen
    to it and send values to it. Any values send will be forwarded to
    all listeners.
    """

    def __init__(self):
        self._sinks = {}

    async def send(self, value):
        for sink, sub in list(self._sinks.items()):
            await sink.send(value)

    async def throw(self, ex):
        for sink, sub in list(self._sinks.items()):
            await sink.throw(ex)
            sub.set_exception(ex)

    async def close(self):
        for sink, sub in list(self._sinks.items()):
            await sink.close()

    async def __alisten__(self, sink):
        sub = Subscription()
        self._sinks[sink] = sub

        def done(sub):
            log.debug("Stream:done()")
            if sink in self._sinks:
                del self._sinks[sink]

        sub.add_done_callback(done)
        return sub
