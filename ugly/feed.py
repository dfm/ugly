#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["add_feed", "update_all"]

import re
import os
import json
import hashlib
import logging
import feedparser


def save(feeds, fn):
    with open(fn, "w") as f:
        feeds = json.dump(feeds, f, indent=2)


def load(fn):
    try:
        with open(fn) as f:
            feeds = json.load(f)
    except FileNotFoundError:
        feeds = {}
    return feeds


def add_feed(name, url, fn):
    feeds = load(fn)
    assert name not in feeds, "Feed already exists: {0}".format(name)
    feeds[name] = {"url": url, "name": name}
    save(feeds, fn)


def remove_feed(name, fn):
    feeds = load(fn)
    assert name in feeds, "Unrecognized feed: {0}".format(name)
    feeds.pop(name)
    save(feeds, fn)


def update_feed(url, etag=None, modified=None):
    tree = feedparser.parse(url, etag=etag, modified=modified)
    if tree.status == 304:
        logging.info("Feed is un-changed: {0}".format(url))
        return None
    return tree


def update_all(fn, basedir):
    feeds = load(fn)

    count = {}
    for nm, f in feeds.items():
        # Check for updated feed.
        feed = update_feed(f["url"], f.get("etag"), f.get("modified"))

        # The feed was unchanged.
        if feed is None:
            continue

        # Update the count of new entries.
        count[nm] = len(feed.entries)

        # Update the meta-data.
        fg = feed.feed.get
        f["title"] = fg("title")
        f["link"] = fg("link")
        f["description"] = fg("description") or fg("subtitle")
        f["etag"] = feed.get("etag")
        f["modified"] = feed.get("modified")

        # Save the entries.
        bp = os.path.join(basedir, f["name"], "new")
        try:
            os.makedirs(bp)
        except os.error:
            pass

        for e in feed.entries:
            date = e.date_parsed
            title = e.get("title", "Untitled")

            # Construct a file name for the entry.
            lfn = ("{1:04d}-{2:02d}-{3:02d}-{4:02d}-{5:02d}-{6:02d}-{0}.json"
                   .format(title.lower(), *date))
            lfn = os.path.join(bp, re.sub(r"[ /]", "-", lfn))

            # Parse the entry into a dictionary.
            doc = {
                "title": title,
                "summary": e.get("summary"),
                "link": e.get("link"),
                "published": e.get("published"),
                "updated": e.get("updated"),
            }

            # Save the JSON.
            save(doc, lfn)

    # Save the feed descriptions.
    save(feeds, fn)


def get_status(fn, basepath):
    feeds = load(fn)
    results = []
    for nm in feeds.keys():
        p = os.path.join(basepath, nm, "new")
        try:
            count = len(os.listdir(p))
        except:
            count = 0
        results.append({"title": nm,
                        "count": count})
    return results
