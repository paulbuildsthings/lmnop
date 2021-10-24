import os

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def hello_world():
    return jsonify(
        {"headers": {k.lower(): v for (k, v) in request.headers}},
        {"environment": dict(os.environ)},
    )
