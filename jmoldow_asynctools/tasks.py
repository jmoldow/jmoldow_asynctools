# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import collections.abc


__all__ = ['yield_loop']


class YieldLoop(collections.abc.Awaitable):
    """The expression `await yield_loop` yields control of the event loop so that a different task can be scheduled."""
    __slots__ = ()

    def __await__(self):
        return asyncio.sleep(0).__await__()


yield_loop: YieldLoop = YieldLoop()


del YieldLoop
