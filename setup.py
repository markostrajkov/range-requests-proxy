#!/usr/bin/env python

from setuptools import setup

setup(
    name='range-requests-proxy',
    version='0.1',
    description='Asynchronous HTTP proxy for HTTP Range Requests',
    author='Marko Trajkov',
    author_email='markostrajkov@gmail.com',
    install_requires=['tornado==4.4.1', 'pycurl==7.43.0'],
    packages=['rangerequestsproxy'],
)
