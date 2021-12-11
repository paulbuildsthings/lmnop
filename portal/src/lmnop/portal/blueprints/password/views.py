import traceback
from urllib.parse import urlparse

from flask import Markup
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError
from passlib.hash import bcrypt
from zxcvbn import zxcvbn

from ...app import csrf, db_client
from ...tools import get_ip_address, get_user_name
from . import view


@view.route("/")
def index():
    user_name = get_user_name()
    return render_template("password/index.html", data={"user_name": user_name})


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
        return redirect(url_for("password.index"))

    password1 = data.get("password1")
    password2 = data.get("password2")

    # make sure that a password was even entered
    if not password1 or not password2:
        app.logger.warning("no password entered for {}".format(user_name))
        flash("You did not enter a new password.", "danger")
        return redirect(url_for("password.index"))

    # ensure the passwords match
    if password1 != password2:
        app.logger.warning("passwords do not match for {}".format(user_name))
        flash("Your new passwords do not match.", "danger")
        return redirect(url_for("password.index"))

    # make sure the password is sufficiently complex
    complexity = zxcvbn(password1, user_inputs=[user_name])
    if complexity["score"] < 3:
        app.logger.warning("password is not sufficiently complex for {}".format(user_name))
        message = "Your password is not sufficiently complex. {} {}".format(
            complexity["feedback"]["warning"],
            " ".join(complexity["feedback"]["suggestions"])
        ).strip()
        flash(message, "danger")
        return redirect(url_for("password.index"))

    hashed_password = bcrypt.hash(password1, ident="2y")

    conn = None
    try:
        conn = db_client.conn()
        conn.autocommit = False

        app.logger.info("changing password for {} from {}".format(user_name, ip))

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO lmnop.authn (username, password) VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE
                SET password = excluded.password
            """, [user_name, hashed_password])

            cur.execute("""
                INSERT INTO lmnop.log_password (username, ip, useragent)
                VALUES (%s, %s, %s)
            """, [user_name, ip, request.headers.get("user-agent")])

        conn.commit()
    except Exception as e:
        app.logger.error("could not change password for {} from {}: {}".format(user_name, ip, e))
        app.logger.error(traceback.format_exc())

        try:
            conn.rollback()
        except Exception:  # noqa: S110
            pass

        flash("An error occurred while trying to change your password.", "danger")
        return redirect(url_for("password.index"))
    finally:
        try:
            conn.autocommit = True
        except Exception:  # noqa: S110
            pass

    # convert the name of the git server to just a hostname
    url = urlparse(app.config["LMNOP_HOMEPAGE_URL"])

    # if we did actually change a password then say that
    flash(Markup(
        f"Successfully changed the password for {user_name}.<br/><br/>If you use "
        f"macOS then you will need to reset your password on the terminal by "
        f"running the command <code>git credential-osxkeychain erase</code> "
        f"and entering: <pre>host={url.netloc}\nprotocol={url.scheme}</pre> "
        f"<br/><br/>If you use Windows then you will need to reset your "
        f"password using the Windows Credential Manager."
    ), "success")
    return redirect(url_for("password.index"))
