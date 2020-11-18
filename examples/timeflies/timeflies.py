import asyncio
from tkinter import Event, Frame, Label, Misc, Tk
from typing import Tuple

import aioreactive as rx
from aioreactive import AsyncAnonymousObserver, AsyncTestSubject
from aioreactive.types import AsyncObservable
from expression.core import MailboxProcessor, pipe


async def main() -> None:
    root = Tk()
    root.title("aioreactive")

    mousemoves: AsyncTestSubject[Tuple[int, int]] = AsyncTestSubject()

    frame = Frame(root, width=800, height=600, bg="white")

    async def worker(mb: MailboxProcessor["Event[Misc]"]) -> None:
        while True:
            event = await mb.receive()
            await mousemoves.asend((event.x, event.y))

    agent = MailboxProcessor.start(worker)
    frame.bind("<Motion>", agent.post)

    text = "TIME FLIES LIKE AN ARROW"
    labels = [Label(frame, text=c, bg="white") for c in text]

    def handle_label(label: Label, i: int) -> AsyncObservable[Tuple[Label, int, int]]:
        label.config(dict(borderwidth=0, padx=0, pady=0))

        def mapper(x: int, y: int) -> Tuple[Label, int, int]:
            """Map mouse-move pos to label and new pos for label."""
            return label, x + i * 12 + 15, y

        return pipe(
            mousemoves,  # stream of mouse-moves
            rx.delay(i / 10.0),  # delay each mouse-move based on index of char
            rx.starmap(mapper),  # place label based on mouse pos and index of char
        )

    stream = pipe(
        labels,  # list of labels
        rx.from_iterable,  # stream of labels
        rx.flat_mapi(handle_label),  # swap stream of labels with stream of labels + pos
    )

    async def asend(value: Tuple[Label, int, int]) -> None:
        """Perform side effect."""
        label, x, y = value
        label.place(x=x, y=y)

    async def athrow(ex: Exception):
        print("Exception: ", ex)

    obv = AsyncAnonymousObserver(asend, athrow)
    await stream.subscribe_async(obv)

    frame.pack()

    # A simple combined event loop
    while True:
        root.update()  # type: ignore
        await asyncio.sleep(0.001)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
