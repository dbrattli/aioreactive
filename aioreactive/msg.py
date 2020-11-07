from dataclasses import dataclass
from typing import Generic, TypeVar

from expression.system import AsyncDisposable

from .observables import AsyncObservable

TSource = TypeVar("TSource")


class Msg:
    ...


@dataclass
class DisposableMsg(Msg):
    disposable: AsyncDisposable


@dataclass
class InnerObservableMsg(Msg, Generic[TSource]):
    inner_observable: AsyncObservable[TSource]


@dataclass
class InnerCompletedMsg(Msg):
    key: int


class OuterCompletedMsg(Msg):
    pass


OuterCompletedMsg_ = OuterCompletedMsg()  # Singleton


class DisposeMsg(Msg):
    pass


DisposeMsg_ = DisposeMsg()  # Singleton
