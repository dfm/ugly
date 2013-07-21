#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["feed"]

import flask
from flask.ext.login import login_required

feed = flask.Blueprint("feed", __name__)


@feed.route("/feed")
@login_required
def index():
    return flask.render_template("feed/index.html")


@feed.route("/feed/new")
@login_required
def new_feed():
    return flask.render_template("feed/new.html")
