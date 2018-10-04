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
            assert not (rlock.locked() or rlock.locked_by_current or rlock.locked_by_other)
            async with rlock:
                assert rlock.locked() and rlock.locked_by_current and (not rlock.locked_by_other)
                async with rlock:
                    assert rlock.locked() and rlock.locked_by_current and (not rlock.locked_by_other)
                assert rlock.locked() and rlock.locked_by_current and (not rlock.locked_by_other)
            assert not (rlock.locked() or rlock.locked_by_current or rlock.locked_by_other)

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
            assert not lock.locked()
            async with lock.shared_lock as obj1:
                assert lock.locked()
                assert obj1 is lock
                async with lock.shared_lock as obj2:
                    assert lock.locked()
                    assert obj2 is lock
                    async with lock.shared_lock as obj3:
                        assert lock.locked()
                        assert obj3 is lock
                    assert lock.locked()
                assert lock.locked()
            assert not lock.locked()

        asyncio.run(_run())

    def test_shared_lock_with_multiple_tasks(self):
        mock = Mock()

        async def _run(n, lock=None):
            lock = lock or SharedLock()
            async with lock.shared_lock:
                assert lock.locked()
                mock(n)
                if n > 0:
                    await asyncio.gather(asyncio.create_task(_run(n - 1, lock)))
                assert lock.locked()
                mock(n)

        asyncio.run(_run(4))
        mock.assert_has_calls(list(map(call, [4, 3, 2, 1, 0, 0, 1, 2, 3, 4])), any_order=False)

    def test_exclusive_lock_with_one_task(self):

        async def _run():
            lock = SharedLock()
            assert not lock.locked()
            async with lock.exclusive_lock as obj1:
                assert lock.locked()
                assert obj1 is lock
                async with lock.shared_lock:
                    assert lock.locked()
                    async with lock.exclusive_lock as obj2:
                        assert lock.locked()
                        assert obj2 is lock
                        async with lock.shared_lock:
                            assert lock.locked()
                        assert lock.locked()
                    assert lock.locked()
                assert lock.locked()
            assert not lock.locked()

        asyncio.run(_run())


    def test_exclusive_lock_with_multiple_tasks(self):

        async def _task(lock: contextlib.AbstractAsyncContextManager, mock: Mock, task_num: int):
            async with lock:
                mock(task_num)
                for _ in range(10):
                    await yield_loop
                async with lock:
                    mock(task_num)
                    for _ in range(10):
                        await yield_loop
                mock(task_num)
                for _ in range(10):
                    await yield_loop
            mock(task_num)

        async def _assert_locked_by_other(lock: SharedLock):
            assert lock.locked()
            assert lock.locked_by_other
            assert not lock.locked_by_current

        def _assert(mock: Mock, expected_calls: typing.List[int]):
            mock.assert_has_calls(list(map(call, expected_calls)), any_order=False)

        async def _run():
            mock = Mock()
            # With a no-op lock, the calls will be interleaved.
            rlock = jmoldow_asynctools.null_awaitable
            await asyncio.gather(_task(rlock, mock, 1), _task(rlock, mock, 2))
            _assert(mock, [1, 2, 1, 2, 1, 2, 1, 2])

            mock = Mock()
            # With a SharedLock.exclusive_lock, all of the first task's calls will come first, then all of the second task's calls.
            lock = SharedLock()
            exclusive_lock_manager = lock.exclusive_lock
            await asyncio.gather(
                _task(exclusive_lock_manager, mock, 1),
                _task(exclusive_lock_manager, mock, 2),
                _assert_locked_by_other(lock),
            )
            _assert(mock, [1, 1, 1, 1, 2, 2, 2, 2])

        asyncio.run(_run())
