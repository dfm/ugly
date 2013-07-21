#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["login", "oid", "login_manager"]

import flask
from flask.ext.login import (LoginManager, login_user, logout_user,
                             login_required)
from flask.ext.openid import OpenID, COMMON_PROVIDERS

from .database import db
from .models import Invitation, User

login = flask.Blueprint("login", __name__)

oid = OpenID()
login_manager = LoginManager()
login_manager.login_view = "login.index"


def try_login():
    return oid.try_login(COMMON_PROVIDERS["google"], ask_for=["email",
                                                              "fullname"])


@login_manager.user_loader
def user_loader(openid):
    return User.query.filter_by(openid=openid).first()


@login.route("/login")
@login.route("/login/<code>")
@oid.loginhandler
def index(code=None):
    if flask.g.user is not None:
        return flask.redirect(flask.url_for("feed.index"))

    if code == "connect":
        return try_login()

    if code is not None:
        existing = Invitation.query.filter_by(code=code).first()
        if existing is not None and existing.sent:
            # Save the code in the session and allow Google sign-in.
            flask.session["invitation"] = code
            return try_login()

    return flask.render_template("login.html")


@oid.after_login
def after_login(resp):
    # Check if the user exists already.
    user = User.query.filter_by(openid=resp.identity_url).first()

    # See if there is a code stored in the session.
    code = flask.session.pop("invitation", None)
    if user is None and code is not None:
        existing = Invitation.query.filter_by(code=code).first()
        if existing is not None:
            if existing.sent:
                user = User(resp.email, resp.identity_url, resp.fullname)
                db.session.add(user)
            db.session.delete(existing)
            db.session.commit()

    if user is not None:
        login_user(user)
        return flask.redirect(oid.get_next_url())

    return flask.redirect(oid.get_next_url())


@login.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for("splash.index"))
