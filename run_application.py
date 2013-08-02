#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from ugly import create_app

if __name__ == "__main__":
    dirname = os.path.dirname(os.path.abspath(__file__))

    app = create_app(os.path.join(dirname, "local.py"))
    app.debug = True

    p = subprocess.Popen(["sass", "-t", "compressed", "--watch",
                          os.path.join(dirname, "ugly", "static", "css")])

    try:
        app.run()
    finally:
        p.kill()
