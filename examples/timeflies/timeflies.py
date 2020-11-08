import asyncio
from tkinter import Event, Frame, Label, Tk

from aioreactive import AsyncAnonymousObserver, AsyncSubject, asyncrx
from expression.core import pipe


async def main() -> None:
    root = Tk()
    root.title("aioreactive")

    mousemoves: AsyncSubject[Event[Frame]] = AsyncSubject()

    frame = Frame(root, width=800, height=600)

    async def move(event: Event) -> None:
        await mousemoves.asend(event)

    def motion(event: Event) -> None:
        asyncio.ensure_future(move(event))

    frame.bind("<Motion>", motion)

    text = "TIME FLIES LIKE AN ARROW"
    labels = [Label(frame, text=c) for c in text]

    async def handle_label(i: int, label: Label) -> None:
        label.config(dict(borderwidth=0, padx=0, pady=0))

        async def asend(ev: Event) -> None:
            label.place(x=ev.x + i * 12 + 15, y=ev.y)

        obv = AsyncAnonymousObserver(asend)
        await pipe(mousemoves, asyncrx.delay(i / 10.0)).subscribe_async(obv)

    for i, label in enumerate(labels):
        await handle_label(i, label)

    frame.pack()

    # A simple combined event loop
    while True:
        root.update()
        await asyncio.sleep(0.005)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
