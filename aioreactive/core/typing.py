from typing import Generic, TypeVar

from . import abc

T_co = TypeVar('T_co', covariant=True)  # Any type covariant containers.
T_contra = TypeVar('T_contra', contravariant=True)  # Ditto contravariant.


class Observable(Generic[T_co], abc.Observable):
    """A generic version of aioreactive.abc.Source."""

    __slots__ = ()


class AsyncObservable(Generic[T_co], abc.AsyncObservable):
    """A generic version of aioreactive.abc.AsyncObservable."""

    __slots__ = ()


class Observer(Generic[T_contra], abc.Observer):
    """A generic version of aioreactive.abc.Sink."""

    __slots__ = ()


class AsyncObserver(Generic[T_contra], abc.AsyncObserver):
    """A generic version of aioreactive.abc.AsyncObserver."""

    __slots__ = ()
