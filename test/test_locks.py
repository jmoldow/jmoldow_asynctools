# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import contextlib
import typing
from unittest.mock import call, Mock

import jmoldow_asynctools
from jmoldow_asynctools.locks import AsyncRLock
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
            async with rlock:
                assert rlock.locked()
                async with rlock:
                    assert rlock.locked()
                assert rlock.locked()
            assert not rlock.locked()

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

        async def _tasks(rlock: contextlib.AbstractAsyncContextManager, mock: Mock):
            await asyncio.gather(_task(rlock, mock, 1), _task(rlock, mock, 2))

        def _assert(mock: Mock, expected_calls: typing.List[int]):
            mock.assert_has_calls(list(map(call, expected_calls)), any_order=False)

        async def _run():
            mock = Mock()
            # With a no-op lock, the calls will be interleaved.
            rlock = jmoldow_asynctools.null_awaitable
            await _tasks(rlock, mock)
            _assert(mock, [1, 2, 1, 2, 1, 2, 1, 2])

            mock = Mock()
            # With an RLock, all of the first task's calls will come first, then all of the second task's calls.
            rlock = AsyncRLock()
            await _tasks(rlock, mock)
            _assert(mock, [1, 1, 1, 1, 2, 2, 2, 2])

        asyncio.run(_run())
