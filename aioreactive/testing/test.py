from typing import Generic, Iterable, Tuple, TypeVar

TSource = TypeVar("TSource")


class Test(Generic[TSource]):
    def __init__(self, xs: Iterable[TSource]) -> None:
        self.xs = xs

    def indexed(self) -> "Test[Tuple[int, int]]":
        return Test((10, 20))

    @staticmethod
    def create(xs: Iterable[TSource]) -> "Test[TSource]":
        return Test(xs)
