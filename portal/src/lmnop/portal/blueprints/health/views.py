from flask import jsonify, make_response

from . import health


@health.route("/check")
def check():
    return make_response(jsonify({
        "status": "pass",
        "message": "flux capacitor is fluxing",
    }), 200)
