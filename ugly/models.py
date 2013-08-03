#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["hash_email", "User", "Feed", "Entry"]

import re
import os
import time
import flask
import imaplib
import requests
import feedparser
from hashlib import sha1
from datetime import datetime
from SimpleAES import SimpleAES
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

    admin = Column(Boolean)
    active = Column(Boolean)
    refresh_token = Column(String)

    api_token = Column(String)

    feeds = relationship("Feed", secondary=subscriptions, backref="users")
    entries = relationship("Entry", secondary=user_entry, backref="users")

    def __init__(self, email, refresh_token):
        self.email = encrypt_email(email)
        self.email_hash = hash_email(email)
        self.refresh_token = refresh_token

        self.joined = datetime.utcnow()
        self.apitoken = self.generate_token()
        self.admin = False
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

    def get_imap_connection(self):
        # Connect to the IMAP server.
        connection = imaplib.IMAP4_SSL("imap.gmail.com")
        s = "user={0}\1auth=Bearer {1}\1\1".format(self.get_email(),
                                                   self.get_oauth2_token())
        status, data = connection.authenticate("XOAUTH2", lambda x: s)
        assert status == "OK"

        return connection

    def deliver_entries(self):
        try:
            connection = self.get_imap_connection()
        except AssertionError:
            raise RuntimeError("Couldn't authenticate.")

        for feed in self.feeds:
            self.deliver_entries_for_feed(feed, connection=connection)

        try:
            connection.close()
        except:
            pass
        connection.logout()

    def deliver_entries_for_feed(self, feed, connection):
        # Find the entries that are waiting to be delivered and return if
        # there are none.
        entries = db.session.query(Entry).filter(Entry.feed == feed) \
            .filter(~Entry.users.contains(self)).all()
        if not len(entries):
            return

        # Try and create the labels.
        base = flask.current_app.config["BASE_MAILBOX"]
        mb = "{0}/{1}".format(base, feed.title)
        connection.create(base)
        connection.create(mb)

        # Select the mailbox.
        status, data = connection.select(mb)
        assert status == "OK"

        # Deliver the messages.
        email = self.get_email()
        for entry in entries:
            # Create the message.
            msg = MIMEMultipart("alternative")
            msg["From"] = flask.current_app.config["ADMIN_EMAIL"]
            msg["To"] = email
            msg["Subject"] = u"{0} — {1}".format(feed.title, entry.title)

            # Render the message body.
            contents = flask.render_template("message.html", feed=feed,
                                             entry=entry)
            part = MIMEText(contents.encode("utf-8"), "html", "utf-8")
            msg.attach(part)

            # Work out the time stamp.
            if entry.updated is not None:
                ts = imaplib.Time2Internaldate(
                    time.mktime(entry.updated.timetuple()))
            elif entry.published is not None:
                ts = imaplib.Time2Internaldate(
                    time.mktime(entry.published.timetuple()))
            else:
                ts = imaplib.Time2Internaldate(time.time())

            # Add the message to Gmail.
            status, [data] = connection.append(mb, "", ts, msg.as_string())
            if status == "OK":
                # Add the base label too.
                uid = re.findall("\[APPENDUID ([0-9]*) ([0-9]*)\]", data)[0][1]
                connection.uid("COPY", uid, base)

            # Update the user to know that this message has been delivered.
            self.entries.append(entry)

        # Update the database session.
        db.session.add(self)
        db.session.commit()


class Feed(db.Model):

    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)

    url = Column(String)
    link = Column(String)
    title = Column(String)

    etag = Column(String)
    modified = Column(String)

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "<Feed(\"{0}\")>".format(self.url)

    def update(self):
        # Do a conditional fetch and parse.
        tree = feedparser.parse(self.url, etag=self.etag,
                                modified=self.modified)

        # Return if nothing has changed.
        if tree.status == 304:
            return

        # Get the feed info.
        self.title = tree.feed.get("title")
        self.link = tree.feed.get("link")
        self.etag = tree.get("etag")
        self.modified = tree.get("modified")

        # Loop over the entries.
        for e in tree.entries:
            # See if the entry already exists.
            entry = Entry.query.filter(Entry.feed == self) \
                .filter(Entry.ref == (e.get("id") or e.get("link"))).first()
            if entry is not None:
                continue

            # Create a new entry and save.
            entry = Entry(self, e)
            self.entries.append(entry)

        db.session.add(self)
        db.session.commit()


class Entry(db.Model):

    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)

    ref = Column(String)
    link = Column(String)
    body = Column(String)
    title = Column(String)
    author = Column(String)
    published = Column(DateTime)
    updated = Column(DateTime)

    feed = relationship("Feed", backref="entries")
    feed_id = Column(Integer, ForeignKey("feeds.id"))

    def __init__(self, feed, entry):
        self.feed = feed

        self.ref = entry.get("id") or entry.get("link")
        self.link = entry.get("link")
        self.body = entry.get("description")
        self.title = entry.get("title")
        self.author = entry.get("author")
        self.published = self.parse_date(entry.get("published_parsed"))
        self.updated = self.parse_date(entry.get("updated_parsed"))

    def parse_date(self, date_tuple):
        if date_tuple is None:
            return None
        return datetime.fromtimestamp(time.mktime(date_tuple))

    def __repr__(self):
        return "<Entry({1}, \"{0}\")>".format(self.ref, repr(self.feed))
