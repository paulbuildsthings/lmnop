import subprocess  # noqa: S404
import sys
from typing import NoReturn, Union

from . import colors


def warn(msg) -> None:
    print(colors.magenta("\nWARNING: {}\n\n".format(msg)), file=sys.stderr, flush=True)


def abort(msg) -> NoReturn:
    print(colors.red("\nFATAL: {}\n\n".format(msg)), file=sys.stderr, flush=True)

    e = SystemExit(1)
    e.message = msg
    raise e


def pipe(cmd1: list, cmd2: list, echo: bool = False, fail: bool = True, cwd: str = None) -> bool:
    # make sure each command is a list
    if not isinstance(cmd1, list):
        raise RuntimeError("executing raw commands is not supported")
    if not isinstance(cmd2, list):
        raise RuntimeError("executing raw commands is not supported")

    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, cwd=cwd)  # noqa: S603
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, cwd=cwd)  # noqa: S603

    # wait for the commands to finish
    p1.wait()
    p2.wait()

    # only a zero from BOTH indicates success
    response1 = p1.returncode
    response2 = p2.returncode

    if response1 == 0 and response2 == 0:
        return True

    if response1 != 0:
        if fail:
            abort("'{}' returned {}".format(" ".join(cmd1), response1))
        else:
            warn("'{}' returned {}".format(" ".join(cmd1), response1))

    if response2 != 0:
        if fail:
            abort("'{}' returned {}".format(" ".join(cmd2), response2))
        else:
            warn("'{}' returned {}".format(" ".join(cmd2), response2))

    return False


# echo: whether to print the command that is about to be executed
# fail: should we abort on error or just show a warning
# capture: should we capture the output of the command and return it
# cwd: the current working directory to use
def execute(cmd: list, echo: bool = False, fail: bool = True, capture: bool = False, cwd: str = None) -> Union[bool, str]:
    # make sure the comand is a list
    if not isinstance(cmd, list):
        raise RuntimeError("executing raw commands is not supported")

    if echo:
        print(colors.white(" ".join(cmd), bold=True), flush=True)

    # if we're capturing output then this is where it goes
    output = []

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)  # noqa: S603
    for c in iter(lambda: p.stdout.read(1), b''):
        line = c.decode("utf8", errors="replace")
        if capture:
            output.append(line)
        else:
            print(line, end="", flush=True)

    # wait for the command to finish
    p.wait()

    # only a zero indicates success
    response = p.returncode
    if response == 0:
        if capture:
            return "".join(output)
        else:
            return True

    if fail:
        abort("'{}' returned {}".format(" ".join(cmd), response))
    else:
        warn("'{}' returned {}".format(" ".join(cmd), response))

    if capture:
        return "".join(output)
    else:
        return False
