"""Internal messages used by mailbox processors. Do not import or use."""

from typing import Generic, Literal, NewType, TypeVar

from expression import case, tag, tagged_union
from expression.system import AsyncDisposable

from .notification import Notification
from .types import AsyncObservable


_TSource = TypeVar("_TSource")

Key = NewType("Key", int)


@tagged_union(frozen=True)
class Msg(Generic[_TSource]):
    """Message tagged union."""

    tag: Literal[
        "source",
        "other",
        "dispose",
        "disposable",
        "inner_observable",
        "inner_completed",
        "completed",
    ] = tag()

    source: Notification[_TSource] = case()
    other: Notification[_TSource] = case()
    dispose: Literal[True] = case()
    disposable: AsyncDisposable = case()
    inner_observable: AsyncObservable[_TSource] = case()
    inner_completed: Key = case()
    completed: Literal[True] = case()


__all__ = ["Msg"]
