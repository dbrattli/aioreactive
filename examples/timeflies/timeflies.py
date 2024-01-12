import asyncio
import signal
import sys
from tkinter import Event, Frame, Label, Misc, Tk
from types import FrameType

from expression import MailboxProcessor, pipe
from expression.system import AsyncDisposable

import aioreactive as rx
from aioreactive import AsyncAnonymousObserver, AsyncSubject
from aioreactive.types import AsyncObservable


# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


async def main() -> None:
    root = Tk()
    root.title("aioreactive")

    mousemoves: AsyncSubject[tuple[int, int]] = AsyncSubject()

    frame = Frame(root, width=800, height=600)  # , bg="white")

    async def worker(mb: MailboxProcessor["Event[Misc]"]) -> None:
        while True:
            event = await mb.receive()
            await mousemoves.asend((event.x, event.y))

    agent = MailboxProcessor.start(worker)
    frame.bind("<Motion>", agent.post)

    text = "TIME FLIES LIKE AN ARROW"
    labels = [Label(frame, text=c, borderwidth=0, padx=0, pady=0) for c in text]

    def handle_label(label: Label, i: int) -> AsyncObservable[tuple[Label, int, int]]:
        label.config(dict(borderwidth=0, padx=0, pady=0))

        def mapper(x: int, y: int) -> tuple[Label, int, int]:
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

    subscription: AsyncDisposable
    running = True

    async def asend(value: tuple[Label, int, int]) -> None:
        """Perform side effect."""
        label, x, y = value
        label.place(x=x, y=y)

    async def athrow(ex: Exception):
        nonlocal running, subscription
        print("Exception: ", ex)
        await subscription.dispose_async()
        running = False

    obv = AsyncAnonymousObserver(asend, athrow)

    async def start():
        nonlocal subscription
        print("Subscribing stream")
        subscription = await stream.subscribe_async(obv)

    async def stop():
        nonlocal subscription
        print("Disposing stream")
        await subscription.dispose_async()

    def handle_focus_in(event: "Event[Misc]"):
        asyncio.ensure_future(start())

    def handle_focus_out(event: "Event[Misc]"):
        asyncio.ensure_future(stop())

    root.bind("<FocusIn>", handle_focus_in)
    root.bind("<FocusOut>", handle_focus_out)

    frame.pack()

    def signal_handler(signal: int, frame: FrameType | None = None) -> None:
        nonlocal running
        running = False
        sys.stderr.write("Exiting...\n")
        root.destroy()
        root.quit()

    signal.signal(signal.SIGINT, signal_handler)

    # A simple combined event loop
    while running:
        await asyncio.sleep(0.001)
        root.update()


if __name__ == "__main__":
    asyncio.run(main())
