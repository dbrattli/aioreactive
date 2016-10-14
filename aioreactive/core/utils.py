from . import typing


def noop(*args, **kw):
    """No operation. Returns nothing"""
    pass


async def anoop(*args, **kw):
    """Async no operation. Returns nothing"""
    pass


class NoopSink(typing.AsyncSink):
    async def asend(self, value):
        pass

    async def athrow(self, ex):
        pass

    async def aclose(self):
        pass


noopsink = NoopSink()
