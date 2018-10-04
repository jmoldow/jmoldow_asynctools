# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

import contextlib


class AsyncContextManager(contextlib.AbstractAsyncContextManager):

    def __init__(self, enter=None, exit=None):
        super().__init__()
        self._enter = enter
        self._exit = exit

    async def __aenter__(self):
        if self._enter:
            return await self._enter()
        return await super().__aenter__()

    async def __aexit__(self, *exc_info):
        if self._exit:
            return await self._exit(*exc_info)
        return await super().__aexit__(*exc_info)
