# type: ignore23
import asyncio
from tkinter import Event, Frame, Label, Tk

import aioreactive as rx
from aioreactive import AsyncAnonymousObserver, AsyncSubject
from expression.core import MailboxProcessor, pipe


async def main(loop) -> None:
    root = Tk()
    root.title("aioreactive")

    mousemoves: AsyncSubject[Event[Frame]] = AsyncSubject()

    frame = Frame(root, width=800, height=600, bg="white")

    async def worker(mb: MailboxProcessor[Event]) -> None:
        while True:
            event = await mb.receive()
            await mousemoves.asend(event)

    agent = MailboxProcessor.start(worker)
    frame.bind("<Motion>", agent.post)

    text = "TIME FLIES LIKE AN ARROW"
    labels = [Label(frame, text=c, bg="white") for c in text]

    async def handle_label(i: int, label: Label) -> None:
        label.config(dict(borderwidth=0, padx=0, pady=0))

        async def asend(ev: Event) -> None:
            label.place(x=ev.x + i * 12 + 15, y=ev.y)

        async def athrow(ex: Exception):
            print("Exception: ", ex)

        obv = AsyncAnonymousObserver(asend, athrow)
        await pipe(
            mousemoves,
            rx.delay(i / 10.0),
            rx.subscribe_async(obv),
        )

    for i, label in enumerate(labels):
        await handle_label(i, label)

    frame.pack()

    # A simple combined event loop
    while True:
        root.update()
        await asyncio.sleep(0.001)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
