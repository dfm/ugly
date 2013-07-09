#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["create_app"]

import flask
from .login import oid, login_manager
from .database import db


def create_app(config_filename=None):
    app = flask.Flask(__name__)
    app.config.from_object("ugly.default_settings")
    if config_filename is not None:
        app.config.from_pyfile(config_filename)

    # Setup database.
    db.init_app(app)

    # Setup Login/OpenID.
    oid.init_app(app)
    login_manager.init_app(app)

    # Bind the blueprints.
    from .splash import splash
    app.register_blueprint(splash)

    from .login import login
    app.register_blueprint(login)

    from .api import api
    app.register_blueprint(api, url_prefix="/api")

    return app
