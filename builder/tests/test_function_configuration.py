import os
import tempfile
import unittest
from contextlib import contextmanager

import yaml
from schema import SchemaError

import builder.commands.build
from builder import __version__
from builder.commands.build import process_function_configuration as parser


@contextmanager
def write_function_definition(definition):
    with tempfile.TemporaryDirectory() as td:
        os.mkdir(os.path.join(td, "source"))
        with open(os.path.join(td, "source", "function.yml"), "wt") as f:
            yaml.dump(definition, f)

        yield td


def read_function_definition(td):
    with open(os.path.join(td, "functions.yml"), "rt") as f:
        return yaml.safe_load(f)


class TestParser(unittest.TestCase):
    def test_parser_empty(self):
        definition = {}

        with write_function_definition(definition) as td:
            self.assertTrue(os.path.exists(os.path.join(td, "source", "function.yml")))
            with self.assertRaises(SchemaError):
                parser("test", td, os.path.join(td, "source"), "latest")

    def test_parser_valid(self):
        definition = {"template": "python3.9"}

        with write_function_definition(definition) as td:
            self.assertTrue(os.path.exists(os.path.join(td, "source", "function.yml")))
            parser("test", td, os.path.join(td, "source"), "latest")
            self.assertEqual({
                "version": "1.0",
                "provider": {
                    "name": "openfaas",
                    "gateway": builder.commands.build.LMNOP_GATEWAY,
                },
                "functions": {
                    "test": {
                        "lang": "python3.9",
                        "handler": os.path.join(td, "source"),
                        "image": f"{builder.commands.build.LMNOP_REGISTRY}/test:latest",
                        "readonly_root_filesystem": True,
                        "requests": {
                            "cpu": "50m",
                            "memory": "64Mi",
                        },
                        "limits": {
                            "cpu": "100m",
                            "memory": "128Mi",
                        },
                        "environment": {},
                        "secrets": [],
                        "build_args": {},
                    }
                }
            }, read_function_definition(td))

    def test_parser_valid_filled(self):
        definition = {
            "template": "python3.9",
            "requests": {
                "cpu": "100m",
                "memory": "32Mi",
            },
            "limits": {
                "cpu": "200m",
                "memory": "50Mi",
            },
            "environment": {
                "foo": "bar",
                "baz": "bat",
            },
            "secrets": [
                "foobar",
                "bazbat",
            ],
            "options": {
                "packages": "curl",
                "situation": "fubar",
            },
        }

        with write_function_definition(definition) as td:
            self.assertTrue(os.path.exists(os.path.join(td, "source", "function.yml")))
            parser("test", td, os.path.join(td, "source"), "latest")
            self.assertEqual({
                "version": "1.0",
                "provider": {
                    "name": "openfaas",
                    "gateway": builder.commands.build.LMNOP_GATEWAY,
                },
                "functions": {
                    "test": {
                        "lang": "python3.9",
                        "handler": os.path.join(td, "source"),
                        "image": f"{builder.commands.build.LMNOP_REGISTRY}/test:latest",
                        "readonly_root_filesystem": True,
                        "requests": {
                            "cpu": "100m",
                            "memory": "32Mi",
                        },
                        "limits": {
                            "cpu": "200m",
                            "memory": "50Mi",
                        },
                        "environment": {
                            "foo": "bar",
                            "baz": "bat",
                        },
                        "secrets": [
                            "foobar",
                            "bazbat",
                        ],
                        "build_args": {
                            "packages": "curl",
                            "situation": "fubar",
                        },
                    }
                }
            }, read_function_definition(td))


def test_version():
    assert __version__ == "0.0.0"  # noqa: S101
