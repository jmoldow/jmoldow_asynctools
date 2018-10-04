# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import contextlib
import typing
from unittest.mock import call, Mock

import jmoldow_asynctools
from jmoldow_asynctools.locks import AsyncRLock, SharedLock
from jmoldow_asynctools.tasks import yield_loop


class TestAsyncRLock(object):

    def test_aenter_return_value(self):

        async def _run():
            rlock = AsyncRLock()
            async with rlock as obj1:
                assert obj1 is rlock
                async with rlock as obj2:
                    assert obj2 is rlock

        asyncio.run(_run())

    def test_locked(self):

        async def _run():
            rlock = AsyncRLock()
            assert not rlock.locked()
            assert not rlock.locked_by_current
            assert not rlock.locked_by_other
            assert not rlock.owned_by_current
            async with rlock:
                assert rlock.locked()
                assert rlock.locked_by_current
                assert not rlock.locked_by_other
                assert rlock.owned_by_current
                async with rlock:
                    assert rlock.locked()
                    assert rlock.locked_by_current
                    assert not rlock.locked_by_other
                    assert rlock.owned_by_current
                    assert rlock.locked()
                assert rlock.locked()
                assert rlock.locked_by_current
                assert not rlock.locked_by_other
                assert rlock.owned_by_current
            assert not rlock.locked()
            assert not rlock.locked_by_current
            assert not rlock.locked_by_other
            assert not rlock.owned_by_current

        asyncio.run(_run())

    def test_repr(self):

        async def _run():
            rlock = AsyncRLock()
            repr(rlock)
            async with rlock:
                repr(rlock)
                async with rlock:
                    repr(rlock)
                repr(rlock)
            repr(rlock)

        asyncio.run(_run())

    def test_locking_between_tasks(self):

        async def _task(rlock: contextlib.AbstractAsyncContextManager, mock: Mock, task_num: int):
            async with rlock:
                mock(task_num)
                await yield_loop
                async with rlock:
                    mock(task_num)
                    await yield_loop
                mock(task_num)
                await yield_loop
            mock(task_num)

        async def _assert_locked_by_other(rlock: AsyncRLock):
            assert rlock.locked()
            assert rlock.locked_by_other
            assert not rlock.locked_by_current
            assert not rlock.owned_by_current

        def _assert(mock: Mock, expected_calls: typing.List[int]):
            mock.assert_has_calls(list(map(call, expected_calls)), any_order=False)

        async def _run():
            mock = Mock()
            # With a no-op lock, the calls will be interleaved.
            rlock = jmoldow_asynctools.null_awaitable
            await asyncio.gather(_task(rlock, mock, 1), _task(rlock, mock, 2))
            _assert(mock, [1, 2, 1, 2, 1, 2, 1, 2])

            mock = Mock()
            # With an RLock, all of the first task's calls will come first, then all of the second task's calls.
            rlock = AsyncRLock()
            await asyncio.gather(_task(rlock, mock, 1), _task(rlock, mock, 2), _assert_locked_by_other(rlock))
            _assert(mock, [1, 1, 1, 1, 2, 2, 2, 2])

        asyncio.run(_run())


class TestSharedLock(object):

    def test_shared_lock_with_one_task(self):
        
        async def _run():
            lock = SharedLock()
            async with lock.shared_lock:
                async with lock.shared_lock:
                    async with lock.shared_lock:
                        pass

        asyncio.run(_run())

    def test_shared_lock_with_multiple_tasks(self):
        
        async def _run(n, lock=None):
            lock = lock or SharedLock()
            async with lock.shared_lock:
                if n > 0:
                    await asyncio.gather(asyncio.create_task(_run(n - 1, lock)))

        asyncio.run(_run(4))

    def test_exclusive_lock_with_one_task(self):
        
        async def _run():
            lock = SharedLock()
            async with lock.exclusive_lock:
                async with lock.shared_lock:
                    async with lock.exclusive_lock:
                        async with lock.shared_lock:
                            pass

        asyncio.run(_run())
