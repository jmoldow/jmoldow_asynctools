# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import collections.abc
import contextlib
from dataclasses import dataclass


@dataclass
class YieldLoop(contextlib.AbstractAsyncContextManager, collections.abc.Awaitable):
    """The expression `await yield_loop` yields control of the event loop so that a different task can be scheduled.

    Can also be used as an asynchronous context manager, yielding on enter and/or on exit, depending on the constructor
    parameters.
    """

    on_enter: bool = True
    on_exit: bool = True

    def __await__(self):
        return asyncio.sleep(0).__await__()

    async def __aenter__(self):
        if self.on_enter:
            await self

    async def __aexit__(self, *exc_info):
        if self.on_exit:
            await self


yield_loop: YieldLoop = YieldLoop()
yield_loop_on_exit: YieldLoop = YieldLoop(on_exit=True, on_enter=False)
