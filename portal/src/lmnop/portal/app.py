import logging

from flask import Flask
from flask_wtf.csrf import CSRFProtect

import lmnop.portal.tools
from lmnop import __version__
from lmnop.portal.database import DatabaseClient

# maintains a database connection pool
db_client = DatabaseClient()

# implements csrf protection on the password form
csrf = CSRFProtect()


def load():
    app = Flask(__name__, static_folder=None)
    environment = lmnop.portal.tools.load_configuration(app, "configurations")
    app.logger.info("starting web application in '{}' mode with version {}".format(environment, __version__))

    # load the secret key so that sessions work
    lmnop.portal.tools.set_secret_key(app)

    # connect to the configured database
    db_client.init_app(app, "lmnop", **app.config.get("DATABASE"))

    # initialize csrf protection
    csrf.init_app(app)

    from .blueprints.main import view as blueprint
    prefix = app.config.get("APPLICATION_ROOT", "")
    blueprint_prefix = prefix
    app.logger.info("using main url prefix '{}'".format(blueprint_prefix))
    app.register_blueprint(blueprint, url_prefix=blueprint_prefix)

    from .blueprints.password import view as blueprint
    blueprint_prefix = "{}/password".format(prefix)
    app.logger.info("using password url prefix {}".format(blueprint_prefix))
    app.register_blueprint(blueprint, url_prefix=blueprint_prefix)

    from .blueprints.functions import view as blueprint
    blueprint_prefix = "{}/functions".format(prefix)
    app.logger.info("using functions url prefix {}".format(blueprint_prefix))
    app.register_blueprint(blueprint, url_prefix=blueprint_prefix)

    from .blueprints.secrets import view as blueprint
    blueprint_prefix = "{}/secrets".format(prefix)
    app.logger.info("using secrets url prefix {}".format(blueprint_prefix))
    app.register_blueprint(blueprint, url_prefix=blueprint_prefix)

    from .blueprints.health import health as blueprint
    blueprint_prefix = "/health"
    app.logger.info("using health url prefix {}".format(blueprint_prefix))
    app.register_blueprint(blueprint, url_prefix=blueprint_prefix)

    @app.template_filter("pretty_size")
    def pretty_size_filter(value):
        suffix = "B"
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if abs(value) < 1024.0:
                return "%3.2f %s%s" % (value, unit, suffix)
            value /= 1024.0
        return "%.2f %s%s" % (value, 'Y', suffix)

    # tell ourselves what we've mapped.
    if app.logger.isEnabledFor(logging.DEBUG):
        for url in app.url_map.iter_rules():
            app.logger.debug(repr(url))

    return app
