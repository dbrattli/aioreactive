import logging
from typing import Any, Optional, TypeVar

from .types import AsyncObserver

TSource = TypeVar("TSource")

log = logging.getLogger(__name__)


def noop(*args: Any, **kw: Any) -> None:
    """No operation. Returns nothing"""
    pass


async def anoop(value: Optional[TSource] = None):
    """Async no operation. Returns nothing"""
    pass


class NoopObserver(AsyncObserver[TSource]):
    async def asend(self, value: TSource) -> None:
        log.debug("NoopSink:asend(%s)", str(value))
        pass

    async def athrow(self, error: Exception) -> None:
        log.debug("NoopSink:athrow(%s)", error)
        pass

    async def aclose(self) -> None:
        log.debug("NoopSink:aclose()")
        pass


noopobserver: NoopObserver[Any] = NoopObserver()
