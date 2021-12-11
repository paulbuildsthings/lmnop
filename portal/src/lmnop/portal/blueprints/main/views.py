from flask import current_app as app
from flask import render_template

from ...tools import get_user_name
from . import view


@view.route("/")
def index():
    user_name = get_user_name()

    return render_template("index.html", data={
        "user_name": user_name,
        "homepage_url": app.config["LMNOP_HOMEPAGE_URL"],
        "function_url": app.config["LMNOP_FUNCTION_URL"],
    })
