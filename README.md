[github_release]: https://img.shields.io/github/release/sdispater/tomlkit.svg?logo=github&logoColor=white
[pypi_version]: https://img.shields.io/pypi/v/tomlkit.svg?logo=python&logoColor=white
[python_versions]: https://img.shields.io/pypi/pyversions/tomlkit.svg?logo=python&logoColor=white
[github_license]: https://img.shields.io/github/license/sdispater/tomlkit.svg?logo=github&logoColor=white
[github_action]: https://github.com/sdispater/tomlkit/actions/workflows/tests.yml/badge.svg

<!--Codecov logo not offered by shields.io or simpleicons.org, this is Codecov's SVG image modified to be white-->

[codecov]: https://img.shields.io/codecov/c/github/sdispater/tomlkit/master.svg?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNTAiIGhlaWdodD0iNDgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CgogPGc+CiAgPHRpdGxlPmJhY2tncm91bmQ8L3RpdGxlPgogIDxyZWN0IGZpbGw9Im5vbmUiIGlkPSJjYW52YXNfYmFja2dyb3VuZCIgaGVpZ2h0PSI0MDIiIHdpZHRoPSI1ODIiIHk9Ii0xIiB4PSItMSIvPgogPC9nPgogPGc+CiAgPHRpdGxlPkxheWVyIDE8L3RpdGxlPgogIDxwYXRoIGlkPSJzdmdfMSIgZmlsbC1ydWxlPSJldmVub2RkIiBmaWxsPSIjZmZmZmZmIiBkPSJtMjUuMDE0LDBjLTEzLjc4NCwwLjAxIC0yNS4wMDQsMTEuMTQ5IC0yNS4wMTQsMjQuODMybDAsMC4wNjJsNC4yNTQsMi40ODJsMC4wNTgsLTAuMDM5YTEyLjIzOCwxMi4yMzggMCAwIDEgOS4wNzgsLTEuOTI4YTExLjg0NCwxMS44NDQgMCAwIDEgNS45OCwyLjk3NWwwLjczLDAuNjhsMC40MTMsLTAuOTA0YzAuNCwtMC44NzQgMC44NjIsLTEuNjk2IDEuMzc0LC0yLjQ0M2MwLjIwNiwtMC4zIDAuNDMzLC0wLjYwNCAwLjY5MiwtMC45MjlsMC40MjcsLTAuNTM1bC0wLjUyNiwtMC40NGExNy40NSwxNy40NSAwIDAgMCAtOC4xLC0zLjc4MWExNy44NTMsMTcuODUzIDAgMCAwIC04LjM3NSwwLjQ5YzIuMDIzLC04Ljg2OCA5LjgyLC0xNS4wNSAxOS4wMjcsLTE1LjA1N2M1LjE5NSwwIDEwLjA3OCwyLjAwNyAxMy43NTIsNS42NTJjMi42MTksMi41OTggNC40MjIsNS44MzUgNS4yMjQsOS4zNzJhMTcuOTA4LDE3LjkwOCAwIDAgMCAtNS4yMDgsLTAuNzlsLTAuMzE4LC0wLjAwMWExOC4wOTYsMTguMDk2IDAgMCAwIC0yLjA2NywwLjE1M2wtMC4wODcsMC4wMTJjLTAuMzAzLDAuMDQgLTAuNTcsMC4wODEgLTAuODEzLDAuMTI2Yy0wLjExOSwwLjAyIC0wLjIzNywwLjA0NSAtMC4zNTUsMC4wNjhjLTAuMjgsMC4wNTcgLTAuNTU0LDAuMTE5IC0wLjgxNiwwLjE4NWwtMC4yODgsMC4wNzNjLTAuMzM2LDAuMDkgLTAuNjc1LDAuMTkxIC0xLjAwNiwwLjNsLTAuMDYxLDAuMDJjLTAuNzQsMC4yNTEgLTEuNDc4LDAuNTU4IC0yLjE5LDAuOTE0bC0wLjA1NywwLjAyOWMtMC4zMTYsMC4xNTggLTAuNjM2LDAuMzMzIC0wLjk3OCwwLjUzNGwtMC4wNzUsMC4wNDVhMTYuOTcsMTYuOTcgMCAwIDAgLTQuNDE0LDMuNzhsLTAuMTU3LDAuMTkxYy0wLjMxNywwLjM5NCAtMC41NjcsMC43MjcgLTAuNzg3LDEuMDQ4Yy0wLjE4NCwwLjI3IC0wLjM2OSwwLjU2IC0wLjYsMC45NDJsLTAuMTI2LDAuMjE3Yy0wLjE4NCwwLjMxOCAtMC4zNDgsMC42MjIgLTAuNDg3LDAuOWwtMC4wMzMsMC4wNjFjLTAuMzU0LDAuNzExIC0wLjY2MSwxLjQ1NSAtMC45MTcsMi4yMTRsLTAuMDM2LDAuMTExYTE3LjEzLDE3LjEzIDAgMCAwIC0wLjg1NSw1LjY0NGwwLjAwMywwLjIzNGEyMy41NjUsMjMuNTY1IDAgMCAwIDAuMDQzLDAuODIyYzAuMDEsMC4xMyAwLjAyMywwLjI1OSAwLjAzNiwwLjM4OGMwLjAxNSwwLjE1OCAwLjAzNCwwLjMxNiAwLjA1MywwLjQ3MWwwLjAxMSwwLjA4OGwwLjAyOCwwLjIxNGMwLjAzNywwLjI2NCAwLjA4LDAuNTI1IDAuMTMsMC43ODdjMC41MDMsMi42MzcgMS43Niw1LjI3NCAzLjYzNSw3LjYyNWwwLjA4NSwwLjEwNmwwLjA4NywtMC4xMDRjMC43NDgsLTAuODg0IDIuNjAzLC0zLjY4NyAyLjc2LC01LjM2OWwwLjAwMywtMC4wMzFsLTAuMDE1LC0wLjAyOGExMS43MzYsMTEuNzM2IDAgMCAxIC0xLjMzMywtNS40MDdjMCwtNi4yODQgNC45NCwtMTEuNTAyIDExLjI0MywtMTEuODhsMC40MTQsLTAuMDE1YzIuNTYxLC0wLjA1OCA1LjA2NCwwLjY3MyA3LjIzLDIuMTM2bDAuMDU4LDAuMDM5bDQuMTk3LC0yLjQ0bDAuMDU1LC0wLjAzM2wwLC0wLjA2MmMwLjAwNiwtNi42MzIgLTIuNTkyLC0xMi44NjUgLTcuMzE0LC0xNy41NTFjLTQuNzE2LC00LjY3OSAtMTAuOTkxLC03LjI1NSAtMTcuNjcyLC03LjI1NSIvPgogPC9nPgo8L3N2Zz4=&label=Codecov

[![GitHub Release][github_release]](https://github.com/sdispater/tomlkit/releases/)
[![PyPI Version][pypi_version]](https://pypi.python.org/pypi/tomlkit/)
[![Python Versions][python_versions]](https://pypi.python.org/pypi/tomlkit/)
[![License][github_license]](https://github.com/sdispater/tomlkit/blob/master/LICENSE)
<br>
[![Codecov][codecov]](https://codecov.io/gh/sdispater/tomlkit)
[![Tests][github_action]](https://github.com/sdispater/tomlkit/actions/workflows/tests.yml)

# TOML Kit - Style-preserving TOML library for Python

TOML Kit is a **1.0.0-compliant** [TOML](https://toml.io/) library.

It includes a parser that preserves all comments, indentations, whitespace and internal element ordering,
and makes them accessible and editable via an intuitive API.

You can also create new TOML documents from scratch using the provided helpers.

Part of the implementation as been adapted, improved and fixed from [Molten](https://github.com/LeopoldArkham/Molten).

## Usage

### Parsing

TOML Kit comes with a fast and style-preserving parser to help you access
the content of TOML files and strings.

```python
>>> from tomlkit import dumps
>>> from tomlkit import parse  # you can also use loads

>>> content = """[table]
... foo = "bar"  # String
... """
>>> doc = parse(content)

# doc is a TOMLDocument instance that holds all the information
# about the TOML string.
# It behaves like a standard dictionary.

>>> assert doc["table"]["foo"] == "bar"

# The string generated from the document is exactly the same
# as the original string
>>> assert dumps(doc) == content
```

### Modifying

TOML Kit provides an intuitive API to modify TOML documents.

```python
>>> from tomlkit import dumps
>>> from tomlkit import parse
>>> from tomlkit import table

>>> doc = parse("""[table]
... foo = "bar"  # String
... """)

>>> doc["table"]["baz"] = 13

>>> dumps(doc)
"""[table]
foo = "bar"  # String
baz = 13
"""

# Add a new table
>>> tab = table()
>>> tab.add("array", [1, 2, 3])

>>> doc["table2"] = tab

>>> dumps(doc)
"""[table]
foo = "bar"  # String
baz = 13

[table2]
array = [1, 2, 3]
"""

# Remove the newly added table
>>> doc.remove("table2")
# del doc["table2] is also possible
```

### Writing

You can also write a new TOML document from scratch.

Let's say we want to create this following document:

```toml
# This is a TOML document.

title = "TOML Example"

[owner]
name = "Tom Preston-Werner"
organization = "GitHub"
bio = "GitHub Cofounder & CEO\nLikes tater tots and beer."
dob = 1979-05-27T07:32:00Z # First class dates? Why not?

[database]
server = "192.168.1.1"
ports = [ 8001, 8001, 8002 ]
connection_max = 5000
enabled = true
```

It can be created with the following code:

```python
>>> from tomlkit import comment
>>> from tomlkit import document
>>> from tomlkit import nl
>>> from tomlkit import table

>>> doc = document()
>>> doc.add(comment("This is a TOML document."))
>>> doc.add(nl())
>>> doc.add("title", "TOML Example")
# Using doc["title"] = "TOML Example" is also possible

>>> owner = table()
>>> owner.add("name", "Tom Preston-Werner")
>>> owner.add("organization", "GitHub")
>>> owner.add("bio", "GitHub Cofounder & CEO\nLikes tater tots and beer.")
>>> owner.add("dob", datetime(1979, 5, 27, 7, 32, tzinfo=utc))
>>> owner["dob"].comment("First class dates? Why not?")

# Adding the table to the document
>>> doc.add("owner", owner)

>>> database = table()
>>> database["server"] = "192.168.1.1"
>>> database["ports"] = [8001, 8001, 8002]
>>> database["connection_max"] = 5000
>>> database["enabled"] = True

>>> doc["database"] = database
```

## Installation

If you are using [Poetry](https://poetry.eustace.io),
add `tomlkit` to your `pyproject.toml` file by using:

```bash
poetry add tomlkit
```

If not, you can use `pip`:

```bash
pip install tomlkit
```

## Running tests

Please clone the repo with submodules with the following command
`git clone --recurse-submodules https://github.com/sdispater/tomlkit.git`.
We need the submodule - `toml-test` for running the tests.

You can run the tests with `poetry run pytest -q tests`
