#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["add_feed", "update_all"]

import os
import json
import sqlite3
import logging
import feedparser
from time import mktime
from datetime import datetime


def init_tables(dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()

        # Add the table to list the feeds.
        cursor.execute("""create table if not exists feeds
        (id integer primary key, name text unique, url text, title text,
         link text, modified text, etag text)
        """)

        # Add the table to contain the actual posts.
        cursor.execute("""create virtual table if not exists posts using fts3
        (id integer primary key, read integer, title text, summary text,
         link text unique, published text, updated text, feedid integer,
         foreign ket(feedid) references feeds(id))
        """)


def add_feed(name, url, dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("insert into feeds (name, url) values(?, ?)",
                       (name, url))


def remove_feed(name, dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("delete from feeds where name=?", (name, ))


def update_feed(url, etag=None, modified=None):
    tree = feedparser.parse(url, etag=etag, modified=modified)
    if tree.status == 304:
        logging.info("Feed is un-changed: {0}".format(url))
        return None
    return tree


def _parse_date(dt):
    if dt is None:
        return None
    dt = datetime.fromtimestamp(mktime(dt))
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ%z")


def update_all(dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("select id,name,url,modified,etag from feeds")
        for feed in cursor.fetchall():
            fid, name, url, modified, etag = feed
            tree = update_feed(url, etag, modified)
            if tree is None:
                print("Feed is up to date: '{0}'".format(name))
                continue

            # Update the meta-data.
            fg = tree.feed.get
            cursor.execute("""update feeds set
                title=?,link=?,etag=?,modified=? where id=?
            """, (fg("title"), fg("link"), tree.get("etag"),
                  tree.get("modified"), fid))

            for e in tree.entries:
                cursor.execute("""insert or replace into posts
                    (feedid,read,title,summary,link,published,updated) values
                    (?,?,?,?,?,?,?)
                """, (fid, 0, e.get("title"), e.get("summary"), e.get("link"),
                      _parse_date(e.get("published_parsed")),
                      _parse_date(e.get("updated_parsed"))))


def get_status(dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("""
        select feeds.title,count(posts) from posts
            join feeds on feeds.id=posts.feedid
            where posts.read=0
            group by posts.feedid
        """)
        return dict(cursor.fetchall())
