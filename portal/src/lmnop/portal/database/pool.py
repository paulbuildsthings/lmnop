import logging
import threading
import uuid
from contextlib import contextmanager

import psycopg2
import tenacity
from psycopg2.extensions import (TRANSACTION_STATUS_IDLE,
                                 TRANSACTION_STATUS_UNKNOWN)
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)


class PoolError(psycopg2.Error):
    pass


class ConnectionPool:
    def __init__(self, minconn, maxconn, retry, *args, **kwargs):
        self.minconn = int(minconn)
        self.maxconn = int(maxconn)

        self._args = args
        self._kwargs = kwargs

        self._pool = []   # connections that are available
        self._used = {}   # connections currently in use

        # control access to the thread pool
        self._lock = threading.RLock()

        # control retries
        self._retry = retry

    def getconn(self, key):
        with self._lock:
            # this key already has a connection so return it
            if key in self._used:
                return self._used[key]

            # our pool is currently empty
            if len(self._pool) == 0:
                # we've given out all of the connections that we want to
                if len(self._used) == self.maxconn:
                    raise PoolError("connection pool exhausted")

                # create new connection and put into the list of available
                # connections. we'll pop it off in a minute and return it
                conn = self._connect()
                self._pool.append(conn)

            # pull a connection off of the pool and test it. if it fails then
            # we're going to drop it and create a new one
            conn = self._pool.pop()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            except psycopg2.Error as e:
                logger.warning("connection failed: {}".format(e))

                # try to rollback anything the connection was doing
                try:
                    if conn is not None:
                        conn.rollback()
                except Exception as e:
                    logger.warning("could not rollback connection: {}".format(e))

                # test failed, make a new connection
                logger.warning("creating new connection to replace failed connection")
                conn = self._connect()

            # move the connection to the "in use" list and return it
            self._used[key] = conn
            return conn

    def putconn(self, key, close=False):
        with self._lock:
            conn = self._used.get(key)
            if conn is None:
                raise PoolError("no connection with that key")

            if len(self._pool) < self.minconn and not close:
                # return the connection into a consistent state before putting
                # it back in the pool by rolling back or forcibly disconnecting
                try:
                    status = conn.info.transaction_status
                    if status == TRANSACTION_STATUS_UNKNOWN:
                        # server connection lost
                        conn.close()
                    if status != TRANSACTION_STATUS_IDLE:
                        # connection in error or in transaction
                        conn.rollback()

                    # regular idle connection. the connection will be checked
                    # before we give it out again, just so you know.
                    self._pool.append(conn)
                except psycopg2.Error as e:
                    # we weren't able to reset the connection so do not put it
                    # back into the pool. log the bad news.
                    logger.warning("could not reset database connection when putting back into the pool: {}".format(e))
            else:
                # just close the connection. it's ok if we're not able to close
                # the connection, though a warning is nice.
                try:
                    conn.close()
                except psycopg2.Error as e:
                    logger.warning("could not close database connection when putting back into the pool: {}".format(e))

            # here we check for the presence of key because it can happen that
            # a thread tries to put back a connection after a call to close
            if key in self._used:
                del self._used[key]

    def _connect(self):
        # if set then we will not retry connections
        retry_flag = threading.Event()

        # control retries
        if self._retry:
            retry_flag.clear()
        else:
            retry_flag.set()

        counter = 0
        for attempt in tenacity.Retrying(
                reraise=True,
                stop=tenacity.stop_when_event_set(retry_flag),
                wait=tenacity.wait_fixed(0.1) + tenacity.wait_random(0, 0.9),
        ):
            with attempt:
                counter = counter + 1
                try:
                    # connect to the database with the arguments provided when the
                    # pool was initialized. enable autocommit for consistency.
                    # this will retry using the "tenacity" library.
                    conn = psycopg2.connect(*self._args, **self._kwargs)
                    conn.autocommit = True
                    return conn
                except Exception as e:
                    logger.error("failed to connect to database on attempt {}: {}".format(counter, e))
                    raise


class DatabaseClient:
    def __init__(self, minconn=2, maxconn=32, retry=True, **kwargs):
        # initialize the connection pool
        self.pool = ConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            retry=retry,
            cursor_factory=DictCursor,
            **kwargs,
        )

    @contextmanager
    def conn(self, autocommit=True):
        conn = None
        key = str(uuid.uuid4())

        try:
            conn = self.pool.getconn(key)
            conn.autocommit = autocommit
            yield conn
            conn.commit()
        except Exception:
            try:
                if conn is not None:
                    conn.rollback()
            except (AttributeError, psycopg2.Error) as e:
                logger.warning("could not rollback connection: {}".format(e))

            raise
        finally:
            try:
                if conn is not None:
                    conn.autocommit = True
            except (AttributeError, psycopg2.Error) as e:
                logger.warning("could not reset autocommit on connection: {}".format(e))

            try:
                self.pool.putconn(key)
            except Exception as e:
                logger.warning("could not put connection back into pool: {}".format(e))
