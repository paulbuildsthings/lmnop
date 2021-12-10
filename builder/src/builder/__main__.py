import argparse
import sys

from builder import __version__


def main():
    parser = argparse.ArgumentParser(prog="builder")

    # arguments common to all components
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="return the version number and exit",
    )

    # require a subcommand
    subparsers = parser.add_subparsers(
        title="command",
        description="which builder component to run",
        dest="command",
        metavar="COMMAND",
    )
    subparsers.required = True

    subparser = subparsers.add_parser(
        "prepare",
        help="prepare the build system to accept a repository",
    )
    subparser.add_argument(
        "root",
        help="the root path where all repositories are stored",
    )
    subparser.add_argument(
        "name",
        help="the name of the new repository",
    )

    subparser = subparsers.add_parser(
        "build",
        help="build a repository that is in the pre-receive state",
    )
    subparser.add_argument(
        "root",
        help="the root path where all repositories are stored",
    )
    subparser.add_argument(
        "name",
        help="the name of the new repository",
    )

    args = parser.parse_args()

    if args.command == "prepare":
        from .commands.prepare import run
        sys.exit(run(args.root, args.name))

    if args.command == "build":
        from .commands.build import run
        sys.exit(run(args.root, args.name))

    print(f"unknown command: {args.command}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
