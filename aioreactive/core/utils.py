import logging
from . import typing

log = logging.getLogger(__name__)


def noop(*args, **kw):
    """No operation. Returns nothing"""
    pass


async def anoop(*args, **kw):
    """Async no operation. Returns nothing"""
    pass


class NoopSink(typing.AsyncSink):
    async def asend(self, value):
        log.debug("NoopSink:asend(%s)", value)
        pass

    async def athrow(self, ex):
        log.debug("NoopSink:athrow(%s)", ex)
        pass

    async def aclose(self):
        log.debug("NoopSink:aclose()")
        pass


noopsink = NoopSink()
