# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import collections.abc
import contextlib
from unittest.mock import call, Mock

import jmoldow_asynctools
from jmoldow_asynctools.tasks import yield_loop


def test_yield_loop():
    call_values1 = [1, 2, 3]
    call_values2 = [4, 5, 6]
    do_yield_loop = False
    mock = Mock()

    async def _task(call_values):
        for value in call_values:
            mock(value)
            if do_yield_loop:
                await yield_loop

    async def _tasks():
        await asyncio.gather(_task(call_values1), _task(call_values2))

    def _assert(expected_calls):
        mock.assert_has_calls(list(map(call, expected_calls)), any_order=False)

    async def _run():
        nonlocal mock, do_yield_loop
        mock = Mock()

        await _tasks()
        _assert([1, 2, 3, 4, 5, 6])

        mock = Mock()
        # The two loops will be interleaved, since they both yield the event loop to each other between calls.
        do_yield_loop = True
        await _tasks()
        _assert([1, 4, 2, 5, 3, 6])

    asyncio.run(_run())
