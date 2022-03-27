# Change Log

## [Unreleased]

## [0.10.1] - 2022-03-27

### Fixed

- Preserve the newlines before super tables when rendering. ([#178](https://github.com/sdispater/tomlkit/issues/178))
- Fix the bug that comments are appended with comma when rendering a multiline array. ([#181](https://github.com/sdispater/tomlkit/issues/181))

## [0.10.0] - 2022-02-18

### Fixed

- Fix the only child detection when creating tables. ([#175](https://github.com/sdispater/tomlkit/issues/175))
- Include the `docs/` directory and `CHANGELOG.md` in sdist tarball. ([#176](https://github.com/sdispater/tomlkit/issues/176))

### Added

- Add keyword arguments to `string` API to allow selecting the representation type. ([#177](https://github.com/sdispater/tomlkit/pull/177))

## [0.9.2] - 2022-02-08

### Changed

- When a table's only child is a table or array of table, it is created as a super table. ([#175](https://github.com/sdispater/tomlkit/issues/175))

## [0.9.1] - 2022-02-07

### Fixed

- Fix a bug of separators not being kept when replacing the value. ([#170](https://github.com/sdispater/tomlkit/issues/170))
- Tuples should be dumped as TOML arrays. ([#171](https://github.com/sdispater/tomlkit/issues/171))

## [0.9.0] - 2022-02-01

### Added

- Add a new argument to `table` API to allow it to be a super table. ([#159](https://github.com/sdispater/tomlkit/pull/159))
- Support adding item to `Table` and `Container` with dotted key. ([#160](https://github.com/sdispater/tomlkit/pull/160))

### Fixed

- Fix a bug of `value()` API that parses string incompletely. ([#168](https://github.com/sdispater/tomlkit/pull/168))

## [0.8.0] - 2021-12-20

### Changed

- Drop support for Python<3.6. ([#151](https://github.com/sdispater/tomlkit/pull/151))
- Comply with TOML v1.0.0. ([#154](https://github.com/sdispater/tomlkit/pull/154))

### Fixed

- Support copy protocols for table items. ([#65](https://github.com/sdispater/tomlkit/issues/65))
- Escape characters in double quoted key string. ([#136](https://github.com/sdispater/tomlkit/issues/136))
- Fix the invalid dumping output of multiline array when it is empty. ([#139](https://github.com/sdispater/tomlkit/issues/139))
- Fix a bug that tomlkit accepts an invalid table with missing `=`. ([#141](https://github.com/sdispater/tomlkit/issues/141))
- Fix the invalid dumping output when the key is empty. ([#143](https://github.com/sdispater/tomlkit/issues/143))
- Fix incorrect string returned by dumps when moving/renaming table. ([#144](https://github.com/sdispater/tomlkit/issues/144))
- Fix inconsistent dumps when replacing existing item with nested table. ([#145](https://github.com/sdispater/tomlkit/issues/145))
- Fix invalid dumps output when appending to a multiline array. ([#146](https://github.com/sdispater/tomlkit/issues/146))
- Fix the `KeyAlreadyPresent` when the table is separated into multiple parts. ([#148](https://github.com/sdispater/tomlkit/issues/148))
- Preserve the line endings in `TOMLFile`. ([#149](https://github.com/sdispater/tomlkit/issues/149))

## [0.7.2] - 2021-05-20

### Fixed

- Fixed an error where container's data were lost when copying. ([#126](https://github.com/sdispater/tomlkit/pull/126))
- Fixed missing tests in the source distribution of the package. ([#127](https://github.com/sdispater/tomlkit/pull/127))

## [0.7.1] - 2021-05-19

### Fixed

- Fixed an error with indent for nested table elements when updating. ([#122](https://github.com/sdispater/tomlkit/pull/122))
- Fixed various issues with dict behavior compliance for containers. ([#122](https://github.com/sdispater/tomlkit/pull/122))
- Fixed an internal error when empty tables were present after existing ones. ([#122](https://github.com/sdispater/tomlkit/pull/122))
- Fixed table representation for dotted keys. ([#122](https://github.com/sdispater/tomlkit/pull/122))
- Fixed an error in top level keys handling when building documents programmatically. ([#122](https://github.com/sdispater/tomlkit/pull/122))
- Fixed compliance with mypy by adding a `py.typed` file. ([#109](https://github.com/sdispater/tomlkit/pull/109))

## [0.7.0] - 2020-07-31

### Added

- Added support for sorting keys when dumping raw dictionaries by passing `sort_keys=True` to `dumps()` ([#103](https://github.com/sdispater/tomlkit/pull/103)).

### Changed

- Keys are not longer sorted by default when dumping a raw dictionary but the original order will be preserved ([#103](https://github.com/sdispater/tomlkit/pull/103)).

### Fixed

- Fixed compliance with the 1.0.0rc1 TOML specification ([#102](https://github.com/sdispater/tomlkit/pull/102)).

## [0.6.0] - 2020-04-15

### Added

- Added support for heterogeneous arrays ([#92](https://github.com/sdispater/tomlkit/pull/92)).

## [0.5.11] - 2020-02-29

### Fixed

- Fix containers and our of order tables dictionary behavior ([#82](https://github.com/sdispater/tomlkit/pull/82)))

## [0.5.10] - 2020-02-28

### Fixed

- Fixed out of order tables not behaving properly ([#79](https://github.com/sdispater/tomlkit/pull/79))

## [0.5.9] - 2020-02-28

### Fixed

- Fixed the behavior for out of order tables ([#68](https://github.com/sdispater/tomlkit/pull/68)).
- Fixed parsing errors when single quotes are present in a table name ([#71](https://github.com/sdispater/tomlkit/pull/71)).
- Fixed parsing errors when parsing some table names ([#76](https://github.com/sdispater/tomlkit/pull/76)).

## [0.5.8] - 2019-10-11

### Added

- Added support for producing multiline arrays

## [0.5.7] - 2019-10-04

### Fixed

- Fixed handling of inline tables.

## [0.5.6] - 2019-10-04

### Fixed

- Fixed boolean comparison.
- Fixed appending inline tables to tables.

## [0.5.5] - 2019-07-01

### Fixed

- Fixed display of inline tables after element deletion.

## [0.5.4] - 2019-06-30

### Fixed

- Fixed the handling of inline tables.
- Fixed date, datetime and time handling on Python 3.8.
- Fixed behavior for sub table declaration with intermediate tables.
- Fixed behavior of `setdefault()` on containers (Thanks to [@AndyKluger](https://github.com/AndyKluger)).
- Fixed tables string representation.

## [0.5.3] - 2018-11-19

### Fixed

- Fixed copy of TOML documents.
- Fixed behavior on PyPy3.

## [0.5.2] - 2018-11-09

### Fixed

- Fixed table header missing when replacing a super table's sub table with a single item.
- Fixed comments being displayed in inline tables.
- Fixed string with non-scalar unicode code points not raising an error.

## [0.5.1] - 2018-11-08

### Fixed

- Fixed deletion and replacement of sub tables declared after other tables.

## [0.5.0] - 2018-11-06

### Changed

- Improved distinction between date(time)s and numbers.

### Fixed

- Fixed comma handling when parsing arrays. (Thanks to [@njalerikson](https://github.com/njalerikson))
- Fixed comma handling when parsing inline tables. (Thanks to [@njalerikson](https://github.com/njalerikson))
- Fixed a `KeyAlreadyPresent` error when declaring a sub table after other tables.

## [0.4.6] - 2018-10-16

### Fixed

- Fixed string parsing behavior.

## [0.4.5] - 2018-10-12

### Fixed

- Fixed trailing commas not raising an error for key/value.
- Fixed key comparison.
- Fixed an error when using pickle on TOML documents.

## [0.4.4] - 2018-09-01

### Fixed

- Fixed performances issues while parsing on Python 2.7.

## [0.4.3] - 2018-08-28

### Fixed

- Fixed handling of characters that need escaping when inserting/modifying a string element.
- Fixed missing newline after table header.
- Fixed dict-like behavior for tables and documents.

## [0.4.2] - 2018-08-06

### Fixed

- Fixed insertion of an element after deletion.

## [0.4.1] - 2018-08-06

### Fixed

- Fixed adding an element after another element without a new line.
- Fixed parsing of dotted keys inside tables.
- Fixed parsing of array of tables with same prefix.

## [0.4.0] - 2018-07-23

### Added

- `dumps()` now also accepts a raw dictionary.

### Changed

- `add()`/`append()`/`remove()` now return the current `Container`/`Table` to provide a fluent interface.
- Most items not behave like their native counterparts.

### Fixed

- Fixed potential new lines inside an inline table.

## [0.3.0] - 2018-07-20

### Changed

- Make new dicts automatically sorted when dumped.
- Improved new elements placement when building.
- Automatically convert lists of dicts to arrays of tables.
- No longer add a new line before standalone tables.
- Make arrays behave (mostly) like lists.

### Fixed

- Fixed string parsing when before last char is a backslash character.
- Fixed handling of array of tables after sub tables.
- Fixed table display order.
- Fixed handling of super tables with different sections.
- Fixed raw strings escaping.

[unreleased]: https://github.com/sdispater/tomlkit/compare/0.10.1...master
[0.10.1]: https://github.com/sdispater/tomlkit/releases/tag/0.10.1
[0.10.0]: https://github.com/sdispater/tomlkit/releases/tag/0.10.0
[0.9.2]: https://github.com/sdispater/tomlkit/releases/tag/0.9.2
[0.9.1]: https://github.com/sdispater/tomlkit/releases/tag/0.9.1
[0.9.0]: https://github.com/sdispater/tomlkit/releases/tag/0.9.0
[0.8.0]: https://github.com/sdispater/tomlkit/releases/tag/0.8.0
[0.7.2]: https://github.com/sdispater/tomlkit/releases/tag/0.7.2
[0.7.1]: https://github.com/sdispater/tomlkit/releases/tag/0.7.1
[0.7.0]: https://github.com/sdispater/tomlkit/releases/tag/0.7.0
[0.6.0]: https://github.com/sdispater/tomlkit/releases/tag/0.6.0
[0.5.11]: https://github.com/sdispater/tomlkit/releases/tag/0.5.11
[0.5.10]: https://github.com/sdispater/tomlkit/releases/tag/0.5.10
[0.5.9]: https://github.com/sdispater/tomlkit/releases/tag/0.5.9
[0.5.8]: https://github.com/sdispater/tomlkit/releases/tag/0.5.8
[0.5.7]: https://github.com/sdispater/tomlkit/releases/tag/0.5.7
[0.5.6]: https://github.com/sdispater/tomlkit/releases/tag/0.5.6
[0.5.5]: https://github.com/sdispater/tomlkit/releases/tag/0.5.5
[0.5.4]: https://github.com/sdispater/tomlkit/releases/tag/0.5.4
[0.5.3]: https://github.com/sdispater/tomlkit/releases/tag/0.5.3
[0.5.2]: https://github.com/sdispater/tomlkit/releases/tag/0.5.2
[0.5.1]: https://github.com/sdispater/tomlkit/releases/tag/0.5.1
[0.5.0]: https://github.com/sdispater/tomlkit/releases/tag/0.5.0
[0.4.6]: https://github.com/sdispater/tomlkit/releases/tag/0.4.6
[0.4.5]: https://github.com/sdispater/tomlkit/releases/tag/0.4.5
[0.4.4]: https://github.com/sdispater/tomlkit/releases/tag/0.4.4
[0.4.3]: https://github.com/sdispater/tomlkit/releases/tag/0.4.3
[0.4.2]: https://github.com/sdispater/tomlkit/releases/tag/0.4.2
[0.4.1]: https://github.com/sdispater/tomlkit/releases/tag/0.4.1
[0.4.0]: https://github.com/sdispater/tomlkit/releases/tag/0.4.0
[0.3.0]: https://github.com/sdispater/tomlkit/releases/tag/0.3.0
[0.2.0]: https://github.com/sdispater/tomlkit/releases/tag/0.2.0
