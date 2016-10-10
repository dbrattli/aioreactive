from . import typing


def noop(*args, **kw):
    """No operation. Returns nothing"""
    pass


async def anoop(*args, **kw):
    """Async no operation. Returns nothing"""
    pass


class NoopSink(typing.AsyncSink):
    async def send(self, value):
        pass

    async def throw(self, ex):
        pass

    async def close(self):
        pass


noopsink = NoopSink()
