#!/usr/bin/env python

from setuptools import setup

setup(
    name="ugly",
    packages=["ugly"],
    package_data={"ugly": ["templates/*", "static/css/*.css"]},
    include_package_data=True,
)
