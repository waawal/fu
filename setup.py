#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

settings = dict()


# Publish Helper.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

settings.update(
    name='fu',
    version='0.9.0',
    description='DNSBL checking SMTPD-Proxy',
    long_description=open('README.rst').read(),
    author='Daniel Waardal',
    author_email='waawal@boom.ws',
    url='https://github.com/waawal/fu',
    py_modules= ['fu',],
    install_requires=['gevent','argparse', 'PyYAML',],
    license='gpl',
    classifiers=(
        'Development Status :: 4 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        'Topic :: System :: Systems Administration',
        'Topic :: Communications',
    )
)


setup(**settings)
