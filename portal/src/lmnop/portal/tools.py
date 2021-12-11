import inspect
import logging
import os

import importlib_resources
from flask import Flask, request, session

logger = logging.getLogger()


def get_ip_address():
    ip_addresses = request.headers.get("X-Forwarded-For")
    if not ip_addresses:
        logger.warning("missing X-Forwarded-For header")
        return request.remote_addr

    # ip addresses could come in a comma separated list
    import re
    p = re.compile(r"\s*,\s*")
    ip_address_list = re.split(p, ip_addresses)
    if len(ip_address_list) == 0:
        logger.warning("no IP addresses found in X-Forwarded-For header")
        return request.remote_addr

    if len(ip_address_list) == 1:
        # if there is only one address then that is the address of the client.
        ip_address = ip_address_list[0]
    else:
        # the X-Forwarded-For field gets populated by proxies. the last proxy
        # in the line before us is haproxy. so we want the second to last
        # because that will be the actual source of our client.
        ip_address = ip_address_list[-2].strip()

    # make sure that we even got an address
    if not ip_address:
        logger.warning("no IP addresses found in X-Forwarded-For header")

    return ip_address


# this depends on apache config that is sticking the REMOTE_USER in this
# header when proxying the connection to us.
def get_user_name():
    user_name = request.headers.get("X-Forwarded-User")

    if not user_name or user_name == "(null)":
        logger.warning("missing X-Forwarded-User header")
        return

    return user_name


def load_configuration(app: Flask, package: str = None, path: str = None, environment: str = None) -> str:
    if environment is None:
        environment = os.environ.get("FLASK_ENV") or "development"

    if package is None:
        if path is None:
            path = os.environ.get("CONFIGURATIONS")

        if path is None:
            # load from a package called "{calling_package}.configurations"
            calling_package = inspect.currentframe().f_back.f_globals["__package__"]
            if calling_package:
                package = ".".join([calling_package, "configurations"])
            else:
                package = "configurations"

            with importlib_resources.as_file(importlib_resources.files(package) / "{}.conf".format(environment)) as path:
                logger.info("loading configuration from '{}'".format(path))
                app.config.from_pyfile(path)
        else:
            path = os.path.join(path, "{}.conf".format(environment))
            logger.info("loading configuration from '{}'".format(path))
            app.config.from_pyfile(path)

    else:
        with importlib_resources.as_file(importlib_resources.files(package) / "{}.conf".format(environment)) as path:
            logger.info("loading configuration from '{}'".format(path))
            app.config.from_pyfile(path)

    return environment


def set_secret_key(app: Flask) -> None:
    # load the secret key which is used for sessions
    if "SECRET_KEY_FILE" in app.config and app.config["SECRET_KEY_FILE"]:
        if os.path.exists(app.config["SECRET_KEY_FILE"]):
            with open(app.config["SECRET_KEY_FILE"], "rt") as f:
                app.secret_key = f.read().strip()
    if app.secret_key is None:
        logger.warning("using a static secret key")

        # keep the secret key static to avoid resetting sessions every time the
        # application restarts which is very annoying when doing development.
        app.secret_key = "test"

    # make the session "permanent" so that it doesn't disappear inadvertently
    @app.before_request
    def make_session_permanent():
        session.permanent = True
