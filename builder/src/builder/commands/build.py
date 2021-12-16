import fcntl
import fileinput
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from time import perf_counter

import yaml
from schema import And, Optional, Or, Schema, Use

from builder.colors import cyan, green, red, yellow
from builder.console import execute, pipe
from builder.database import conn as db

# we will only deploy to this branch
LMNOP_DEPLOY_BRANCH = os.environ.get("LMNOP_DEPLOY_BRANCH", "main")
LMNOP_HOMEPAGE_URL = os.environ.get("LMNOP_HOMEPAGE_URL", "http://localhost:30001")
LMNOP_FUNCTION_URL = os.environ.get("LMNOP_FUNCTION_URL", "http://localhost:30001/function/[]").replace("[", "{").replace("]", "}")
LMNOP_GATEWAY = os.environ.get("LMNOP_GATEWAY", "http://host.docker.internal:30001")
LMNOP_REGISTRY = os.environ.get("LMNOP_REGISTRY", "host.docker.internal:30002/lmnop")


@contextmanager
def lock(repo_path):
    with open(os.path.join(repo_path, ".deploy.lock"), "w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def process_function_configuration(repo_name, temporary_path, source_path, tag):
    with open(os.path.join(source_path, "function.yml"), "rt") as f:
        function = yaml.safe_load(f)

    def validate_cpu(x):
        m = re.match("^([0-9]+)m$", x)
        if not m.groups():
            return False

        # limit to no more than 1 CPU
        value = int(m.group(1))
        if value < 50 or value > 1000:
            return False

        return True

    def validate_memory(x):
        m = re.match("^([0-9]+)Mi$", x)
        if not m.groups():
            return False

        # limit to no more than 4GB memory
        value = int(m.group(1))
        if value < 32 or value > 4096:
            return False

        return True

    schema = Schema({
        "template": And(str, Use(str.strip), len),
        Optional("requests"): {
            Optional("cpu"): And(str, Use(str.strip), len, validate_cpu),
            Optional("memory"): And(str, Use(str.strip), len, validate_memory),
        },
        Optional("limits"): {
            Optional("cpu"): And(str, Use(str.strip), len, validate_cpu),
            Optional("memory"): And(str, Use(str.strip), len, validate_memory),
        },
        Optional("environment"): {And(str, Use(str.strip), len): Or(str, int)},
        Optional("secrets"): [And(str, Use(str.strip), len)],
        Optional("options"): {And(str, Use(str.strip), len): Or(str, int)},
    })

    # validate and clean the function configuration
    function = schema.validate(function)

    # give default values for requests and limits
    if "requests" not in function:
        function["requests"] = {}
    if "cpu" not in function["requests"]:
        function["requests"]["cpu"] = "50m"
    if "memory" not in function["requests"]:
        function["requests"]["memory"] = "64Mi"
    if "limits" not in function:
        function["limits"] = {}
    if "cpu" not in function["limits"]:
        function["limits"]["cpu"] = "100m"
    if "memory" not in function["limits"]:
        function["limits"]["memory"] = "128Mi"

    if "environment" not in function:
        function["environment"] = {}
    if "secrets" not in function:
        function["secrets"] = []
    if "options" not in function:
        function["options"] = {}

    definition = {
        "version": "1.0",
        "provider": {
            "name": "openfaas",
            "gateway": LMNOP_GATEWAY,
        },
        "functions": {
            repo_name: {
                "lang": function["template"],
                "handler": os.path.join(temporary_path, "source"),
                "image": f"{LMNOP_REGISTRY}/{repo_name}:{tag}",
                "requests": function["requests"],
                "limits": function["limits"],
                "environment": function["environment"],
                "secrets": function["secrets"],
                "readonly_root_filesystem": True,
                "build_args": function["options"],
            }
        }
    }

    with open(os.path.join(temporary_path, "functions.yml"), "wt") as f:
        yaml.dump(definition, f)

    return definition


def run(root_path, repo_name):
    print(cyan(f"Processing {repo_name} for deployment."), flush=True)

    # interesting to know how long it takes to build things
    timer = perf_counter()

    # this is the actual stack file that openfaas will get
    definition = {}

    # get the actual repo contents and put it into a temporary directory
    try:
        with tempfile.TemporaryDirectory() as td:
            repo_path = os.path.join(root_path, repo_name)
            source_path = os.path.join(td, "source")
            os.mkdir(source_path)

            for line in fileinput.input(files=["-"]):
                (_, revision, reference) = line.split()
                if reference != f"refs/heads/{LMNOP_DEPLOY_BRANCH}":
                    print(yellow(f"Skipping {reference} because we only deploy changes to {LMNOP_DEPLOY_BRANCH}."), flush=True)
                    continue

                # prevent issue with accessing the quarantined files in git
                os.environ.pop("GIT_QUARANTINE_PATH", None)

                # acquire a lock on the repository
                with lock(repo_path):
                    # after this command we will have a copy of our repository in our temp file
                    pipe(["git", "archive", "--format=tar", revision], ["tar", "--warning=none", "-x", "-C", source_path])

                    # process the function definition
                    definition = process_function_configuration(repo_name, td, source_path, revision)

                    # link the templates into place
                    os.symlink("/home/lmnop/templates", os.path.join(td, "template"))

                    # call "faas up" to build the container and send it to the openfaas gateway
                    execute(["faas", "up", "-f", "functions.yml", "--envsubst=false", "--gateway", LMNOP_GATEWAY], cwd=td)

        # get the size of the repository (after working with it)
        # if we try to get the size of the repo BEFORE we work on it then everything fails
        result = execute(["du", "-s", "--block-size=1", repo_path], capture=True)
        repo_bytes, _ = result.strip().split(maxsplit=1)
        print(f"Repository named {repo_name} in {repo_path} is {repo_bytes} bytes.", flush=True)

        # record a successful deployment
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lmnop.function
                        (name, size, configuration)
                    VALUES
                        (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        size = excluded.size,
                        configuration = excluded.configuration,
                        marked_for_delete = FALSE
                """, [repo_name, repo_bytes, json.dumps(definition)])

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lmnop.log_deployment
                        (authn_username, function_name, function_size, timer, configuration)
                    VALUES
                        (%s, %s, %s, %s, %s)
                """, [os.environ.get("GIT_COMMITTER_NAME", "unknown"), repo_name, repo_bytes, perf_counter() - timer, json.dumps(definition)])

        # use a dict as they are guaranteed to preserve insertion order
        urls = {}
        urls[f"{LMNOP_HOMEPAGE_URL}/function/{repo_name}"] = None
        urls[LMNOP_FUNCTION_URL.format(repo_name)] = None

        print("------>")
        print("------> " + green(f"Your function {repo_name} has been deployed successfully and is coming online."))
        print("------> " + green("You can see your function at these URLs:"))
        print("------>")
        for url in urls.keys():
            print("------>    " + green(url, bold=True))
        print("------>")

        print()
    except Exception as e:
        try:
            with db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO lmnop.log_deployment
                            (authn_username, function_name, configuration, errors)
                        VALUES
                            (%s, %s, %s, %s)
                    """, [os.environ.get("GIT_COMMITTER_NAME", "unknown"), repo_name, json.dumps(definition), str(e)])
        except Exception as e:
            print(yellow(f"An error occurred while trying to record this deployment: {e}"), file=sys.stderr)

        print(red(f"An error occurred while building the repository: {e}", bold=True), file=sys.stderr)
        return 1
