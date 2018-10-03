# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals


__doc__ = r"""jmoldow_asynctools - Extra tools for Python's async/await and asyncio

Copyright (C) 2018  Jordan Moldow

Contact:
E-mail: Jordan Moldow <jmoldow@alum.mit.edu>
Github: Jordan Moldow <https://github.com/jmoldow>




Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.




This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import collections.abc
import contextlib


class NullAwaitable(contextlib.AbstractAsyncContextManager, collections.abc.Awaitable):
    """Similar to contextlib.nullcontext, this is an async context manager that does nothing.

    If a value is passed to the constructor, then that value is returned from `__aenter__()`.

    This object is also an awaitable that can be used in an `await` expression, e.g.

        await NullAwaitable()

    The result will be the value of the constructor parameter, which defaults to `None`.
    """

    def __init__(self, await_result=None):
        super().__init__()
        self.await_result = await_result

    def __await__(self):
        return self.__aenter__().__await__()

    async def __aenter__(self):
        return self.await_result

    async def __aexit__(self, *excinfo):
        pass


null_awaitable: NullAwaitable = NullAwaitable()
