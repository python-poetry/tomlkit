import json
import os

import pytest

from tomlkit import load
from tomlkit import parse
from tomlkit._compat import decode
from tomlkit._utils import parse_rfc3339
from tomlkit.exceptions import TOMLKitError


TESTS_ROOT = os.path.join(os.path.dirname(__file__), "toml-test", "tests")
FILES_LIST = os.path.join(TESTS_ROOT, "files-toml-1.1.0")


def to_bool(s):
    assert s in ["true", "false"]

    return s == "true"


stypes = {
    "string": str,
    "bool": to_bool,
    "integer": int,
    "float": float,
    "datetime": parse_rfc3339,
    "datetime-local": parse_rfc3339,
    "date-local": parse_rfc3339,
    "time-local": parse_rfc3339,
}


def untag(value):
    if isinstance(value, list):
        return [untag(i) for i in value]
    elif "type" in value and "value" in value and len(value) == 2:
        if value["type"] in stypes:
            val = decode(value["value"])

            return stypes[value["type"]](val)
        elif value["type"] == "array":
            return [untag(i) for i in value["value"]]
        else:
            raise Exception(f"Unsupported type {value['type']}")
    else:
        return {k: untag(v) for k, v in value.items()}


def _load_case_list():
    with open(FILES_LIST, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _build_cases():
    valid_cases = []
    valid_ids = []
    invalid_decode_cases = []
    invalid_decode_ids = []
    invalid_encode_cases = []
    invalid_encode_ids = []

    for relpath in _load_case_list():
        full_path = os.path.join(TESTS_ROOT, relpath)
        if not relpath.endswith(".toml"):
            continue

        case_id = relpath.rsplit(".", 1)[0]

        if relpath.startswith("invalid/encoding/"):
            invalid_encode_cases.append(full_path)
            invalid_encode_ids.append(case_id)
        elif relpath.startswith("valid/"):
            with open(full_path, encoding="utf-8", newline="") as f:
                toml_content = f.read()

            json_path = full_path.rsplit(".", 1)[0] + ".json"
            with open(json_path, encoding="utf-8") as f:
                json_content = f.read()

            valid_cases.append({"toml": toml_content, "json": json_content})
            valid_ids.append(case_id)
        elif relpath.startswith("invalid/"):
            with open(full_path, encoding="utf-8", newline="") as f:
                toml_content = f.read()

            invalid_decode_cases.append({"toml": toml_content})
            invalid_decode_ids.append(case_id)

    return (
        valid_cases,
        valid_ids,
        invalid_decode_cases,
        invalid_decode_ids,
        invalid_encode_cases,
        invalid_encode_ids,
    )


(
    VALID_CASES,
    VALID_IDS,
    INVALID_DECODE_CASES,
    INVALID_DECODE_IDS,
    INVALID_ENCODE_CASES,
    INVALID_ENCODE_IDS,
) = _build_cases()


@pytest.mark.parametrize("toml11_valid_case", VALID_CASES, ids=VALID_IDS)
def test_valid_decode(toml11_valid_case):
    json_val = untag(json.loads(toml11_valid_case["json"]))
    toml_val = parse(toml11_valid_case["toml"])

    assert toml_val == json_val
    assert toml_val.as_string() == toml11_valid_case["toml"]


@pytest.mark.parametrize(
    "toml11_invalid_decode_case", INVALID_DECODE_CASES, ids=INVALID_DECODE_IDS
)
def test_invalid_decode(toml11_invalid_decode_case):
    with pytest.raises(TOMLKitError):
        parse(toml11_invalid_decode_case["toml"])


@pytest.mark.parametrize(
    "toml11_invalid_encode_case", INVALID_ENCODE_CASES, ids=INVALID_ENCODE_IDS
)
def test_invalid_encode(toml11_invalid_encode_case):
    with open(toml11_invalid_encode_case, encoding="utf-8") as f:
        with pytest.raises((TOMLKitError, UnicodeDecodeError)):
            load(f)
