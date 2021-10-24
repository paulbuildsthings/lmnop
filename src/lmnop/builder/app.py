import sys

from invoke import Collection, Program
from invoke.config import Config

from .. import __version__
from . import tasks


# this modifies the config file searching and makes it search for these files:
#    /etc/builder.yaml
#    ~/.builder.yaml
#    builder.yaml
#    BUILDER_RUN_ECHO  <- environment variable example
class AppConfig(Config):
    prefix = "builder"


def run():
    program = Program(
        binary="builder",
        version=__version__,
        config_class=AppConfig,
        namespace=Collection.from_module(tasks),
    )
    sys.exit(program.run())


if __name__ == "__main__":
    run()
