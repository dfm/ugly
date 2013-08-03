#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["frontend"]

import flask
from flask.ext.login import login_required

import feedfinder

from .models import User, Feed
from .database import db

frontend = flask.Blueprint("frontend", __name__)


@frontend.route("/")
def index():
    if flask.g.user is not None:
        return flask.redirect(flask.url_for(".settings"))

    return flask.render_template("splash.html",
                                 error=flask.request.args.get("error"))


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
            feed = db.session.query(Feed).join(User.feeds) \
                .filter(User.id == flask.g.user.id) \
                .filter(Feed.url == url).first()

            if feed is None:
                feed = Feed.query.filter(Feed.url == url).first()

                if feed is None:
                    feed = Feed(url)
                    db.session.add(feed)

                flask.g.user.feeds.append(feed)
                db.session.add(flask.g.user)
                db.session.commit()

            else:
                error = "You're already subscribed to that feed."

    # Unsubscribe from a feed.
    remove_url = flask.request.args.get("remove", None)
    if remove_url is not None:
        feed = db.session.query(Feed).join(User.feeds) \
            .filter(User.id == flask.g.user.id) \
            .filter(Feed.url == remove_url).first()

        if feed is None:
            error = "Couldn't unsubscribe you from that feed."

        else:
            flask.g.user.feeds.remove(feed)
            db.session.add(flask.g.user)
            db.session.commit()

    return flask.render_template("settings.html", error=error)
