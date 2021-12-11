from flask import Blueprint

health = Blueprint("health", "lmnop.portal.blueprints.health", static_folder=None, template_folder=None)
main = Blueprint("main", "lmnop.portal.blueprints.main", static_folder="static", template_folder="templates")
password = Blueprint("password", "lmnop.portal.blueprints.password", static_folder=None, template_folder="templates")
functions = Blueprint("functions", "lmnop.portal.blueprints.functions", static_folder=None, template_folder="templates")
secrets = Blueprint("secrets", "lmnop.portal.blueprints.secrets", static_folder=None, template_folder="templates")
