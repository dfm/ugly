#!/usr/bin/env python

import os
import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit()

setup(
    name="ugly",
    version="0.0.1",
    description="Fucking ugly rss",
    long_description=open("README.rst").read(),
    author="Dan F-M",
    author_email="danfm@nyu.edu",
    url="https://github.com/dfm/ugly",
    packages=["ugly"],
    scripts=["bin/ugly"],
    install_requires=open("requirements.txt").read().splitlines(),
    license="MIT",
    classifiers=(
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.3",
    ),
)
