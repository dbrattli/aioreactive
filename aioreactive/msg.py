"""Internal messages used by mailbox processors. Do not import or use."""
from abc import ABC
from dataclasses import dataclass
from typing import Any, Generic, NewType, TypeVar

from expression.system import AsyncDisposable

from .notification import Notification
from .types import AsyncObservable


_TSource = TypeVar("_TSource")
_TOther = TypeVar("_TOther")

Key = NewType("Key", int)


class Msg(Generic[_TSource], ABC):
    """Message base class."""


@dataclass
class SourceMsg(Msg[_TSource]):
    value: Notification[_TSource]


@dataclass
class OtherMsg(
    Msg[Notification[_TOther]],
):
    value: Notification[_TOther]


@dataclass
class DisposableMsg(Msg[AsyncDisposable]):
    """Message containing a diposable."""

    disposable: AsyncDisposable


@dataclass
class InnerObservableMsg(Msg[_TSource]):
    """Message containing an inner observable."""

    inner_observable: AsyncObservable[_TSource]


@dataclass
class InnerCompletedMsg(Msg[_TSource]):
    """Message notifying that the inner observable completed."""

    key: Key


class CompletedMsg_(Msg[Any]):
    """Message notifying that the observable sequence completed."""


CompletedMsg = CompletedMsg_()  # Singleton


class DisposeMsg_(Msg[None]):
    """Message notifying that the operator got disposed."""


DisposeMsg = DisposeMsg_()  # Singleton


__all__ = [
    "Msg",
    "DisposeMsg",
    "CompletedMsg",
    "InnerCompletedMsg",
    "InnerObservableMsg",
    "DisposableMsg",
]
