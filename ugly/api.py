#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["api"]

import flask
import requests


api = flask.Blueprint("api", __name__)


@api.route("/")
def index():
    return "Hello world."
