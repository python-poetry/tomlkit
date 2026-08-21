import json
import os

from typing import Any
from typing import Callable

import pytest

from tomlkit import load
from tomlkit import parse
from tomlkit._compat import decode
from tomlkit._utils import parse_rfc3339
from tomlkit.exceptions import TOMLKitError


TESTS_ROOT = os.path.join(os.path.dirname(__file__), "toml-test", "tests")
FILES_LIST = os.path.join(TESTS_ROOT, "files-toml-1.1.0")

# Cases added upstream (toml-test) that tomlkit does not yet handle correctly.
# Each reason cites the toml-test commit that introduced the case and its
# upstream issue, so these can be found again once the underlying bug is fixed.
KNOWN_FAILURES = {
    "valid/utf8-bom-01": (
        "leading UTF-8 BOM is not stripped before parsing "
        "(toml-test 542746b, BurntSushi/toml-test#199)"
    ),
    "valid/utf8-bom-02": (
        "leading UTF-8 BOM is not stripped before parsing "
        "(toml-test 542746b, BurntSushi/toml-test#199)"
    ),
    "invalid/float/arabic-zero-01": (
        "Arabic-Indic digit zero (٠) is accepted as a fraction digit "
        "(toml-test d736b6f, BurntSushi/toml-test#196)"
    ),
    "invalid/float/arabic-zero-03": (
        "Arabic-Indic digit zero (٠) is accepted in an exponent "
        "(toml-test d736b6f, BurntSushi/toml-test#196)"
    ),
    "invalid/float/arabic-zero-04": (
        "Arabic-Indic digit zero (٠) is accepted as a signed float value "
        "(toml-test d736b6f, BurntSushi/toml-test#196)"
    ),
    "invalid/integer/arabic-zero-01": (
        "Arabic-Indic digit zero (٠) is accepted as a trailing integer digit "
        "(toml-test d736b6f, BurntSushi/toml-test#196)"
    ),
    "invalid/integer/arabic-zero-02": (
        "Arabic-Indic digit zero (٠) is accepted after an underscore digit "
        "separator (toml-test d736b6f, BurntSushi/toml-test#196)"
    ),
}


def _param(case_id: str, value: Any) -> Any:
    reason = KNOWN_FAILURES.get(case_id)
    marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
    return pytest.param(value, id=case_id, marks=marks)


def to_bool(s: str) -> bool:
    assert s in ["true", "false"]

    return s == "true"


stypes: dict[str, Callable[[str], Any]] = {
    "string": str,
    "bool": to_bool,
    "integer": int,
    "float": float,
    "datetime": parse_rfc3339,
    "datetime-local": parse_rfc3339,
    "date-local": parse_rfc3339,
    "time-local": parse_rfc3339,
}


def untag(value: Any) -> Any:
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


def _load_case_list() -> list[str]:
    with open(FILES_LIST, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _build_cases() -> tuple[list[Any], list[Any], list[Any]]:
    valid_cases = []
    invalid_decode_cases = []
    invalid_encode_cases = []

    for relpath in _load_case_list():
        full_path = os.path.join(TESTS_ROOT, relpath)
        if not relpath.endswith(".toml"):
            continue

        case_id = relpath.rsplit(".", 1)[0]

        if relpath.startswith("invalid/encoding/"):
            invalid_encode_cases.append(_param(case_id, full_path))
        elif relpath.startswith("valid/"):
            with open(full_path, encoding="utf-8", newline="") as f:
                toml_content = f.read()

            json_path = full_path.rsplit(".", 1)[0] + ".json"
            with open(json_path, encoding="utf-8") as f:
                json_content = f.read()

            valid_cases.append(
                _param(case_id, {"toml": toml_content, "json": json_content})
            )
        elif relpath.startswith("invalid/"):
            with open(full_path, encoding="utf-8", newline="") as f:
                toml_content = f.read()

            invalid_decode_cases.append(_param(case_id, {"toml": toml_content}))

    return valid_cases, invalid_decode_cases, invalid_encode_cases


VALID_CASES, INVALID_DECODE_CASES, INVALID_ENCODE_CASES = _build_cases()


@pytest.mark.parametrize("toml11_valid_case", VALID_CASES)
def test_valid_decode(toml11_valid_case: dict[str, str]) -> None:
    json_val = untag(json.loads(toml11_valid_case["json"]))
    toml_val = parse(toml11_valid_case["toml"])

    assert toml_val == json_val
    assert toml_val.as_string() == toml11_valid_case["toml"]


@pytest.mark.parametrize("toml11_invalid_decode_case", INVALID_DECODE_CASES)
def test_invalid_decode(toml11_invalid_decode_case: dict[str, str]) -> None:
    with pytest.raises(TOMLKitError):
        parse(toml11_invalid_decode_case["toml"])


@pytest.mark.parametrize("toml11_invalid_encode_case", INVALID_ENCODE_CASES)
def test_invalid_encode(toml11_invalid_encode_case: str) -> None:
    with open(toml11_invalid_encode_case, encoding="utf-8") as f:
        with pytest.raises((TOMLKitError, UnicodeDecodeError)):
            load(f)
