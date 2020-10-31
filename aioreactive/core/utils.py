import logging
from typing import Optional, TypeVar

from .types import AsyncObserver

TSource = TypeVar("TSource")

log = logging.getLogger(__name__)


def noop(*args, **kw) -> None:
    """No operation. Returns nothing"""
    pass


async def anoop(value: Optional[TSource] = None):
    """Async no operation. Returns nothing"""
    pass


class NoopObserver(AsyncObserver):
    async def asend(self, value) -> None:
        log.debug("NoopSink:asend(%s)", str(value))
        pass

    async def athrow(self, ex) -> None:
        log.debug("NoopSink:athrow(%s)", ex)
        pass

    async def aclose(self) -> None:
        log.debug("NoopSink:aclose()")
        pass


noopobserver = NoopObserver()
