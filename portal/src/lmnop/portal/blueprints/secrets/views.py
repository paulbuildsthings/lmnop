import re
import traceback

from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from ...app import csrf
from ...tools import get_ip_address, get_user_name
from . import actions, view


@view.route("/")
def index():
    data = actions.select_secrets()
    return render_template(
        "secrets/index.html",
        data={"secrets": data},
    )


@view.route("/", methods=["POST"])
def save():
    ip = get_ip_address()
    user_name = get_user_name()

    try:
        # apply csrf protection
        csrf.protect()
    except CSRFError as e:
        app.logger.error("intercepted CSRF error from {} for {}: {}".format(ip, user_name, e))
        raise

    # see if we received a request body
    data = request.form
    if not data:
        return redirect(url_for("secrets.index"))

    action = data.get("action")

    try:
        if action == "create":
            return create_secret(data.get("name"), data.get("value"))

        if action == "update":
            return update_secret(data.get("name"), data.get("value"))

        if action == "delete":
            return delete_secret(data.get("name"))
    except Exception as e:
        app.logger.error(f"error trying to perform action: {e}")
        app.logger.error(traceback.format_exc())
        flash("An error occurred when trying to perform this action.", "danger")
        return redirect(url_for("secrets.index"))

    app.logger.warning("missing action from {}".format(ip))
    flash("No action was provided so no action was taken.", "danger")
    return redirect(url_for("secrets.index"))


def create_secret(name, value):
    try:
        # validate the name
        matcher = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*")
        if not matcher.match(name):
            flash("The secret name '{}' is not valid. Secret names must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character.".format(name), "danger")
            return redirect(url_for("secrets.index"))

        actions.insert_secret(name, value)
        app.logger.info("creating {}".format(name))
        flash("The secret '{}' has been created.".format(name), "success")
        return redirect(url_for("secrets.index"))
    except Exception as e:
        app.logger.warning("an error occurred when creating {}: {}".format(name, e))
        flash("An error occurred while trying to create '{}'.".format(name), "danger")
        return redirect(url_for("secrets.index"))


def update_secret(name, value):
    try:
        actions.update_secret(name, value)
        app.logger.info("deleting {}".format(name))
        flash("The secret '{}' has been updated.".format(name), "success")
        return redirect(url_for("secrets.index"))
    except Exception as e:
        app.logger.warning("an error occurred when updating {}: {}".format(name, e))
        flash("An error occurred while trying to update '{}'.".format(name), "danger")
        return redirect(url_for("secrets.index"))


def delete_secret(name):
    try:
        actions.delete_secret(name)
        app.logger.info("deleting {}".format(name))
        flash("The secret '{}' has been deleted.".format(name), "success")
        return redirect(url_for("secrets.index"))
    except Exception as e:
        app.logger.warning("an error occurred when deleting {}: {}".format(name, e))
        flash("An error occurred while trying to delete '{}'.".format(name), "danger")
        return redirect(url_for("secrets.index"))
