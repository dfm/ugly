Ugly Reader
===========

*The ugliest Google Reader reaplacement on the market.*

**Take a look at the live demo at: https://reader.dfm.io**

This is the Python source code for this app and it is licensed under the MIT license.

Installation & Setup
--------------------

First off, you'll need a Postgres server running somewhere and your web user should have
read and write access to a fresh database.

If you have a sane Python environment on your server, create a virtual environment and
then do the usual

::

    pip install -r requirements.txt

Then, you'll need to sign up as a Google OAuth app using the `Google API Console
<https://code.google.com/apis/console>`_ and save your client ID and secret to a Python
file with the following syntax:

::

    GOOGLE_OAUTH2_CLIENT_ID = "<your client ID>"
    GOOGLE_OAUTH2_CLIENT_SECRET = "<your client secret>"

The other options that you can set are shown in the default settings file 
``ugly/default_settings.py``. Make sure that you change your secret keys and double
check that the Postgres URI points to the right server and database. Then, to build
the needed database tables, launch Python and run (if your custom settings file is
saved as ``local.py``):

::

    from ugly import create_app
    from ugly.database import db
    from ugly.models import *
    
    db.create_all(app=create_app("local.py"))

The web app itself is built using `Flask <http://flask.pocoo.org/>`_ and it lives
in ``ugly/__init__.py``. For an example of how to run the app using a configuation
saved to ``local.py``, take a look at ``run_application.py``.

License
-------

Copyright 2013 `Dan Foreman-Mackey <http://dfm.io>`_.

Ugly Reader is licensed under the MIT license (see LICENSE).
