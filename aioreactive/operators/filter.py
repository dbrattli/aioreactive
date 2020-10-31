from asyncio import iscoroutinefunction
from typing import Awaitable, Callable, TypeVar, Union

from aioreactive.core import AsyncObservable, AsyncObserver, AsyncSingleSubject
from fslash.system import AsyncCompositeDisposable, AsyncDisposable

T = TypeVar("T")

/// Applies the given async function to each element of the stream and returns the stream comprised of the results
/// for each element where the function returns Some with some value.
let chooseAsync (chooser: 'TSource -> Async<'TResult option>) : Stream<'TSource, 'TResult> =
    Transform.transformAsync (fun next a -> async {
        match! chooser a with
        | Some b -> return! next b
        | None -> return ()
    })

/// Applies the given function to each element of the stream and returns the stream comprised of the results for
/// each element where the function returns Some with some value.
let choose (chooser: 'TSource -> 'TResult option) : Stream<'TSource, 'TResult> =
    Transform.transformAsync (fun next a ->
        match chooser a with
        | Some b -> next b
        | None -> Async.empty
    )
