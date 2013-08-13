#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["api"]

import flask
import feedfinder
from functools import wraps
from flask.ext.login import current_user

from .database import db
from .models import User, Feed

api = flask.Blueprint("api", __name__)


def private_view(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated():
            return flask.abort(404)
        return func(*args, **kwargs)
    return decorated_view


@api.route("/")
def index():
    return flask.redirect(flask.url_for("frontend.index"))


@api.route("/feeds")
@private_view
def feeds():
    feeds = current_user.feeds
    return flask.jsonify(
        count=len(feeds),
        feeds=[feed.to_dict() for feed in feeds],
    )


@api.route("/subscribe", methods=["GET", "POST"])
@private_view
def subscribe():
    # Get the requested subscription URL.
    add_url = flask.request.values.get("url")
    if add_url is None:
        return flask.jsonify(message="You must provide a URL."), 400

    # Try to find a feed below the requested resource.
    url = feedfinder.feed(add_url)
    if url is None:
        return flask.jsonify(message="Invalid feed URL."), 400

    # See if the user is already subscribed to a feed at that URL.
    feed = db.session.query(Feed).join(User.feeds) \
        .filter(User.id == current_user.id) \
        .filter(Feed.url == url).first()
    if feed is not None:
        return flask.jsonify(
            message="You've already subscribed to that feed.",
            feed=feed.to_dict(),
        )

    # See if a feed object already exists for that URL.
    feed = Feed.query.filter(Feed.url == url).first()

    # If it doesn't, create a new one.
    if feed is None:
        feed = Feed(url)

        # Update the feed immediately to get the title, etc.
        feed.update(force=True)

    # Subscribe the current user.
    current_user.feeds.append(feed)
    db.session.commit()

    return flask.jsonify(
        message="Successfully subscribed.",
        feed=feed.to_dict(),
    )


@api.route("/unsubscribe/<int:feedid>", methods=["GET", "POST"])
@private_view
def unsubscribe(feedid):
    # Find the feed that the user wants to unsubscribe from.
    feed = db.session.query(Feed).join(User.feeds) \
        .filter(User.id == current_user.id) \
        .filter(Feed.id == feedid).first()

    # If the user isn't subscribed, return a failure.
    if feed is None:
        return flask.jsonify(message="Invalid feed ID."), 400

    # Unsubscribe the user.
    current_user.feeds.remove(feed)
    db.session.commit()

    return flask.jsonify(message="Successfully unsubscribed.")
