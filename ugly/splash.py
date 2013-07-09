#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["splash"]

import flask

from .database import db
from .models import hash_email, Invitation

splash = flask.Blueprint("splash", __name__)


@splash.route("/")
def index():
    return flask.render_template("splash/index.html")


@splash.route("/request")
def request():
    # Get the provided email address.
    email = flask.request.values.get("email", None)
    if email is None or len(email) == 0:
        return flask.render_template("splash/request.html",
                                     error="You need to give us an email "
                                           "address.")

    # Do a very basic check of the address.
    spl = email.split("@")
    if len(spl) != 2 or "." not in spl[1]:
        return flask.render_template("splash/request.html",
                                     error="That doesn't look like an email "
                                           "address at all. Try again?")

    # Check if an invitation already exists.
    emailhash = hash_email(email)
    existing = Invitation.query.filter_by(email=emailhash).first()
    if existing is not None:
        return flask.render_template("splash/request.html",
                                     registered=True, sent=existing.sent,
                                     email=email)

    # Save the invitation to the database.
    invite = Invitation(email)
    db.session.add(invite)
    db.session.commit()

    return flask.render_template("splash/request.html")


@splash.route("/resend/<email>")
def resend(email):
    # Try to find the email.
    emailhash = hash_email(email)
    existing = Invitation.query.filter_by(email=emailhash).first()
    if existing is None:
        return flask.render_template("splash/resend.html",
                                     error="No invitation registered for that"
                                           " email.")

    # Check if the invitation is registered to send or not.
    if not existing.sent:
        return flask.render_template("splash/resend.html",
                                     error="Be patient, it'll come soon.")

    return flask.render_template("splash/resend.html")


@splash.route("/signup/<code>")
def signup(code):
    existing = Invitation.query.filter_by(code=code).first()
    if existing is None or not existing.sent:
        return flask.render_template("splash/signup.html",
                                     error="The invitation code doesn't seem "
                                           "to exist.")

    return flask.render_template("splash/signup.html", code=code)
