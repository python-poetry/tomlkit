# Change Log

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


[Unreleased]: https://github.com/sdispater/tomlkit/compare/0.6.0...master
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
