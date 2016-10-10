from typing import Generic, TypeVar

from . import abc

T_co = TypeVar('T_co', covariant=True)  # Any type covariant containers.
T_contra = TypeVar('T_contra', contravariant=True)  # Ditto contravariant.


class Source(Generic[T_co], abc.Source):
    """A generic version of aioreactive.abc.Source."""

    __slots__ = ()


class AsyncSource(Generic[T_co], abc.AsyncSource):
    """A generic version of aioreactive.abc.AsyncSource."""

    __slots__ = ()


class Sink(Generic[T_contra], abc.Sink):
    """A generic version of aioreactive.abc.Sink."""

    __slots__ = ()


class AsyncSink(Generic[T_contra], abc.AsyncSink):
    """A generic version of aioreactive.abc.AsyncSink."""

    __slots__ = ()
