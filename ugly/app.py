#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["add", "remove", "update"]

from . import feed


def add(args, config):
    try:
        feed.add_feed(args.name, args.url, config["feedlist"])
    except Exception as e:
        print(e)
        return -1
    return 0


def remove(args, config):
    try:
        feed.remove_feed(args.name, config["feedlist"])
    except Exception as e:
        print(e)
        return -1
    return 0


def update(args, config):
    feed.update_all(config["feedlist"], config["basepath"])
    return 0


def status(args, config):
    counts = feed.get_status(config["feedlist"], config["basepath"])
    for el in counts:
        count = el["count"]
        if count > 0:
            print("{0}: {1} unread".format(el["title"], count))
    return 0


def read(args, config):
    item = feed.get_unread(args.name, config["feedlist"], config["basepath"])
