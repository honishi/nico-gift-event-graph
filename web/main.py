#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from flask import render_template, Flask

app = Flask(__name__)


@app.route("/")
def top():
    return render_template('index.html')


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # EXPERIMENTAL: use gevent for slow performance issue with Chrome.
        # https://stackoverflow.com/a/29887309/13220031
        # http_server = WSGIServer((sys.argv[1], int(sys.argv[2])), app)
        # http_server.serve_forever()
        pass
    else:
        app.run(debug=True, threaded=True, port=5001)
