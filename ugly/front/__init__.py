#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["front"]

import flask
from hashlib import sha1

from ..database import db
from ..models import hash_email, Invitation

front = flask.Blueprint("front", __name__, template_folder="templates")


@front.route("/")
def index():
    return flask.render_template("splash/index.html")


@front.route("/request")
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
    existing = Invitation.query.filter_by(emailhash=emailhash).first()
    if existing is not None:
        return flask.render_template("splash/request.html",
                                     registered=True, sent=existing.sent,
                                     email=email)

    # Save the invitation to the database.
    invite = Invitation(email)
    db.session.add(invite)
    db.session.commit()

    return flask.render_template("splash/request.html")


@front.route("/resend/<email>")
def resend(email):
    # Try to find the email.
    emailhash = hash_email(email)
    existing = Invitation.query.filter_by(emailhash=emailhash).first()
    if existing is None:
        return flask.render_template("splash/resend.html",
                                     error="No invitation registered for that"
                                           " email.")

    # Check if the invitation is registered to send or not.
    if not existing.sent:
        return flask.render_template("splash/resend.html",
                                     error="Be patient, it'll come soon.")

    return flask.render_template("splash/resend.html")
