#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["add_feed", "update_all"]

import sqlite3
import logging
import html2text
import feedparser
from time import mktime
from datetime import datetime


def init_tables(dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()

        # Add the table to list the feeds.
        cursor.execute("""create table if not exists feeds
        (name text unique, url text, title text, link text,
         modified text, etag text)
        """)

        # Add the table to contain the actual posts.
        cursor.execute("""create virtual table if not exists posts using fts3
        (read integer, title text, summary text,
         link text, published text, updated text, feedid integer,
         foreign key(feedid) references feeds(rowid),
         tokenize=porter)
        """)


def add_feed(name, url, dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("insert or ignore into feeds (name, url) values(?, ?)",
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
        cursor.execute("select rowid,name,url,modified,etag from feeds")
        for feed in cursor.fetchall():
            fid, name, url, modified, etag = feed
            tree = update_feed(url, etag, modified)
            if tree is None:
                continue

            # Update the meta-data.
            fg = tree.feed.get
            cursor.execute("""update feeds set
                title=?,link=?,etag=?,modified=? where rowid=?
            """, (fg("title"), fg("link"), tree.get("etag"),
                  tree.get("modified"), fid))

            for e in tree.entries:
                link = e.get("link")
                cursor.execute("""insert or replace into posts
                    (rowid,feedid,read,title,summary,link,published,updated)
                values
                    ((select rowid FROM posts WHERE link=?),
                     ?,?,?,?,?,?,?)
                """, (link, name, 0, e.get("title"), e.get("summary"), link,
                      _parse_date(e.get("published_parsed")),
                      _parse_date(e.get("updated_parsed"))))


def get_status(dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("""
        select feeds.title,count(posts) from posts
            join feeds on feeds.name=posts.feedid
            where posts.read=0
            group by posts.feedid
        """)
        return dict(cursor.fetchall())


def read_post(feed, dbfn):
    with sqlite3.connect(dbfn) as c:
        cursor = c.cursor()
        cursor.execute("""
        select rowid,title,link,summary,updated from posts
        where feedid=? and read=0
        order by updated limit 1
        """, (feed, ))

        doc = cursor.fetchone()
        if doc is None:
            return "No unread posts.", None

        rowid, title, link, summary, updated = doc

        # Update as read.
        cursor.execute("update posts set read=1 where rowid=?", (rowid, ))

        # Parse and format the text.
        title = "Post {0}: ".format(rowid) + html2text.html2text(title).strip()
        summary = html2text.html2text(summary).strip()
        return (title + "\n" + "=" * len(title) + "\n\n" + updated + "\n"
                + "-" * len(updated) + "\n\n" + summary, link)
