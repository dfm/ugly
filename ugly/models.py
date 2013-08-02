#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["hash_email", "Invitation", "User", "Feed", "Article"]

import os
import flask
import logging
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


class Invitation(db.Model):

    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    code = Column(String)
    sent = Column(Boolean)
    created = Column(DateTime)

    def __init__(self, email, sent=False):
        # Encrypt and hash the email address.
        self.email = hash_email(email)

        # Generate an invitation code.
        self.code = sha1(os.urandom(24)).hexdigest()

        # Invitation sent flag.
        self.sent = sent

        # Date of registration.
        self.created = datetime.utcnow()

    def __repr__(self):
        return "<Invitation(\"{0}\", sent={1})>".format(self.email,
                                                        self.sent)


class User(db.Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String)
    hemail = Column(String)
    joined = Column(DateTime)

    openid = Column(String)
    name = Column(String)
    apitoken = Column(String)

    def __init__(self, email, openid, name):
        # Encrypt and hash the email address.
        self.email = encrypt_email(email)
        self.hemail = hash_email(email)

        # Date of registration.
        self.joined = datetime.utcnow()

        # Initialize the OpenID stuff.
        self.openid = openid
        self.name = name

        # Generate an API token.
        self.apitoken = self.generate_token()

    def __repr__(self):
        return "<User(\"{0}\")>".format(self.get_email())

    def get_email(self):
        return decrypt_email(self.email)

    def get_id(self):
        return self.openid

    def is_authenticated(self):
        return self.openid is not None

    def is_active(self):
        return self.openid is not None

    def is_anonymous(self):
        return False

    def generate_token(self):
        return sha1(os.urandom(8) + self.email + os.urandom(8)).hexdigest()


class Feed(db.Model):

    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    link = Column(String)
    description = Column(String)
    etag = Column(String)
    modified = Column(String)
    articles = relationship("Article", backref="feed")

    user = relationship("User", backref="feeds")
    user_id = Column(Integer, ForeignKey("users.id"))

    updating = Column(Boolean, default=False)

    def __init__(self, user, url):
        self.user = user
        self.url = url

    def __repr__(self):
        return "<Feed(\"{0.title}\")>".format(self)

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


class Article(db.Model):

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"))

    title = Column(String)
    author = Column(String)
    description = Column(String)
    published = Column(DateTime)
    updated = Column(DateTime)

    read = Column(Boolean, default=False)

    def __init__(self, title, author, description, published=None,
                 updated=None, feed=None):
        self.title = title
        self.author = author
        self.description = description
        self.published = published
        self.updated = updated
        self.feed = feed

    def __repr__(self):
        return "<Article(\"{0.title}\")>".format(self)
