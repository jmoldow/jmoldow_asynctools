#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, annotations, division, generator_stop, print_function, unicode_literals

from os.path import dirname, join

from setuptools import setup, find_packages


def main():
    base_dir = dirname(__file__)
    test_requires = [
        'pycodestyle',
        'pylint',
        'tox',
        'pytest>=2.8.3',
        'pytest-cov',
        'pytest-xdist',
    ]
    extra_requires = {'test': test_requires}
    setup(
        name='jmoldow_asynctools',
        version='0.0.0a0',
        description="Extra tools for Python's async/await and asyncio",
        long_description=open(join(base_dir, 'README.rst'), encoding='utf-8').read(),
        author='Jordan Moldow',
        author_email='jmoldow@alum.mit.edu',
        url='http://github.com/jmoldow',
        packages=find_packages(exclude=['docs', 'test', 'test*', '*test', '*test*']),
        install_requires=[],
        extras_require=extra_requires,
        tests_require=test_requires,
        license=(
        'Apache Software License Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0> ; '
        'or GNU General Public License Version 3.0 or any later version <https://www.gnu.org/licenses/>'
        ),
    )


if __name__ == '__main__':
    main()
