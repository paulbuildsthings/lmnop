import fcntl
import fileinput
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime
from time import perf_counter

import psycopg2
import psycopg2.extras
import yaml
from invoke import task
from schema import And, Optional, Or, Schema, Use

from .colors import cyan, green, yellow
from .console import abort

# we will only deploy to this branch
LMNOP_DEPLOY_BRANCH = os.environ.get("LMNOP_DEPLOY_BRANCH", "main")
LMNOP_HOME = os.environ.get("LMNOP_HOME", "http://localhost:8080")
LMNOP_GATEWAY = os.environ.get("LMNOP_GATEWAY", "http://localhost:8080")
LMNOP_REGISTRY = os.environ.get("LMNOP_REGISTRY", "http://ghcr.io/github")


@contextmanager
def database():
    conn = None
    try:
        conn = psycopg2.connect(**{
            "host": os.environ.get("LMNOP_DATABASE_HOST", "localhost"),
            "dbname": os.environ.get("LMNOP_DATABASE_NAME", "lmnop"),
            "user": os.environ.get("LMNOP_DATABASE_USERNAME", "lmnop"),
            "password": os.environ.get("LMNOP_DATABASE_PASSWORD", None),
            "sslmode": "prefer",
            "cursor_factory": psycopg2.extras.DictCursor,
        })
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        try:
            if conn is not None:
                conn.rollback()
        except (AttributeError, psycopg2.Error):
            pass

        raise
    finally:
        try:
            if conn is not None:
                conn.autocommit = True
        except (AttributeError, psycopg2.Error):
            pass


@contextmanager
def lock(repo_path):
    with open(os.path.join(repo_path, ".deploy.lock"), "w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


@task(positional=["root_path", "repo_name"])
def prepare(c, root_path, repo_name):
    """initialize a new repository"""

    # look in database and remove any repos that have been marked for deletion
    with database() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM lmnop.project WHERE marked_for_delete IS TRUE")
            for row in cur:
                repo_path = os.path.join(root_path, row["name"])
                c.run(f"rm -rf {repo_path}")

    # check to see if the repo already exists
    repo_path = os.path.join(root_path, repo_name)
    if not os.path.exists(repo_path):
        c.run(f"git init --bare {repo_path}")

        # update the repo's description
        with open(os.path.join(repo_path, "description"), "wt") as f:
            print(f"Originally pushed {datetime.now()} by {os.environ.get('GIT_COMMITTER_NAME', 'unknown')}.", file=f)


@task(positional=["root_path", "repo_name"])
def receive(c, root_path, repo_name):
    """build a project with openfaas"""
    print(cyan(f"Processing {repo_name} for deployment."))

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
                    print(yellow(f"Skipping {reference} because we only deploy changes to {LMNOP_DEPLOY_BRANCH}."))
                    continue

                # prevent issue with accessing the quarantined files in git
                os.environ.pop("GIT_QUARANTINE_PATH", None)

                # acquire a lock on the repository
                with lock(repo_path):
                    # after this command we will have a copy of our repository in our temp file
                    c.run(f"git archive --format=tar {revision} | tar --warning=none -x -C {source_path}")

                    # process the function definition
                    definition = process_function_configuration(repo_name, td, source_path, revision)

                    # link the templates into place
                    os.symlink("/home/lmnop/templates", os.path.join(td, "template"))

                    # call "faas up" to build the container and send it to the openfaas gateway
                    with c.cd(td):
                        c.run(f"faas up -f functions.yml --envsubst=false --gateway {LMNOP_GATEWAY}")

        # get the size of the repository (after working with it)
        # if we try to get the size of the repo BEFORE we work on it then everything fails
        result = c.run(f"du -s --block-size=1 {repo_path}", hide=True)
        repo_bytes, _ = result.stdout.strip().split(maxsplit=1)
        print(f"Repository in {repo_path} is {repo_bytes} bytes.")

        # record a successful deployment
        with database() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lmnop.project
                        (name, size, configuration)
                    VALUES
                        (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        size = excluded.size,
                        configuration = excluded.configuration
                """, [repo_name, repo_bytes, json.dumps(definition)])

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lmnop.deployment
                        (authn_name, project_name, project_size, timer, configuration)
                    VALUES
                        (%s, %s, %s, %s, %s)
                """, [os.environ.get("GIT_COMMITTER_NAME", "unknown"), repo_name, repo_bytes, perf_counter() - timer, json.dumps(definition)])

        print()
        print(green(f"Your project {repo_name} has been deployed successfully and is coming online."))
        print(green(f"You can see your function here: {LMNOP_HOME}/function/{repo_name}"))
        print()
    except Exception as e:
        with database() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lmnop.deployment
                        (authn_name, project_name, configuration, errors)
                    VALUES
                        (%s, %s, %s, %s)
                """, [os.environ.get("GIT_COMMITTER_NAME", "unknown"), repo_name, json.dumps(definition), str(e)])

        # this will exit with an error code and interrupt the git push
        abort(f"An error occurred during deployment: {e}")


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

        # limit to no more than 8GB memory
        value = int(m.group(1))
        if value < 32 or value > 8192:
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
