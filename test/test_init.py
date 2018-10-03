# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import asyncio
import collections.abc
import contextlib

import jmoldow_asynctools
from jmoldow_asynctools import null_awaitable, NullAwaitable


class TestNullAwaitable(object):


    def test_await(self):
        obj = object()
        awaitable = NullAwaitable(obj)
        assert asyncio.run(self._run_awaitable(awaitable)) is obj

    def test_await_null_awaitable_singleton(self):
        assert asyncio.run(self._run_awaitable(null_awaitable)) is None

    def test_async_with(self):
        obj = object()
        awaitable = NullAwaitable(obj)
        assert asyncio.run(self._run_async_with(awaitable)) is obj

    def test_async_with_null_awaitable_singleton(self):
        assert asyncio.run(self._run_async_with(null_awaitable)) is None

    async def _run_awaitable(self, awaitable: collections.abc.Awaitable):
        return await awaitable

    async def _run_async_with(self, async_context_manager: contextlib.AbstractAsyncContextManager):
        async with async_context_manager as result:
            return result
