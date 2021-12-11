import traceback

from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from ...app import csrf
from ...tools import get_ip_address, get_user_name
from . import actions, view


@view.route("/")
def index():
    data = actions.select_functions()
    return render_template(
        "functions/index.html",
        data={"functions": data}
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
        return redirect(url_for("functions.index"))

    action = data.get("action")

    try:
        if action == "replicas":
            return scale_function(data.get("name"), data.get("replicas"))

        if action == "delete":
            return delete_function(data.get("name"))
    except Exception as e:
        app.logger.error(f"error trying to perform action: {e}")
        app.logger.error(traceback.format_exc())
        flash("An error occurred when trying to perform this action.", "danger")
        return redirect(url_for("functions.index"))

    app.logger.warning("missing action from {}".format(ip))
    flash("No action was provided so no action was taken.", "danger")
    return redirect(url_for("functions.index"))


def scale_function(name, replicas):
    try:
        replicas = int(replicas)
    except (TypeError, ValueError):
        app.logger.warning("invalid replica count: {}".format(replicas))
        flash("You have provided an invalid replica count.", "danger")
        return redirect(url_for("functions.index"))

    if replicas < 0:
        app.logger.warning("invalid replica count: {}".format(replicas))
        flash("You may not have a negative number of replicas.", "danger")
        return redirect(url_for("functions.index"))

    if replicas > 5:
        app.logger.warning("invalid replica count: {}".format(replicas))
        flash("You may not have a more than five replicas.", "danger")
        return redirect(url_for("functions.index"))

    try:
        actions.scale_function(name, replicas)
        app.logger.info("scaling {} to {}".format(name, replicas))
        flash("The function '{}' is being scaled to {}.".format(name, replicas), "success")
        return redirect(url_for("functions.index"))
    except Exception as e:
        app.logger.warning("an error occurred when scaling {} to {}: {}".format(name, replicas, e))
        flash("An error occurred while trying to scale '{}' to {}.".format(name, replicas), "danger")
        return redirect(url_for("functions.index"))


def delete_function(name):
    try:
        actions.delete_function(name)
        app.logger.info("deleting {}".format(name))
        flash("The function '{}' is marked for deletion.".format(name), "success")
        return redirect(url_for("functions.index"))
    except Exception as e:
        app.logger.warning("an error occurred when deleting {}: {}".format(name, e))
        flash("An error occurred while trying to delete '{}'.".format(name), "danger")
        return redirect(url_for("functions.index"))
