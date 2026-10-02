#!/usr/bin/env bash

set -uo pipefail

usage() {
  cat <<'EOF'
Usage: validate-json-schema.sh <schema.json> <document.json>

Validate a JSON document against a JSON Schema using Python jsonschema in a
Nix shell.

Arguments:
  schema.json    Path to the JSON Schema definition.
  document.json  Path to the JSON document to validate.

Options:
  -h, --help     Show this help message.

Exit status:
  0  Schema validation passed, or help was requested.
  1  Schema validation failed.
  2  Invalid command usage.
EOF
}

if [[ $# -eq 0 ]]; then
  usage
  exit 0
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 2 ]]; then
  echo "Schema validation failed: expected a schema and a document." >&2
  usage >&2
  exit 2
fi

schema_path="$1"
document_path="$2"

if [[ ! -f "$schema_path" ]]; then
  echo "Schema validation failed: schema file not found: $schema_path" >&2
  exit 1
fi

if [[ ! -f "$document_path" ]]; then
  echo "Schema validation failed: document file not found: $document_path" >&2
  exit 1
fi

export JSON_SCHEMA_PATH="$schema_path"
export JSON_DOCUMENT_PATH="$document_path"

nix-shell -p python313Packages.jsonschema --run 'python -c '\''
import json
import os
import sys

import jsonschema

try:
    with open(os.environ["JSON_SCHEMA_PATH"], encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    with open(os.environ["JSON_DOCUMENT_PATH"], encoding="utf-8") as document_file:
        document = json.load(document_file)
    jsonschema.Draft7Validator.check_schema(schema)
    jsonschema.validate(document, schema)
except jsonschema.ValidationError as error:
    print(f"Schema validation failed at {error.json_path}: {error.message}", file=sys.stderr)
    raise SystemExit(1)
except jsonschema.SchemaError as error:
    print(f"Schema validation failed: invalid schema: {error.message}", file=sys.stderr)
    raise SystemExit(1)
except (OSError, json.JSONDecodeError) as error:
    print(f"Schema validation failed: {error}", file=sys.stderr)
    raise SystemExit(1)

print("Schema validation passed")
'\'''
