#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["hash_email", "User", "Feed"]

import os
import flask
import requests
from hashlib import sha1
from datetime import datetime
from SimpleAES import SimpleAES
from sqlalchemy import (Column, Integer, String, Boolean, DateTime,
                        ForeignKey, Table)
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


# Association tables.
subscriptions = Table("subscriptions", db.Model.metadata,
                      Column("user_id", Integer, ForeignKey("users.id")),
                      Column("feed_id", Integer, ForeignKey("feeds.id")))

user_entry = Table("user_entry", db.Model.metadata,
                   Column("user_id", Integer, ForeignKey("users.id")),
                   Column("entry_id", Integer, ForeignKey("entries.id")))


# Data models.
class User(db.Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String)
    email_hash = Column(String)
    joined = Column(DateTime)

    active = Column(Boolean)
    refresh_token = Column(String)

    api_token = Column(String)

    feeds = relationship("Feed", secondary=subscriptions, backref="users")
    entries = relationship("Entry", secondary=user_entry, backref="users")

    def __init__(self, email, refresh_token):
        self.email = encrypt_email(email)
        self.email_hash = hash_email(email)
        self.joined = datetime.utcnow()
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
        return r.json().get("access_token")


class Feed(db.Model):

    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    etag = Column(String)
    modified = Column(String)

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "<Feed({0}, \"{1}\")>".format(repr(self.user), self.url)


class Entry(db.Model):

    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)
    ref = Column(String)

    feed = relationship("Feed", backref="entries")
    feed_id = Column(Integer, ForeignKey("feeds.id"))

    def __init__(self, ref, feed):
        self.ref = ref
        self.feed = feed

    def __repr__(self):
        return "<Entry(\"{0}\", {1})>".format(self.ref, repr(self.feed))
