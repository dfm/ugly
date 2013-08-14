#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask
from flask.ext.login import login_required

from .models import Entry

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    if flask.g.user is not None:
        return flask.redirect(flask.url_for(".settings"))

    return flask.render_template("splash.html",
                                 error=flask.request.args.get("error"))


@frontend.route("/about")
def about():
    return flask.render_template("about.html")


@frontend.route("/privacy")
def privacy():
    return flask.render_template("privacy.html")


@frontend.route("/settings")
@login_required
def settings():
    error = None
    return flask.render_template("settings.html", error=error)


@frontend.route("/message")
@login_required
def message():
    e = Entry.query.all()[51]
    try:
        return flask.render_template("message.html", entry=e)
    except:
        import traceback
        return traceback.format_exc()
