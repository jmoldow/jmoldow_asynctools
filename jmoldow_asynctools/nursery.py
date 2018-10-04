# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import abc
import asyncio
import collections.abc
import contextlib
import typing


class Nursery(contextlib.AbstractAsyncContextManager, collections.abc.Awaitable):

    def __init__(self):
        super().__init__()
        self._entered: bool = False
        self._exited: bool = False
        self._tasks: typing.List[asyncio.Task] = []
        self._owner: asyncio.Task = asyncio.current_task()

    def create_task(self, coro: collections.abc.Coroutine) -> asyncio.Task:
        if not self.is_open:
            raise RuntimeError("nursery isn't open")
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task

    async def __aenter__(self) -> Nursery:
        self._validate_owned_by_current()
        if self._entered:
            raise RuntimeError('already entered nursery')
        self._entered = True
        return self

    async def __aexit__(self, *exc_info):
        self._validate_owned_by_current()
        self._exited = True
        for task in self._tasks:
            if not task.done():
                task.cancel()

    @property
    def is_open(self) -> bool:
        return self._entered and (not self._exited) and self.owned_by_current

    @property
    def owned_by_current(self) -> bool:
        return asyncio.current_task() is self._owner

    def __await__(self):
        return self._await().__await__()

    def _validate_owned_by_current(self) -> None:
        if not self.owned_by_current:
            raise RuntimeError("nursery isn't owned by this task")

    async def _await(self) -> None:
        async with self:
            pass
