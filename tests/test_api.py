import pytest

from tomllib import dumps
from tomllib import loads
from tomllib import parse
from tomllib.exceptions import InvalidNumberOrDateError
from tomllib.exceptions import MixedArrayTypesError
from tomllib.exceptions import UnexpectedCharError
from tomllib.toml_document import TOMLDocument


@pytest.mark.parametrize("example_name", ["example", "fruit", "hard"])
def test_parse_can_parse_valid_toml_files(example, example_name):
    assert isinstance(parse(example(example_name)), TOMLDocument)
    assert isinstance(loads(example(example_name)), TOMLDocument)


@pytest.mark.parametrize(
    "example_name,error",
    [
        ("section_with_trailing_characters", UnexpectedCharError),
        ("key_value_with_trailing_chars", UnexpectedCharError),
        ("array_with_invalid_chars", UnexpectedCharError),
        ("mixed_array_types", MixedArrayTypesError),
        ("invalid_number", InvalidNumberOrDateError),
    ],
)
def test_parse_raises_errors_for_invalid_toml_files(
    invalid_example, error, example_name
):
    with pytest.raises(error):
        parse(invalid_example(example_name))


@pytest.mark.parametrize("example_name", ["example", "fruit", "hard"])
def test_original_string_and_dumped_string_are_equal(example, example_name):
    content = example(example_name)
    parsed = parse(content)

    assert content == dumps(parsed)
