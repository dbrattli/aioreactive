import logging
from typing import Any, TypeVar

from .types import AsyncObserver


_TSource = TypeVar("_TSource")

log = logging.getLogger(__name__)


def noop(*args: Any, **kw: Any) -> None:
    """No operation. Returns nothing."""


async def anoop(value: Any | None = None) -> None:
    """Async no operation. Returns nothing."""


class NoopObserver(AsyncObserver[_TSource]):
    async def asend(self, value: _TSource) -> None:
        log.debug("NoopSink:asend(%s)", str(value))

    async def athrow(self, error: Exception) -> None:
        log.debug("NoopSink:athrow(%s)", error)

    async def aclose(self) -> None:
        log.debug("NoopSink:aclose()")


noopobserver: NoopObserver[Any] = NoopObserver()
