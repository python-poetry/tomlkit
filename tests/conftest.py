import os

import pytest


@pytest.fixture
def example():
    def _example(name):
        with open(
            os.path.join(os.path.dirname(__file__), "examples", name + ".toml"),
            encoding="utf-8",
        ) as f:
            return f.read()

    return _example


@pytest.fixture
def json_example():
    def _example(name):
        with open(
            os.path.join(os.path.dirname(__file__), "examples", "json", name + ".json"),
            encoding="utf-8",
        ) as f:
            return f.read()

    return _example


@pytest.fixture
def invalid_example():
    def _example(name):
        with open(
            os.path.join(
                os.path.dirname(__file__), "examples", "invalid", name + ".toml"
            ),
            encoding="utf-8",
        ) as f:
            return f.read()

    return _example


TEST_DIR = os.path.join(os.path.dirname(__file__), "toml-test", "tests")
IGNORED_TESTS = {
    "invalid": [
        "array-mixed-types-strings-and-ints.toml",
        "array-mixed-types-arrays-and-ints.toml",
        "array-mixed-types-ints-and-floats.toml",
    ]
}


def get_tomltest_cases():
    dirs = sorted(
        f for f in os.listdir(TEST_DIR) if os.path.isdir(os.path.join(TEST_DIR, f))
    )
    assert dirs == ["invalid", "invalid-encoder", "valid"]
    rv = {}
    for d in dirs:
        rv[d] = {}
        ignored = IGNORED_TESTS.get(d, [])
        files = os.listdir(os.path.join(TEST_DIR, d))
        for f in files:
            if f in ignored:
                continue

            bn, ext = f.rsplit(".", 1)
            if bn not in rv[d]:
                rv[d][bn] = {}
            with open(os.path.join(TEST_DIR, d, f), encoding="utf-8") as inp:
                rv[d][bn][ext] = inp.read()
    return rv


def pytest_generate_tests(metafunc):
    test_list = get_tomltest_cases()
    if "valid_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "valid_case",
            test_list["valid"].values(),
            ids=list(test_list["valid"].keys()),
        )
    elif "invalid_decode_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "invalid_decode_case",
            test_list["invalid"].values(),
            ids=list(test_list["invalid"].keys()),
        )
    elif "invalid_encode_case" in metafunc.fixturenames:
        metafunc.parametrize(
            "invalid_encode_case",
            test_list["invalid-encoder"].values(),
            ids=list(test_list["invalid-encoder"].keys()),
        )
