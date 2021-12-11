import json

import requests
from flask import current_app as app

# # list secrets
# curl -X 'GET' \
#   'http://localhost:30001/system/secrets' \
#   -H 'accept: application/json'
#
# # create a new secret
# curl -X 'POST' \
#   'http://localhost:30001/system/secrets' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{"name": "aws-key","value": "changeme"}'
#
# # update a secret
# curl -X 'PUT' \
#   'http://localhost:30001/system/secrets' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{"name": "aws-key","value": "changeme"}'
#
# # delete the secret
# curl -X 'DELETE' \
#   'http://localhost:30001/system/secrets' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{"name": "aws-key"}'


def select_secrets() -> list[dict]:
    root = app.config["LMNOP_GATEWAY"]
    response = requests.get(
        f"{root}/system/secrets",
        headers={"accept": "application/json"},
    )
    response.raise_for_status()
    data = response.json()

    results = []

    for datum in data:
        results.append({
            "name": datum["name"],
        })

    return sorted(results, key=lambda x: x["name"])


def insert_secret(name: str, value: str):
    root = app.config["LMNOP_GATEWAY"]
    response = requests.post(
        f"{root}/system/secrets",
        headers={"accept": "application/json", "content-type": "application/json"},
        data=json.dumps({"name": name, "value": value}),
    )
    response.raise_for_status()


def update_secret(name: str, value: str):
    root = app.config["LMNOP_GATEWAY"]
    response = requests.put(
        f"{root}/system/secrets",
        headers={"accept": "application/json", "content-type": "application/json"},
        data=json.dumps({"name": name, "value": value}),
    )
    response.raise_for_status()


def delete_secret(name: str):
    root = app.config["LMNOP_GATEWAY"]
    response = requests.delete(
        f"{root}/system/secrets",
        headers={"accept": "application/json", "content-type": "application/json"},
        data=json.dumps({"name": name}),
    )
    response.raise_for_status()
