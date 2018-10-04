# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import contextlib
import typing


class AsyncRLock(contextlib.AbstractAsyncContextManager):
    """A reentrant lock for use with asyncio, analogous to threading.RLock."""

    def __init__(self):
        super().__init__()
        self._lock: asyncio.Lock = asyncio.Lock()
        self._owner: typing.Optional[asyncio.Task] = None
        self._count: int = 0
        self.locked = self._lock.locked

    async def __aenter__(self) -> AsyncRLock:
        await self.acquire()
        return self

    async def __aexit__(self, *exc_info):
        self.release()

    def locked(self) -> bool:
        return self._lock.locked()

    @property
    def locked_by_current(self) -> bool:
        return self.locked() and self.owned_by_current

    @property
    def locked_by_other(self) -> bool:
        return self.locked() and (not self.owned_by_current)

    @property
    def owned_by_current(self) -> bool:
        return self._owner is asyncio.current_task()

    async def acquire(self) -> bool:
        if self.owned_by_current:
            assert self._lock.locked() and (self._count > 0)
            return self._acquire()
        await self._lock.acquire()
        assert (self._owner is None) and (self._count == 0)
        return self._acquire()

    def release(self):
        if not self.locked_by_current:
            raise RuntimeError("cannot release un-acquired lock")
        assert self._count > 0
        self._count -= 1
        if self._count == 0:
            self._owner = None
            self._lock.release()

    def __repr__(self):
        res = super().__repr__()
        return f'<{res[1:-1]!s} [count:{self._count!r}, lock:{self._lock!r}]>'

    def _acquire(self) -> bool:
        self._owner = asyncio.current_task()
        self._count += 1
        return True
