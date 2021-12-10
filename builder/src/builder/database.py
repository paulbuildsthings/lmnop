import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras


@contextmanager
def conn():
    conn = None
    try:
        conn = psycopg2.connect(**{
            "host": os.environ.get("LMNOP_DATABASE_HOST", "localhost"),
            "port": os.environ.get("LMNOP_DATABASE_PORT", 5432),
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
