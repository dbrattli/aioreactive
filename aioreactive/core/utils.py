import logging
from . import typing

log = logging.getLogger(__name__)


def noop(*args, **kw) -> None:
    """No operation. Returns nothing"""
    pass


async def anoop(*args, **kw) -> None:
    """Async no operation. Returns nothing"""
    pass


class NoopObserver(typing.AsyncObserver):
    async def asend(self, value) -> None:
        log.debug("NoopSink:asend(%s)", value)
        pass

    async def athrow(self, ex) -> None:
        log.debug("NoopSink:athrow(%s)", ex)
        pass

    async def aclose(self) -> None:
        log.debug("NoopSink:aclose()")
        pass


noopobserver = NoopObserver()
