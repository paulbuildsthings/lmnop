import os
import sys
from datetime import datetime

from builder.colors import red
from builder.console import execute
from builder.database import conn as db


def run(root_path, repo_name) -> int:
    try:
        # look in database and remove any repos that have been marked for deletion
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM lmnop.function
                    WHERE marked_for_delete IS TRUE
                    RETURNING name
                """)
                for row in cur:
                    repo_path = os.path.join(root_path, row["name"])
                    execute(["rm", "-rf", repo_path])

        # check to see if the repo already exists
        repo_path = os.path.join(root_path, repo_name)
        if not os.path.exists(repo_path):
            execute(["git", "init", "--bare", repo_path])

            # update the repo's description
            with open(os.path.join(repo_path, "description"), "wt") as f:
                print(f"Originally pushed {datetime.now()} by {os.environ.get('REMOTE_USER', 'unknown')}.", file=f)

        return 0
    except Exception as e:
        print(red(f"An error occurred while preparing the repository to be pushed: {e}", bold=True), file=sys.stderr)
        return 1
