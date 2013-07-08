#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["front"]

import flask
from SimpleAES import SimpleAES

front = flask.Blueprint("front", __name__, template_folder="templates")


@front.route("/")
def index():
    return flask.render_template("splash/index.html")


@front.route("/request")
def request():
    email = flask.request.values.get("email", None)
    if email is not None:
        aes = SimpleAES(flask.current_app.config["AES_KEY"])
        enc_email = aes.encrypt(email)
    return flask.render_template("splash/request.html")
