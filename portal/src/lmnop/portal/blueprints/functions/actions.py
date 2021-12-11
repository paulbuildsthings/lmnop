import json

import requests
from flask import current_app as app

from ...app import db_client

# # list functions
# curl -X 'GET' \
#   'http://localhost:30001/system/functions' \
#   -H 'accept: application/json' | jq
#
# # delete function
# curl -X 'DELETE' \
#   'http://localhost:30001/system/functions' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{"functionName": "testy"}'
#
# # scale a function
# curl -X 'POST' \
#   'http://localhost:30001/system/scale-function/testy' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{"replicas": 1}'


def select_functions() -> list[dict]:
    root = app.config["LMNOP_GATEWAY"]
    response = requests.get(
        f"{root}/system/functions",
        headers={"accept": "application/json"},
    )
    response.raise_for_status()
    data = response.json()

    homepage_url = app.config["LMNOP_HOMEPAGE_URL"]
    function_url = app.config["LMNOP_FUNCTION_URL"]

    results = []

    with db_client.conn() as conn:
        for datum in data:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, configuration, marked_for_delete
                    FROM lmnop.function
                    WHERE name = %s
                """, [datum["name"]])
                row = cur.fetchone()

            # use a dict as they are guaranteed to preserve insertion order
            urls = {}
            urls[f"{homepage_url}/function/{datum['name']}"] = None
            urls[function_url.format(datum["name"])] = None

            result = {
                "name": datum["name"],
                "image": datum["image"],
                "invocations": datum.get("invocationCount", 0),
                "replicas": datum["replicas"],
                "urls": list(urls.keys()),
            }

            if row is None:
                results.append(result)
            else:
                results.append({
                    **result,
                    "configuration": row["configuration"],
                    "marked_for_delete": row["marked_for_delete"],
                })

    return sorted(results, key=lambda x: x["name"])


def delete_function(name: str):
    root = app.config["LMNOP_GATEWAY"]
    response = requests.delete(
        f"{root}/system/functions",
        headers={"accept": "application/json", "content-type": "application/json"},
        data=json.dumps({"functionName": name}),
    )
    response.raise_for_status()

    with db_client.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE lmnop.function
                SET marked_for_delete = TRUE
                WHERE name = %s
            """, [name])


def scale_function(name: str, scale: int):
    root = app.config["LMNOP_GATEWAY"]
    response = requests.post(
        f"{root}/system/scale-function/{name}",
        headers={"accept": "application/json", "content-type": "application/json"},
        data=json.dumps({"replicas": scale}),
    )
    response.raise_for_status()
