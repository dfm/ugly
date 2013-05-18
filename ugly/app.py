#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["init", "add", "remove", "update", "status"]

import os
import sqlite3
import subprocess
from . import feed


def init(args, config):
    feed.init_tables(config["db"])
    return 0


def add(args, config):
    try:
        feed.add_feed(args.name, args.url, config["db"])
    except sqlite3.IntegrityError:
        print("Feed already exists: '{0}'".format(args.name))
        return -1
    return update(None, config)


def remove(args, config):
    try:
        feed.remove_feed(args.name, config["db"])
    except Exception as e:
        print(repr(e))
        return -1
    return 0


def update(args, config):
    feed.update_all(config["db"])
    return 0


def status(args, config):
    counts = feed.get_status(config["db"])
    for name, count in counts.items():
        if count > 0:
            print("{0}: {1} unread".format(name, count))
    return 0


def next(args, config):
    txt, link = feed.read_post(args.name, config["db"])
    if link is None:
        return 0

    # Paginate the post.
    p1 = subprocess.Popen(["echo", txt], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["more"], shell=True, stdin=p1.stdout)
    p1.stdout.close()
    p2.communicate()

    # Open in a browser?
    choice = input("\nOpen in browser? [y/N] ")
    if choice in ["y", "Y"]:
        return subprocess.call(["open", link])

    return 0
