#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask
from flask.ext.login import login_required

import feedfinder

from .models import Feed
from .database import db

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    if flask.g.user is not None:
        return flask.redirect(flask.url_for(".settings"))

    return flask.render_template("splash.html")


@frontend.route("/settings")
@login_required
def settings():
    error = None

    # Add a new feed.
    add_url = flask.request.args.get("add", None)
    if add_url is not None:
        url = feedfinder.feed(add_url)
        if url is None:
            error = "Invalid feed URL."

        else:
            # Check if the user is already subscribed.
            feed = Feed.query.filter_by(user_id=flask.g.user.id,
                                        url=url).first()

            if feed is None:
                feed = Feed(flask.g.user, url)
                db.session.add(feed)
                db.session.commit()

            else:
                error = "You're already subscribed to that feed."

    # Unsubscribe from a feed.
    remove_url = flask.request.args.get("remove", None)
    if remove_url is not None:
        feed = Feed.query.filter_by(user_id=flask.g.user.id,
                                    url=remove_url).first()
        if feed is None:
            error = "Couldn't unsubscribe you from that feed."

        else:
            db.session.delete(feed)
            db.session.commit()

    return flask.render_template("settings.html", error=error)
