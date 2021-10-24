# this file is copied from the python library called "fabric"
import sys

from . import colors


def warn(msg):
    sys.stderr.write(colors.magenta("\nWARNING: {}\n\n".format(msg)))


def abort(msg):
    sys.stderr.write(colors.red("\nFATAL: {}\n\n".format(msg)))

    e = SystemExit(1)
    e.message = msg
    raise e


def confirm(question, assume_yes=True):
    suffix = "Y/n" if assume_yes else "y/N"

    # Loop till we get something we like
    while (True):
        response = input(colors.red("{} [{}] ".format(question, suffix)))
        response = response.lower().strip()  # normalize

        # default
        if (not response):
            return assume_yes

        # yes
        if (response in ["y", "yes"]):
            return True

        # no
        if (response in ["n", "no"]):
            return False

        # didn't get empty, yes or no, so complain and loop
        print("I didn't understand you. Please specify '(y)es' or '(n)o'.")
