# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import collections
import contextlib
import operator
import sys
import typing

from . import null_awaitable
from .util import AsyncContextManager
from .tasks import yield_loop


class AsyncRLock(contextlib.AbstractAsyncContextManager):
    """A reentrant lock for use with asyncio, analogous to threading.RLock."""

    def __init__(self):
        super().__init__()
        self._lock: asyncio.Lock = asyncio.Lock()
        self._owner: typing.Optional[asyncio.Task] = None
        self._count: int = 0

    async def __aenter__(self) -> AsyncRLock:
        await self.acquire()
        return self

    async def __aexit__(self, *exc_info):
        self.release()

    def locked(self) -> bool:
        return self._lock.locked()

    @property
    def locked_by_current(self) -> bool:
        return self.locked() and self._owned_by_current

    @property
    def locked_by_other(self) -> bool:
        return self.locked() and (not self._owned_by_current)

    async def acquire(self) -> bool:
        current_task = asyncio.current_task()
        current_task_id = id(current_task)
        print(f"\nacquire {self!r} from task {current_task_id}\n{current_task}\n")
        #print(f"acquire {self!r}    {self.__dict__}")
        if self._owned_by_current:
            assert self._lock.locked() and (self._count > 0)
            return self._acquire()
        await self._lock.acquire()
        assert (self._owner is None) and (self._count == 0)
        return self._acquire()

    def release(self):
        current_task = asyncio.current_task()
        current_task_id = id(current_task)
        print(f"\nrelease {self!r} from task{current_task_id}\n{current_task}\n")
        #print(f"release {self!r}    {self.__dict__}")
        if not self.locked():
            breakpoint()
            raise RuntimeError("cannot release un-acquired lock")
        if self.locked_by_other:
            breakpoint()
            raise RuntimeError("cannot release lock that is acquired by a different task")
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
        assert self.locked_by_current and (not self.locked_by_other)
        return True

    @property
    def _owned_by_current(self) -> bool:
        return self._owner is asyncio.current_task()


class SharedLock(object):

    def __init__(self):
        super().__init__()
        self._semaphore: typing.DefaultDict[asyncio.Task, AsyncRLock] = collections.defaultdict(AsyncRLock)
        self._exclusive_lock: AsyncRLock = AsyncRLock()
        self._shared_lock = AsyncContextManager(enter=self._enter_shared_lock, exit=self._exit_shared_lock)
        self._exclusive_lock_manager = AsyncContextManager(enter=self._enter_exclusive_lock, exit=self._exit_exclusive_lock)

    def locked(self) -> bool:
        return (
        self._exclusive_lock.locked() or
        any(map(operator.methodcaller('locked'), self._semaphore.values()))
        )

    @property
    def locked_by_current(self) -> bool:
        return self.locked() and self._owned_by_current

    @property
    def locked_by_other(self) -> bool:
        return self.locked() and (not self._owned_by_current)

    @property
    def shared_lock(self):
        return self._shared_lock

    async def _enter_shared_lock(self):
        async with yield_loop:
            current_task = asyncio.current_task()
            async with (
                self._exclusive_lock
                if (current_task not in self._semaphore) or (not self._semaphore[current_task].locked())
                else null_awaitable
            ):
                await self._semaphore[current_task].acquire()
                return self

    async def _exit_shared_lock(self, *exc_info):
        async with yield_loop:
            current_task = asyncio.current_task()
            rlock = self._semaphore[current_task]
            rlock.release()
            if not (self._exclusive_lock.locked_by_other or rlock.locked()):
                del self._semaphore[current_task]

    @property
    def exclusive_lock(self):
        return self._exclusive_lock_manager

    @property
    @contextlib.asynccontextmanager
    async def ____exclusive_lock(self):
        current_task = asyncio.current_task()
        already_exclusively_locked = self._exclusive_lock.locked_by_current
        async with self._exclusive_lock:
            if (current_task in self._semaphore) and (not already_exclusively_locked):
                raise RuntimeError(
                'Tried to claim exclusive lock when already holding shared lock. '
                'This is disallowed because it could lead to deadlocks. '
                'It also may indicate a code error: typically, '
                'exclusive locks should be claimed as early in the task as possible.'
                )
            current_task_rlock = self._semaphore[current_task]
            del self._semaphore[current_task]
            async with contextlib.AsyncExitStack() as stack:
                for rlock in self._semaphore.values():
                    await stack.enter_async_context(rlock)
                self._semaphore.clear()
            self._semaphore[current_task] = current_task_rlock
            del current_task_rlock
            try:
                async with self._semaphore[current_task]:
                    yield self
            finally:
                if not self._semaphore[current_task].locked():
                    del self._semaphore[current_task]

    async def _enter_exclusive_lock(self):
        current_task = asyncio.current_task()
        already_exclusively_locked = self._exclusive_lock.locked_by_current
        async with contextlib.AsyncExitStack() as emergency_stack:
            await emergency_stack.enter_async_context(self._exclusive_lock)
            if (current_task in self._semaphore) and (not already_exclusively_locked):
                raise RuntimeError(
                'Tried to claim exclusive lock when already holding shared lock. '
                'This is disallowed because it could lead to deadlocks. '
                'It also may indicate a code error: typically, '
                'exclusive locks should be claimed as early in the task as possible.'
                )
            current_task_rlock = self._semaphore[current_task]
            del self._semaphore[current_task]
            async with contextlib.AsyncExitStack() as stack:
                for rlock in self._semaphore.values():
                    await stack.enter_async_context(rlock)
                self._semaphore.clear()
            self._semaphore[current_task] = current_task_rlock
            del current_task_rlock
            await emergency_stack.enter_async_context(self._semaphore[current_task])
            emergency_stack.pop_all()
        return self

    async def _exit_exclusive_lock(self, *exc_info):
        current_task = asyncio.current_task()
        try:
            self._semaphore[current_task].release()
            if not self._semaphore[current_task].locked():
                del self._semaphore[current_task]
        finally:
            self._exclusive_lock.release()

    def __repr__(self):
        semaphore = len(self._semaphore)
        return f"<{self.__class__.__name__!s}: semaphore={semaphore!r}, exclusive_lock={self._exclusive_lock!r}>"

    @property
    def _owned_by_current(self) -> bool:
        return (
        self._exclusive_lock.locked_by_current or
        any(map(operator.attrgetter('locked_by_current'), self._semaphore.values()))
        )
