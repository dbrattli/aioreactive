"""Internal messages used by mailbox processors. Do not import or use.
"""
from dataclasses import dataclass
from typing import Generic, TypeVar

from expression.system import AsyncDisposable

from .notification import Notification
from .observables import AsyncObservable

TSource = TypeVar("TSource")


class Msg:
    """Message base class"""

    ...


@dataclass
class SourceMsg(Msg, Generic[TSource]):
    value: Notification[TSource]


@dataclass
class OtherMsg(Msg, Generic[TSource]):
    value: Notification[TSource]


@dataclass
class DisposableMsg(Msg, Generic[TSource]):
    """Message containing a diposable."""

    disposable: AsyncDisposable


@dataclass
class InnerObservableMsg(Msg, Generic[TSource]):
    """Message containing an inner observable."""

    inner_observable: AsyncObservable[TSource]


@dataclass
class InnerCompletedMsg(Msg):
    """Message notifying that the inner observable completed."""

    key: int


class CompletedMsg(Msg, Generic[TSource]):
    """Message notifying that the observable sequence completed."""

    pass


CompletedMsg_ = CompletedMsg()  # Singleton


class DisposeMsg(Msg, Generic[TSource]):
    """Message notifying that the operator got disposed."""

    pass


DisposeMsg_ = DisposeMsg()  # Singleton

__all__ = ["Msg", "DisposeMsg", "CompletedMsg", "InnerCompletedMsg", "InnerObservableMsg", "DisposableMsg"]
