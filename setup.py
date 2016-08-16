#!/usr/bin/env python

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='range-requests-proxy',
    version='0.1',
    description='Asynchronous HTTP proxy for HTTP Range Requests',
    author='Marko Trajkov',
    author_email='markostrajkov@gmail.com',
    cmdclass={'test': PyTest},
    tests_require=['pytest>=2.8.0', 'mock==2.0.0'],
    install_requires=['tornado==4.4.1', 'pycurl==7.43.0'],
    packages=['rangerequestsproxy'],
    license='BSD',
    url='https://github.com/markostrajkov/range-requests-proxy',
)
