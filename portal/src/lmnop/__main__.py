import argparse
import sys

from lmnop import __version__

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="lmnop")
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="return the version number and exit",
    )
    args = parser.parse_args()

    # no actions at this level
    parser.print_help()
    sys.exit(2)
