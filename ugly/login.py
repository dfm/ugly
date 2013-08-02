#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["login", "login_manager"]

import urllib
import requests
import flask
from flask.ext.login import (LoginManager, login_user, logout_user,
                             login_required)

from .database import db
from .models import User, hash_email

login = flask.Blueprint("login", __name__)

login_manager = LoginManager()
login_manager.login_view = "login.index"

google_oauth2_url = "https://accounts.google.com/o/oauth2/auth"
google_token_url = "https://accounts.google.com/o/oauth2/token"
google_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


@login.route("/oauth2callback")
def oauth2callback():
    if "error" in flask.request.args or "code" not in flask.request.args:
        return "Error"

    # Request a refresh code and an access code.
    code = flask.request.args.get("code")
    data = {
        "code": code,
        "client_id": flask.current_app.config["GOOGLE_OAUTH2_CLIENT_ID"],
        "client_secret":
        flask.current_app.config["GOOGLE_OAUTH2_CLIENT_SECRET"],
        "redirect_uri": flask.url_for(".oauth2callback", _external=True),
        "grant_type": "authorization_code",
    }
    r = requests.post(google_token_url, data=data)
    if r.status_code != requests.codes.ok:
        return "Bad response"

    # Parse the response.
    data = r.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token", None)

    # Get the user information (email, id, etc.).
    r = requests.get(google_info_url, params={"access_token": access_token})
    data = r.json()
    email = data.get("email")

    # Find the user entry if it already exists.
    user = User.query.filter_by(email_hash=hash_email(email)).first()
    if user is None:
        if refresh_token is None:
            return "No refresh token"
        user = User(email, refresh_token)

    elif refresh_token is not None:
        user.refresh_token = refresh_token

    db.session.add(user)
    db.session.commit()

    login_user(user)

    return flask.redirect(flask.url_for("frontend.index"))


@login.route("/login")
def index():
    params = {
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/userinfo.email "
                 "https://mail.google.com/",
        "client_id": flask.current_app.config["GOOGLE_OAUTH2_CLIENT_ID"],
        "redirect_uri": flask.url_for(".oauth2callback", _external=True),
        "access_type": "offline",
    }
    return flask.redirect(google_oauth2_url
                          + "?{0}".format(urllib.urlencode(params)))


@login.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for("frontend.index"))
