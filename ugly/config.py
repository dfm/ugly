#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["load_config"]

import os
import json
import logging


def load_config(fn):
    try:
        with open(fn) as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.info("Using default settings.")
        config = {}

    # Set defaults.
    config["basepath"] = os.path.expanduser(config.get("basepath",
                                            os.path.join("~", ".ugly")))
    config["feedlist"] = os.path.expanduser(
        config.get("feedlist", os.path.join(config["basepath"], "feeds.json")))

    return config
