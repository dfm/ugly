#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["hash_email", "User", "Feed"]

import os
import flask
import logging
import requests
import feedparser
from time import mktime
from hashlib import sha1
from datetime import datetime
from SimpleAES import SimpleAES
from sqlalchemy import (Column, Integer, String, Boolean, DateTime,
                        ForeignKey)
from sqlalchemy.orm import relationship

from .database import db


def hash_email(email):
    """
    The default hash function for storing email addresses in the database.

    :param email:
        The email address.

    """
    return sha1(email).hexdigest()


def encrypt_email(email):
    """
    The default encryption function for storing emails in the database. This
    uses AES and the encryption key defined in the applications configuration.

    :param email:
        The email address.

    """
    aes = SimpleAES(flask.current_app.config["AES_KEY"])
    return aes.encrypt(email)


def decrypt_email(enc_email):
    """
    The inverse of :func:`encrypt_email`.

    :param enc_email:
        The encrypted email address.

    """
    aes = SimpleAES(flask.current_app.config["AES_KEY"])
    return aes.decrypt(enc_email)


class User(db.Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String)
    email_hash = Column(String)
    joined = Column(DateTime)

    active = Column(Boolean)
    last_updated = Column(DateTime)

    refresh_token = Column(String)

    api_token = Column(String)

    def __init__(self, email, refresh_token):
        self.email = encrypt_email(email)
        self.email_hash = hash_email(email)
        self.joined = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.apitoken = self.generate_token()
        self.refresh_token = refresh_token
        self.active = True

    def __repr__(self):
        return "<User(\"{0}\", \"{1}\")>".format(self.get_email(),
                                                 self.refresh_token)

    def get_email(self):
        return decrypt_email(self.email)

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.refresh_token is not None

    def is_active(self):
        return self.refresh_token is not None

    def is_anonymous(self):
        return False

    def generate_token(self):
        return sha1(os.urandom(8) + self.email + os.urandom(8)).hexdigest()

    def get_oauth2_token(self):
        data = {
            "refresh_token": self.refresh_token,
            "client_id":
            flask.current_app.config["GOOGLE_OAUTH2_CLIENT_ID"],
            "client_secret":
            flask.current_app.config["GOOGLE_OAUTH2_CLIENT_SECRET"],
            "grant_type": "refresh_token",
        }
        r = requests.post("https://accounts.google.com/o/oauth2/token",
                          data=data)
        return r.json()["access_token"]


class Feed(db.Model):

    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    etag = Column(String)
    modified = Column(String)

    user = relationship("User", backref="feeds")
    user_id = Column(Integer, ForeignKey("users.id"))

    def __init__(self, user, url):
        self.user = user
        self.url = url

    def __repr__(self):
        return "<Feed({0}, \"{1}\")>".format(repr(self.user), self.url)

    def update(self):
        # Check for simultaneous updates.
        if self.updating:
            logging.info("Already updating: {0}".format(self.url))
            return

        # Flag this feed as updating.
        self.updating = True
        db.session.add(self)
        db.session.commit()

        # Fetch and parse the XML tree.
        tree = feedparser.parse(self.url, etag=self.etag,
                                modified=self.modified)

        # The feed will return 304 if it hasn't changed since the last check.
        if tree.status == 304:
            logging.info("Feed is un-changed: {0}".format(self.url))
            return

        # Update the feed meta data.
        fg = tree.feed.get
        self.title = fg("title")
        self.link = fg("link")
        self.description = fg("description")
        self.etag = tree.get("etag")
        self.modified = tree.get("modified")

        # Parse the new articles.
        for e in tree.entries:
            published = e.published_parsed
            if published is not None:
                published = datetime.fromtimestamp(mktime(published))
            updated = e.updated_parsed
            if updated is not None:
                updated = datetime.fromtimestamp(mktime(updated))
            article = Article(e.get("title"), e.get("author"),
                              e.get("description"),
                              published=published,
                              updated=updated,
                              feed=self)
            self.articles.append(article)

        # Commit the changes to the database.
        self.updating = False
        db.session.add(self)
        db.session.commit()
