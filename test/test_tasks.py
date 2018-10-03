# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import collections.abc
import contextlib
from unittest.mock import call, Mock

import jmoldow_asynctools
from jmoldow_asynctools.tasks import yield_loop, yield_loop_on_exit, YieldLoop


class TestYieldLoop(object):

    def test_yield_loop(self):
        call_values1 = [1, 2, 3, 4, 5]
        call_values2 = [6, 7, 8, 9, 10]
        do_yield_loop = False
        mock = Mock()

        async def _task(call_values):
            call_values = iter(call_values)
            mock(next(call_values))
            if do_yield_loop:
                await yield_loop
            mock(next(call_values))
            async with (yield_loop if do_yield_loop else YieldLoop(on_enter=False, on_exit=False)):
                mock(next(call_values))
            async with (yield_loop_on_exit if do_yield_loop else YieldLoop(on_enter=False, on_exit=False)):
                mock(next(call_values))
            mock(next(call_values))

        async def _tasks():
            await asyncio.gather(_task(call_values1), _task(call_values2))

        def _assert(expected_calls):
            mock.assert_has_calls(list(map(call, expected_calls)), any_order=False)

        async def _run():
            nonlocal mock, do_yield_loop
            mock = Mock()

            await _tasks()
            # The two loops will execute serially, since neither yields the event loop during execution.
            _assert([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

            mock = Mock()
            # The two loops will be interleaved, since they both yield the event loop to each other between calls.
            do_yield_loop = True
            await _tasks()
            _assert([1, 6, 2, 7, 3, 8, 4, 9, 5, 10])

        asyncio.run(_run())
