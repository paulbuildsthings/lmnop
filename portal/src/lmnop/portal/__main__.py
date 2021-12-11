import logging
import sys

from lmnop.portal.app import load

if __name__ == "__main__":
    # send application logs to stdout
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)-8s - %(message)s",
        level=logging.DEBUG,
        stream=sys.stdout,
    )

    # send access logs to stderr and do not propagate them to the root logger
    access_logger = logging.getLogger("werkzeug")
    access_logger.addHandler(logging.StreamHandler(stream=sys.stderr))
    access_logger.propagate = False

    # run only on localhost for testing
    load().run(host="127.0.0.1", port=8080, debug=True, use_reloader=False)
